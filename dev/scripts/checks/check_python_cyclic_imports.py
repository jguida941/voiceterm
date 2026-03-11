#!/usr/bin/env python3
"""Guard against non-regressive growth of Python import cycles."""

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
        resolve_guard_config,
        resolve_quality_scope_roots,
        utc_timestamp,
    )
    from python_cyclic_imports_core import (
        CycleGraphInputs,
        CycleReportInputs,
        build_cycle_report,
        coerce_ignored_paths,
        list_python_paths_from_ref,
        list_python_paths_from_worktree,
    )
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.check_bootstrap import (
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        resolve_guard_config,
        resolve_quality_scope_roots,
        utc_timestamp,
    )
    from dev.scripts.checks.python_cyclic_imports_core import (
        CycleGraphInputs,
        CycleReportInputs,
        build_cycle_report,
        coerce_ignored_paths,
        list_python_paths_from_ref,
        list_python_paths_from_worktree,
    )

list_changed_paths_with_base_map = import_attr(
    "git_change_paths", "list_changed_paths_with_base_map"
)
GuardContext = import_attr("rust_guard_common", "GuardContext")

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)

TARGET_ROOTS = tuple(resolve_quality_scope_roots("python_guard", repo_root=REPO_ROOT))
build_report = build_cycle_report


def _resolve_guard_config(script_id: str, repo_root: Path) -> dict:
    return resolve_guard_config(script_id, repo_root=repo_root)


def _render_md(report: dict) -> str:
    lines = ["# check_python_cyclic_imports", ""]
    lines.append(f"- mode: {report['mode']}")
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- files_changed: {report['files_changed']}")
    lines.append(f"- files_considered: {report['files_considered']}")
    lines.append(f"- files_skipped_non_python: {report['files_skipped_non_python']}")
    lines.append(f"- files_skipped_tests: {report['files_skipped_tests']}")
    lines.append(f"- graph_python_files_base: {report['graph_python_files_base']}")
    lines.append(f"- graph_python_files_current: {report['graph_python_files_current']}")
    lines.append(f"- cycles_scanned: {report['cycles_scanned']}")
    lines.append(f"- violations: {len(report['violations'])}")
    if report.get("since_ref"):
        lines.append(f"- since_ref: {report['since_ref']}")
    if report.get("head_ref"):
        lines.append(f"- head_ref: {report['head_ref']}")
    lines.append(
        f"- aggregate_growth: cyclic_imports {report['totals']['cyclic_imports_growth']:+d}"
    )
    if report["ignored_paths"]:
        lines.append("- ignored_paths: " + ", ".join(report["ignored_paths"]))
    lines.append(f"- ignored_cycle_count: {report['ignored_cycle_count']}")

    if report["cycles"]:
        lines.extend(
            (
                "",
                "## Cycles",
                "- Guidance: break Python import cycles with interface modules, late-bound helpers, or dependency inversion instead of top-level cross-imports.",
            )
        )
        for cycle in report["cycles"]:
            lines.append("- " + " -> ".join(cycle["members"]))
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
        ignored_paths = coerce_ignored_paths(
            repo_root=REPO_ROOT,
            resolve_guard_config_fn=_resolve_guard_config,
        )
        if args.since_ref:
            base_paths = list_python_paths_from_ref(
                ref=args.since_ref,
                run_git_fn=guard.run_git,
                target_roots=TARGET_ROOTS,
                ignored_paths=ignored_paths,
            )
            current_paths = list_python_paths_from_ref(
                ref=args.head_ref,
                run_git_fn=guard.run_git,
                target_roots=TARGET_ROOTS,
                ignored_paths=ignored_paths,
            )
        else:
            base_paths = list_python_paths_from_ref(
                ref="HEAD",
                run_git_fn=guard.run_git,
                target_roots=TARGET_ROOTS,
                ignored_paths=ignored_paths,
            )
            current_paths = list_python_paths_from_worktree(
                repo_root=REPO_ROOT,
                target_roots=TARGET_ROOTS,
                ignored_paths=ignored_paths,
            )
    except RuntimeError as exc:
        return emit_runtime_error(
            "check_python_cyclic_imports",
            args.format,
            str(exc),
        )

    base_text_by_path = {
        path.as_posix(): guard.read_text_from_ref(path, args.since_ref or "HEAD")
        for path in base_paths
    }
    current_text_by_path = {
        path.as_posix(): (
            guard.read_text_from_ref(path, args.head_ref)
            if args.since_ref
            else guard.read_text_from_worktree(path)
        )
        for path in current_paths
    }
    report = build_cycle_report(
        repo_root=REPO_ROOT,
        inputs=CycleReportInputs(
            candidate_paths=changed_paths,
            graph_inputs=CycleGraphInputs(
                base_paths=base_paths,
                current_paths=current_paths,
                base_map=base_map,
            ),
            base_text_by_path=base_text_by_path,
            current_text_by_path=current_text_by_path,
            mode="commit-range" if args.since_ref else "working-tree",
            target_roots=TARGET_ROOTS,
        ),
        resolve_guard_config_fn=_resolve_guard_config,
    )
    report["timestamp"] = utc_timestamp()
    report["since_ref"] = args.since_ref
    report["head_ref"] = args.head_ref

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
