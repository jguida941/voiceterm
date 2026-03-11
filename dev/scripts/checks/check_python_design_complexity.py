#!/usr/bin/env python3
"""Guard against non-regressive growth of branchy Python functions."""

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
        resolve_guard_config,
        resolve_quality_scope_roots,
        utc_timestamp,
    )
    from python_design_complexity_core import (
        build_function_violation,
        collect_excessive_functions,
        is_python_test_path,
        resolve_thresholds,
    )
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.check_bootstrap import (
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        is_under_target_roots,
        resolve_guard_config,
        resolve_quality_scope_roots,
        utc_timestamp,
    )
    from dev.scripts.checks.python_design_complexity_core import (
        build_function_violation,
        collect_excessive_functions,
        is_python_test_path,
        resolve_thresholds,
    )

list_changed_paths_with_base_map = import_attr(
    "git_change_paths", "list_changed_paths_with_base_map"
)
GuardContext = import_attr("rust_guard_common", "GuardContext")

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)

TARGET_ROOTS = resolve_quality_scope_roots("python_guard", repo_root=REPO_ROOT)
_collect_excessive_functions = collect_excessive_functions


def build_report(
    *,
    repo_root: Path = REPO_ROOT,
    candidate_paths: list[Path],
    base_text_by_path: dict[str, str | None],
    current_text_by_path: dict[str, str | None],
    mode: str,
    guard_config: dict | None = None,
) -> dict:
    thresholds = resolve_thresholds(guard_config)
    files_considered = 0
    files_skipped_non_python = 0
    files_skipped_tests = 0
    violations: list[dict] = []
    totals = {
        "high_branch_functions_growth": 0,
        "high_return_functions_growth": 0,
    }

    for candidate in candidate_paths:
        if candidate.suffix != ".py":
            files_skipped_non_python += 1
            continue
        if not is_under_target_roots(
            candidate,
            repo_root=repo_root,
            target_roots=TARGET_ROOTS,
        ):
            files_skipped_non_python += 1
            continue
        if is_python_test_path(candidate):
            files_skipped_tests += 1
            continue

        relative_path = (
            candidate.relative_to(repo_root).as_posix()
            if candidate.is_absolute()
            else candidate.as_posix()
        )
        files_considered += 1
        base_functions = collect_excessive_functions(
            base_text_by_path.get(relative_path),
            thresholds=thresholds,
        )
        current_functions = collect_excessive_functions(
            current_text_by_path.get(relative_path),
            thresholds=thresholds,
        )

        file_violations: list[dict] = []
        branch_function_growth = 0
        return_function_growth = 0
        for qualname, current_metrics in current_functions.items():
            item = build_function_violation(
                qualname=qualname,
                current=current_metrics,
                base=base_functions.get(qualname),
                thresholds=thresholds,
            )
            if item is None:
                continue
            if "too_many_branches" in item["reasons"]:
                branch_function_growth += 1
            if "too_many_returns" in item["reasons"]:
                return_function_growth += 1
            file_violations.append(item)

        if not file_violations:
            continue

        file_violations.sort(key=lambda item: (int(item["line"]), str(item["qualname"])))
        totals["high_branch_functions_growth"] += branch_function_growth
        totals["high_return_functions_growth"] += return_function_growth
        violations.append(
            {
                "path": relative_path,
                "growth": {
                    "high_branch_functions": branch_function_growth,
                    "high_return_functions": return_function_growth,
                },
                "functions": file_violations,
            }
        )

    return {
        "command": "check_python_design_complexity",
        "timestamp": utc_timestamp(),
        "mode": mode,
        "ok": len(violations) == 0,
        "files_changed": len(candidate_paths),
        "files_considered": files_considered,
        "files_skipped_non_python": files_skipped_non_python,
        "files_skipped_tests": files_skipped_tests,
        "thresholds": thresholds,
        "totals": totals,
        "violations": violations,
    }


def _render_md(report: dict) -> str:
    thresholds = report["thresholds"]
    lines = ["# check_python_design_complexity", ""]
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
    lines.append(
        "- aggregate_growth: "
        f"high_branch_functions {report['totals']['high_branch_functions_growth']:+d}, "
        f"high_return_functions {report['totals']['high_return_functions_growth']:+d}"
    )
    lines.append(
        f"- thresholds: branches >{thresholds['max_branches']}, "
        f"returns >{thresholds['max_returns']}"
    )

    if report["violations"]:
        lines.extend(
            (
                "",
                "## Violations",
                "- Guidance: decompose branch-heavy functions, use dispatch tables or "
                "typed helper objects, and prefer a smaller number of explicit exits.",
            )
        )
        for item in report["violations"]:
            lines.append(f"- `{item['path']}`:")
            for function in item["functions"]:
                reasons = ", ".join(function["reasons"])
                lines.append(
                    "  - "
                    f"`{function['qualname']}` line {function['line']} "
                    f"(branches={function['current']['branches']}, "
                    f"returns={function['current']['returns']}): {reasons}"
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
        return emit_runtime_error(
            "check_python_design_complexity",
            args.format,
            str(exc),
        )

    base_text_by_path: dict[str, str | None] = {}
    current_text_by_path: dict[str, str | None] = {}
    for path in changed_paths:
        if path.suffix != ".py":
            continue
        relative_path = path.as_posix()
        base_path = base_map.get(path, path)
        if args.since_ref:
            base_text = guard.read_text_from_ref(base_path, args.since_ref)
            current_text = guard.read_text_from_ref(path, args.head_ref)
        else:
            base_text = guard.read_text_from_ref(base_path, "HEAD")
            current_text = guard.read_text_from_worktree(path)
        base_text_by_path[relative_path] = base_text
        current_text_by_path[relative_path] = current_text

    report = build_report(
        repo_root=REPO_ROOT,
        candidate_paths=changed_paths,
        base_text_by_path=base_text_by_path,
        current_text_by_path=current_text_by_path,
        mode="commit-range" if args.since_ref else "working-tree",
        guard_config=resolve_guard_config(
            "python_design_complexity",
            repo_root=REPO_ROOT,
        ),
    )
    report["since_ref"] = args.since_ref
    report["head_ref"] = args.head_ref

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(_render_md(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
