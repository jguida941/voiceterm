#!/usr/bin/env python3
"""Guard against non-regressive growth of mutable global/default state in Python files."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

try:
    from check_bootstrap import (
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        is_under_target_roots,
        utc_timestamp,
    )
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.check_bootstrap import (
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        is_under_target_roots,
        utc_timestamp,
    )

list_changed_paths_with_base_map = import_attr(
    "git_change_paths", "list_changed_paths_with_base_map"
)
GuardContext = import_attr("rust_guard_common", "GuardContext")

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)

TARGET_ROOTS = (
    Path("dev/scripts"),
    Path("app/operator_console"),
)
MUTABLE_DEFAULT_FACTORIES = frozenset({"list", "dict", "set", "defaultdict", "deque"})


def _is_test_path(path: Path) -> bool:
    return "tests" in path.parts or path.name.startswith("test_")


def _count_global_statements(text: str | None) -> int:
    if text is None:
        return 0
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 0
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Global):
            count += len(node.names)
    return count


def _default_is_mutable(node: ast.AST) -> bool:
    if isinstance(node, (ast.List, ast.Dict, ast.Set)):
        return True
    if isinstance(node, ast.Call):
        target = node.func
        if isinstance(target, ast.Name):
            return target.id in MUTABLE_DEFAULT_FACTORIES
        if isinstance(target, ast.Attribute):
            return target.attr in MUTABLE_DEFAULT_FACTORIES
    return False


def _count_mutable_default_args(text: str | None) -> int:
    if text is None:
        return 0
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 0
    count = 0
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        defaults = list(node.args.defaults)
        defaults.extend(item for item in node.args.kw_defaults if item is not None)
        for default in defaults:
            if _default_is_mutable(default):
                count += 1
    return count


def _count_metrics(text: str | None) -> dict[str, int]:
    return {
        "global_statements": _count_global_statements(text),
        "mutable_default_args": _count_mutable_default_args(text),
    }


def _growth(base: dict[str, int], current: dict[str, int]) -> dict[str, int]:
    return {key: current[key] - base[key] for key in base}


def _has_positive_growth(growth: dict[str, int]) -> bool:
    return any(value > 0 for value in growth.values())


def _render_md(report: dict) -> str:
    lines = ["# check_python_global_mutable", ""]
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
        f"global_statements {totals['global_statements_growth']:+d}, "
        f"mutable_default_args {totals['mutable_default_args_growth']:+d}"
    )

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        lines.append(
            "- Guidance: avoid mutable global/default state. Use "
            "dependency injection, module-level factories with `reset_*()` "
            "test hooks, pass state explicitly, and default function args to "
            "`None` with in-function initialization."
        )
        for item in report["violations"]:
            growth_bits = [
                f"{key} {value:+d}"
                for key, value in item["growth"].items()
                if value > 0
            ]
            lines.append(f"- `{item['path']}`: {', '.join(growth_bits)}")
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
        return emit_runtime_error(
            "check_python_global_mutable", args.format, str(exc)
        )

    mode = "commit-range" if args.since_ref else "working-tree"
    files_considered = 0
    files_skipped_non_python = 0
    files_skipped_tests = 0
    violations: list[dict] = []
    totals = {
        "global_statements_growth": 0,
        "mutable_default_args_growth": 0,
    }

    for path in changed_paths:
        if path.suffix != ".py":
            files_skipped_non_python += 1
            continue
        if not is_under_target_roots(
            path, repo_root=REPO_ROOT, target_roots=TARGET_ROOTS
        ):
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

        totals["global_statements_growth"] += growth["global_statements"]
        totals["mutable_default_args_growth"] += growth["mutable_default_args"]

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
        "command": "check_python_global_mutable",
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
