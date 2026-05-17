#!/usr/bin/env python3
"""Guard against non-regressive growth of facade-heavy Python modules.

A facade-heavy module is one with multiple pure-delegation functions that
just forward all arguments to another function. A few are fine (adapter
pattern), but a file full of them suggests a dead indirection layer.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

try:
    from check_bootstrap import (
    REPO_ROOT,
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        is_under_target_roots,
        resolve_quality_scope_roots,
        utc_timestamp,
    )
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.check_bootstrap import (
    REPO_ROOT,
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        is_under_target_roots,
        resolve_quality_scope_roots,
        utc_timestamp,
    )

list_changed_paths_with_base_map = import_attr("git_change_paths", "list_changed_paths_with_base_map")
GuardContext = import_attr("rust_guard_common", "GuardContext")

guard = GuardContext(REPO_ROOT)

TARGET_ROOTS = (*resolve_quality_scope_roots("python_guard", repo_root=REPO_ROOT),)

# A file is facade-heavy when it has this many pure-delegation wrappers
FACADE_THRESHOLD = 3

def _is_test_path(path: Path) -> bool:
    return "tests" in path.parts or path.name.startswith("test_")

def _is_pure_delegation(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True when a function body is a single return-of-call statement.

    Ignores a leading docstring (Expr wrapping a Constant) so that
    ``def f(): "doc"; return g()`` still counts as delegation.
    """
    stmts = [s for s in node.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
    if len(stmts) != 1:
        return False
    stmt = stmts[0]
    if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Call):
        return True
    return bool(isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call))

def _count_facade_wrappers(text: str | None) -> int:
    if text is None:
        return 0
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 0
    wrappers = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and _is_pure_delegation(node):
            wrappers += 1
    return wrappers

def _is_facade_heavy(text: str | None) -> bool:
    return _count_facade_wrappers(text) > FACADE_THRESHOLD

def _count_metrics(text: str | None) -> dict[str, int]:
    return {
        "facade_heavy_modules": 1 if _is_facade_heavy(text) else 0,
        "facade_wrappers": _count_facade_wrappers(text),
    }

def _growth(base: dict[str, int], current: dict[str, int]) -> dict[str, int]:
    return {key: current[key] - base[key] for key in base}

def _has_positive_growth(growth: dict[str, int]) -> bool:
    return growth.get("facade_heavy_modules", 0) > 0

def _render_md(report: dict) -> str:
    lines = ["# check_facade_wrappers", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- files_changed: {report['files_changed']}")
    lines.append(f"- files_considered: {report['files_considered']}")
    lines.append(f"- files_skipped_non_python: {report['files_skipped_non_python']}")
    lines.append(f"- files_skipped_tests: {report['files_skipped_tests']}")
    lines.append(f"- violations: {len(report['violations'])}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("head_ref"):
        lines.append(f"- head_ref: {report['head_ref']}")

    totals = report["totals"]
    lines.append(
        "- aggregate_growth: "
        f"facade_heavy_modules {totals['facade_heavy_modules_growth']:+d}, "
        f"facade_wrappers {totals['facade_wrappers_growth']:+d}"
    )
    lines.append(f"- threshold: >{FACADE_THRESHOLD} pure-delegation wrappers per file")

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        lines.append(
            "- Guidance: remove thin delegation wrappers. Import the "
            "target function directly instead of wrapping it."
        )
        for item in report["violations"]:
            lines.append(
                f"- `{item['path']}`: "
                f"facade_wrappers {item['current']['facade_wrappers']} "
                f"(+{item['growth']['facade_wrappers']})"
            )
    return "\n".join(lines)

def _build_parser() -> argparse.ArgumentParser:
    return build_since_ref_format_parser(__doc__ or "")

def main() -> int:
    args = _build_parser().parse_args()

    try:
        if args.since_ref:
            guard.validate_ref(args.since_ref)
            guard.validate_ref(args.head_ref)
        changed_paths, base_map = list_changed_paths_with_base_map(
            guard.run_git,
            args.since_ref,
            args.head_ref,
        )
    except RuntimeError as exc:
        return emit_runtime_error("check_facade_wrappers", args.format, str(exc))

    mode = "commit-range" if args.since_ref else "working-tree"
    files_considered = 0
    files_skipped_non_python = 0
    files_skipped_tests = 0
    violations: list[dict] = []
    totals = {
        "facade_heavy_modules_growth": 0,
        "facade_wrappers_growth": 0,
    }

    for path in changed_paths:
        if path.suffix != ".py":
            files_skipped_non_python += 1
            continue
        if not is_under_target_roots(path, repo_root=REPO_ROOT, target_roots=TARGET_ROOTS):
            files_skipped_non_python += 1
            continue
        if _is_test_path(path):
            files_skipped_tests += 1
            continue

        files_considered += 1

        base_path = base_map.get(path, path)
        if args.since_ref:
            base_text = guard.read_text_from_ref(base_path, args.since_ref)
            current_text = guard.read_text_from_ref(path, args.head_ref)
        else:
            base_text = guard.read_text_from_ref(base_path, "HEAD")
            current_text = guard.read_text_from_worktree(path)

        base = _count_metrics(base_text)
        current = _count_metrics(current_text)
        growth = _growth(base, current)

        totals["facade_heavy_modules_growth"] += growth["facade_heavy_modules"]
        totals["facade_wrappers_growth"] += growth["facade_wrappers"]

        if _has_positive_growth(growth):
            violations.append(
                {
                    "path": path.as_posix(),
                    "base": base,
                    "current": current,
                    "growth": growth,
                }
            )

    report = {
        "command": "check_facade_wrappers",
        "timestamp": utc_timestamp(),
        "mode": mode,
        "since_ref": args.since_ref,
        "head_ref": args.head_ref,
        "ok": len(violations) == 0,
        "files_changed": len(changed_paths),
        "files_considered": files_considered,
        "files_skipped_non_python": files_skipped_non_python,
        "files_skipped_tests": files_skipped_tests,
        "totals": totals,
        "violations": violations,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))

    return 0 if report["ok"] else 1

if __name__ == "__main__":
    sys.exit(main())
