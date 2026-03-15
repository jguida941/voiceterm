#!/usr/bin/env python3
"""Guard against non-regressive growth of god classes (excessive methods or instance vars)."""

from __future__ import annotations

import argparse
import ast
import json
import re
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
_is_rust_test_path = import_attr("rust_guard_common", "is_test_path")
strip_cfg_test_blocks = import_attr("rust_check_text_utils", "strip_cfg_test_blocks")

guard = GuardContext(REPO_ROOT)

TARGET_ROOTS = (
    *resolve_quality_scope_roots("rust_guard", repo_root=REPO_ROOT),
    *resolve_quality_scope_roots("python_guard", repo_root=REPO_ROOT),
)

PYTHON_METHOD_THRESHOLD = 20
PYTHON_IVAR_THRESHOLD = 10
RUST_IMPL_METHOD_THRESHOLD = 20

RUST_IMPL_RE = re.compile(r"\bimpl(?:\s*<[^>]*>)?\s+([A-Za-z_][A-Za-z0-9_]*)")
RUST_FN_IN_IMPL_RE = re.compile(r"^\s*(?:pub(?:\s*\([^)]*\))?\s+)?fn\s+")

def _is_python_test_path(path: Path) -> bool:
    return "tests" in path.parts or path.name.startswith("test_")

def _count_python_god_classes(text: str | None) -> int:
    if text is None:
        return 0
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 0
    count = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        methods = sum(1 for child in node.body if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef))
        ivars: set[str] = set()
        for child in node.body:
            if not isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            if child.name != "__init__":
                continue
            for stmt in ast.walk(child):
                if (
                    isinstance(stmt, ast.Assign)
                    and len(stmt.targets) == 1
                    and isinstance(stmt.targets[0], ast.Attribute)
                    and isinstance(stmt.targets[0].value, ast.Name)
                    and stmt.targets[0].value.id == "self"
                ):
                    ivars.add(stmt.targets[0].attr)
        if methods > PYTHON_METHOD_THRESHOLD or len(ivars) > PYTHON_IVAR_THRESHOLD:
            count += 1
    return count

def _count_rust_god_impls(text: str | None) -> int:
    if text is None:
        return 0
    text = strip_cfg_test_blocks(text)
    impl_methods: dict[str, int] = {}
    lines = text.splitlines()
    current_impl: str | None = None
    brace_depth = 0

    for line in lines:
        stripped = line.split("//", 1)[0]
        if current_impl is None:
            match = RUST_IMPL_RE.search(stripped)
            if match and "{" in stripped:
                current_impl = match.group(1)
                brace_depth = stripped.count("{") - stripped.count("}")
                if RUST_FN_IN_IMPL_RE.match(stripped):
                    impl_methods[current_impl] = impl_methods.get(current_impl, 0) + 1
                if brace_depth <= 0:
                    current_impl = None
                continue
        else:
            if RUST_FN_IN_IMPL_RE.match(stripped):
                impl_methods[current_impl] = impl_methods.get(current_impl, 0) + 1
            brace_depth += stripped.count("{") - stripped.count("}")
            if brace_depth <= 0:
                current_impl = None

    return sum(1 for count in impl_methods.values() if count > RUST_IMPL_METHOD_THRESHOLD)

def _count_metrics(text: str | None, *, suffix: str = ".rs") -> dict[str, int]:
    if suffix == ".py":
        return {"god_classes": _count_python_god_classes(text)}
    if suffix == ".rs":
        return {"god_classes": _count_rust_god_impls(text)}
    return {"god_classes": 0}

def _growth(base: dict[str, int], current: dict[str, int]) -> dict[str, int]:
    return {key: current[key] - base[key] for key in base}

def _has_positive_growth(growth: dict[str, int]) -> bool:
    return any(value > 0 for value in growth.values())

def _render_md(report: dict) -> str:
    lines = ["# check_god_class", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- files_changed: {report['files_changed']}")
    lines.append(f"- files_considered: {report['files_considered']}")
    lines.append(f"- files_skipped_non_source: {report['files_skipped_non_source']}")
    lines.append(f"- files_skipped_tests: {report['files_skipped_tests']}")
    lines.append(f"- violations: {len(report['violations'])}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("head_ref"):
        lines.append(f"- head_ref: {report['head_ref']}")

    totals = report["totals"]
    lines.append("- aggregate_growth: " f"god_classes {totals['god_classes_growth']:+d}")
    lines.append(
        f"- thresholds: python methods >{PYTHON_METHOD_THRESHOLD} or "
        f"ivars >{PYTHON_IVAR_THRESHOLD}, rust impl methods >{RUST_IMPL_METHOD_THRESHOLD}"
    )

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        lines.append(
            "- Guidance: decompose large classes into focused collaborators. "
            "Extract method groups into helper classes, services, or mixins."
        )
        for item in report["violations"]:
            growth_bits = [f"{key} {value:+d}" for key, value in item["growth"].items() if value > 0]
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
        return emit_runtime_error("check_god_class", args.format, str(exc))

    mode = "commit-range" if args.since_ref else "working-tree"
    files_considered = 0
    files_skipped_non_source = 0
    files_skipped_tests = 0
    violations: list[dict] = []
    totals = {"god_classes_growth": 0}

    for path in changed_paths:
        if path.suffix not in (".rs", ".py"):
            files_skipped_non_source += 1
            continue
        if not is_under_target_roots(path, repo_root=REPO_ROOT, target_roots=TARGET_ROOTS):
            files_skipped_non_source += 1
            continue
        if path.suffix == ".rs" and _is_rust_test_path(path):
            files_skipped_tests += 1
            continue
        if path.suffix == ".py" and _is_python_test_path(path):
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

        base = _count_metrics(base_text, suffix=path.suffix)
        current = _count_metrics(current_text, suffix=path.suffix)
        growth = _growth(base, current)

        totals["god_classes_growth"] += growth["god_classes"]

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
        "command": "check_god_class",
        "timestamp": utc_timestamp(),
        "mode": mode,
        "since_ref": args.since_ref,
        "head_ref": args.head_ref,
        "ok": len(violations) == 0,
        "files_changed": len(changed_paths),
        "files_considered": files_considered,
        "files_skipped_non_source": files_skipped_non_source,
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
