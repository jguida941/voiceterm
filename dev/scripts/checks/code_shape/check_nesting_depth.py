#!/usr/bin/env python3
"""Guard against non-regressive growth of deeply nested functions in changed files."""

from __future__ import annotations

import argparse
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
scan_rust_functions = import_attr("code_shape_function_policy", "scan_rust_functions")
scan_python_functions = import_attr("code_shape_function_policy", "scan_python_functions")
strip_cfg_test_blocks = import_attr("rust_check_text_utils", "strip_cfg_test_blocks")

guard = GuardContext(REPO_ROOT)

TARGET_ROOTS = (
    *resolve_quality_scope_roots("rust_guard", repo_root=REPO_ROOT),
    *resolve_quality_scope_roots("python_guard", repo_root=REPO_ROOT),
)

PYTHON_NESTING_THRESHOLD = 4
RUST_NESTING_THRESHOLD = 5

PYTHON_DEF_RE = re.compile(r"^(\s*)def\s+")

def _is_python_test_path(path: Path) -> bool:
    return "tests" in path.parts or path.name.startswith("test_")

def _scan_python_function_depth(lines: list[str], start: int, def_indent: int) -> tuple[int, int]:
    """Return (max_nesting_depth, next_line_index) for one Python function."""
    base_indent = def_indent + 4
    max_depth = 0
    i = start
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if stripped == "" or stripped.startswith("#"):
            i += 1
            continue
        line_indent = len(raw) - len(raw.lstrip())
        if line_indent <= def_indent:
            break
        depth = (line_indent - base_indent) // 4
        if depth > max_depth:
            max_depth = depth
        i += 1
    return max_depth, i

def _max_python_nesting(text: str | None) -> int:
    """Count functions whose body exceeds the nesting threshold."""
    if text is None:
        return 0
    lines = text.splitlines()
    count = 0
    i = 0
    while i < len(lines):
        match = PYTHON_DEF_RE.match(lines[i])
        if not match:
            i += 1
            continue
        def_indent = len(match.group(1))
        i += 1
        max_depth, i = _scan_python_function_depth(lines, i, def_indent)
        if max_depth > PYTHON_NESTING_THRESHOLD:
            count += 1
    return count

def _rust_function_brace_depth(func_lines: list[str]) -> int:
    """Return the max brace nesting depth within a single Rust function body."""
    max_depth = 0
    base_found = False
    for line in func_lines:
        code = line.split("//", 1)[0]
        if not code.strip():
            continue
        if not base_found and "{" in code:
            base_found = True
            continue
        if not base_found:
            continue
        current = 0
        for ch in code:
            if ch == "{":
                current += 1
            elif ch == "}":
                current -= 1
            if current > max_depth:
                max_depth = current
    return max_depth

def _max_rust_nesting(text: str | None) -> int:
    """Count functions whose body exceeds the nesting threshold."""
    if text is None:
        return 0
    text = strip_cfg_test_blocks(text)
    functions = scan_rust_functions(text)
    lines = text.splitlines()
    count = 0
    for func in functions:
        start = func["start_line"] - 1
        end = func["end_line"]
        depth = _rust_function_brace_depth(lines[start:end])
        if depth > RUST_NESTING_THRESHOLD:
            count += 1
    return count

def _count_metrics(text: str | None, *, suffix: str = ".rs") -> dict[str, int]:
    if suffix == ".py":
        return {"deeply_nested_functions": _max_python_nesting(text)}
    if suffix == ".rs":
        return {"deeply_nested_functions": _max_rust_nesting(text)}
    return {"deeply_nested_functions": 0}

def _growth(base: dict[str, int], current: dict[str, int]) -> dict[str, int]:
    return {key: current[key] - base[key] for key in base}

def _has_positive_growth(growth: dict[str, int]) -> bool:
    return any(value > 0 for value in growth.values())

def _render_md(report: dict) -> str:
    lines = ["# check_nesting_depth", ""]
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
    lines.append("- aggregate_growth: " f"deeply_nested_functions {totals['deeply_nested_functions_growth']:+d}")
    lines.append(f"- thresholds: python >{PYTHON_NESTING_THRESHOLD} levels, " f"rust >{RUST_NESTING_THRESHOLD} levels")

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        lines.append(
            "- Guidance: reduce nesting by extracting inner blocks to helper "
            "functions, using early returns, or inverting conditions."
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
        return emit_runtime_error("check_nesting_depth", args.format, str(exc))

    mode = "commit-range" if args.since_ref else "working-tree"
    files_considered = 0
    files_skipped_non_source = 0
    files_skipped_tests = 0
    violations: list[dict] = []
    totals = {"deeply_nested_functions_growth": 0}

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

        totals["deeply_nested_functions_growth"] += growth["deeply_nested_functions"]

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
        "command": "check_nesting_depth",
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
