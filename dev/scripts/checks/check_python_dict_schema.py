#!/usr/bin/env python3
"""Guard against non-regressive growth of large untyped dict constructions in Python."""

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
        resolve_quality_scope_roots,
        utc_timestamp,
    )
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.check_bootstrap import (
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        is_under_target_roots,
        resolve_quality_scope_roots,
        utc_timestamp,
    )

list_changed_paths_with_base_map = import_attr(
    "git_change_paths", "list_changed_paths_with_base_map"
)
GuardContext = import_attr("rust_guard_common", "GuardContext")

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)

TARGET_ROOTS = (
    *resolve_quality_scope_roots("python_probe", repo_root=REPO_ROOT),
)

# Dict literals with this many string keys or more suggest a dataclass
STRING_KEY_THRESHOLD = 6


def _is_test_path(path: Path) -> bool:
    return "tests" in path.parts or path.name.startswith("test_")


def _node_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _subscript_args(node: ast.Subscript) -> tuple[ast.AST, ...]:
    slice_node = node.slice
    if isinstance(slice_node, ast.Tuple):
        return tuple(slice_node.elts)
    return (slice_node,)


def _is_str_type(node: ast.AST) -> bool:
    return _node_name(node) == "str"


def _is_any_type(node: ast.AST) -> bool:
    return _node_name(node) == "Any"


def _is_dict_any_type(node: ast.AST) -> bool:
    if not isinstance(node, ast.Subscript):
        return False
    if _node_name(node.value) not in {"dict", "Dict"}:
        return False
    args = _subscript_args(node)
    if len(args) != 2:
        return False
    return _is_str_type(args[0]) and _is_any_type(args[1])


def _contains_dict_any_type(node: ast.AST) -> bool:
    if _is_dict_any_type(node):
        return True
    return any(_contains_dict_any_type(child) for child in ast.iter_child_nodes(node))


def _is_type_alias_target(node: ast.AST) -> bool:
    return isinstance(node, ast.Name) and bool(node.id) and node.id[0].isupper()


def _count_large_dict_literals(text: str | None) -> int:
    if text is None:
        return 0
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 0
    count = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        string_keys = sum(
            1
            for key in node.keys
            if isinstance(key, ast.Constant) and isinstance(key.value, str)
        )
        if string_keys >= STRING_KEY_THRESHOLD:
            count += 1
    return count


def _count_weak_dict_any_aliases(text: str | None) -> int:
    """Count growth-prone type aliases such as `ArgumentDef = dict[str, Any]`."""
    if text is None:
        return 0
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 0
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if len(node.targets) != 1 or not _is_type_alias_target(node.targets[0]):
                continue
            if _contains_dict_any_type(node.value):
                count += 1
            continue
        if isinstance(node, ast.AnnAssign):
            if not _is_type_alias_target(node.target) or node.value is None:
                continue
            if _contains_dict_any_type(node.value):
                count += 1
    return count


def _count_metrics(text: str | None) -> dict[str, int]:
    return {
        "large_dict_literals": _count_large_dict_literals(text),
        "weak_dict_any_aliases": _count_weak_dict_any_aliases(text),
    }


def _growth(base: dict[str, int], current: dict[str, int]) -> dict[str, int]:
    return {key: current[key] - base[key] for key in base}


def _has_positive_growth(growth: dict[str, int]) -> bool:
    return any(value > 0 for value in growth.values())


def _render_md(report: dict) -> str:
    lines = ["# check_python_dict_schema", ""]
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
        f"large_dict_literals {totals['large_dict_literals_growth']:+d}, "
        f"weak_dict_any_aliases {totals['weak_dict_any_aliases_growth']:+d}"
    )
    lines.append(f"- threshold: >={STRING_KEY_THRESHOLD} string keys")

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        lines.append(
            "- Guidance: replace large dict literals with @dataclass, "
            "TypedDict, or NamedTuple for type safety and maintainability."
        )
        lines.append(
            "- Guidance: avoid weak uppercase type aliases using `dict[str, Any]`; "
            "prefer TypedDict/dataclass argument specs."
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
            "check_python_dict_schema", args.format, str(exc)
        )

    mode = "commit-range" if args.since_ref else "working-tree"
    files_considered = 0
    files_skipped_non_python = 0
    files_skipped_tests = 0
    violations: list[dict] = []
    totals = {
        "large_dict_literals_growth": 0,
        "weak_dict_any_aliases_growth": 0,
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

        totals["large_dict_literals_growth"] += growth["large_dict_literals"]
        totals["weak_dict_any_aliases_growth"] += growth["weak_dict_any_aliases"]

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
        "command": "check_python_dict_schema",
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
