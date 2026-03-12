#!/usr/bin/env python3
"""Guard against non-regressive growth of Python default-state evaluation traps."""

from __future__ import annotations

import argparse
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

try:
    from python_default_trap_core import (
        METRIC_LABELS,
    )
    from python_default_trap_core import (
        count_dataclass_default_traps as _count_dataclass_default_traps_impl,
    )
    from python_default_trap_core import (
        count_function_call_default_args as _count_function_call_default_args_impl,
    )
    from python_default_trap_core import (
        count_global_statements as _count_global_statements_impl,
    )
    from python_default_trap_core import (
        count_metrics as _count_metrics,
    )
    from python_default_trap_core import (
        count_mutable_default_args as _count_mutable_default_args_impl,
    )
    from python_default_trap_core import (
        format_growth as _format_growth,
    )
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.python_default_trap_core import (
        METRIC_LABELS,
    )
    from dev.scripts.checks.python_default_trap_core import (
        count_dataclass_default_traps as _count_dataclass_default_traps_impl,
    )
    from dev.scripts.checks.python_default_trap_core import (
        count_function_call_default_args as _count_function_call_default_args_impl,
    )
    from dev.scripts.checks.python_default_trap_core import (
        count_global_statements as _count_global_statements_impl,
    )
    from dev.scripts.checks.python_default_trap_core import (
        count_metrics as _count_metrics,
    )
    from dev.scripts.checks.python_default_trap_core import (
        count_mutable_default_args as _count_mutable_default_args_impl,
    )
    from dev.scripts.checks.python_default_trap_core import (
        format_growth as _format_growth,
    )

_count_dataclass_default_traps = _count_dataclass_default_traps_impl
_count_function_call_default_args = _count_function_call_default_args_impl
_count_global_statements = _count_global_statements_impl
_count_mutable_default_args = _count_mutable_default_args_impl

list_changed_paths_with_base_map = import_attr("git_change_paths", "list_changed_paths_with_base_map")
GuardContext = import_attr("rust_guard_common", "GuardContext")

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)

TARGET_ROOTS = (*resolve_quality_scope_roots("python_guard", repo_root=REPO_ROOT),)


def _is_test_path(path: Path) -> bool:
    return "tests" in path.parts or path.name.startswith("test_")


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

    aggregate_growth = {key: report["totals"][f"{key}_growth"] for key in METRIC_LABELS}
    lines.append(f"- aggregate_growth: {_format_growth(aggregate_growth)}")

    if report["violations"]:
        lines.append("")
        lines.append("## Violations")
        lines.append(
            "- Guidance: avoid mutable global/default state and eager default "
            "evaluation. Use dependency injection, module-level factories with "
            "`reset_*()` test hooks, `None` sentinels plus in-function "
            "initialization, and `field(default_factory=...)` for dataclasses."
        )
        for item in report["violations"]:
            growth_bits = [f"{METRIC_LABELS[key]} {value:+d}" for key, value in item["growth"].items() if value > 0]
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
        return emit_runtime_error("check_python_global_mutable", args.format, str(exc))

    mode = "commit-range" if args.since_ref else "working-tree"
    files_considered = 0
    files_skipped_non_python = 0
    files_skipped_tests = 0
    violations: list[dict] = []
    totals = {f"{key}_growth": 0 for key in METRIC_LABELS}

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

        for key, value in growth.items():
            totals[f"{key}_growth"] += value

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
