#!/usr/bin/env python3
"""Review probe: detect functions with too few blank lines (wall-of-code).

Functions longer than 20 lines with zero blank lines are hard to scan
because there is no visual separation between logical sections.  Adding
blank lines between setup, computation, and output blocks improves
readability more than adding comments.

This probe always exits 0.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from check_bootstrap import (
    REPO_ROOT,
        import_attr,
        is_under_target_roots,
        resolve_quality_scope_roots,
    )
    from probe_bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        emit_probe_report,
    )
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.check_bootstrap import (
    REPO_ROOT,
        import_attr,
        is_under_target_roots,
        resolve_quality_scope_roots,
    )
    from dev.scripts.checks.probe_bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        emit_probe_report,
    )

list_changed_paths_with_base_map = import_attr("git_change_paths", "list_changed_paths_with_base_map")
GuardContext = import_attr("rust_guard_common", "GuardContext")
is_review_probe_test_path = import_attr("probe_path_filters", "is_review_probe_test_path")
scan_python_functions = import_attr("code_shape_function_policy", "scan_python_functions")
scan_rust_functions = import_attr("code_shape_function_policy", "scan_rust_functions")
strip_cfg_test_blocks = import_attr("rust_check_text_utils", "strip_cfg_test_blocks")

guard = GuardContext(REPO_ROOT)

PYTHON_ROOTS = resolve_quality_scope_roots("python_probe", repo_root=REPO_ROOT)
RUST_ROOTS = resolve_quality_scope_roots("rust_probe", repo_root=REPO_ROOT)

REVIEW_LENS = "design_quality"

# Thresholds: minimum function length to trigger each severity level.
MIN_LINES_HIGH = 20
MIN_LINES_MEDIUM = 30
MIN_BLANK_MEDIUM = 2

AI_INSTRUCTIONS = {
    "high": (
        "This function is a wall of code with no blank lines. Add blank "
        "lines between logical sections \u2014 separate setup from computation "
        "from output. Aim for one blank line every 5-8 lines of code."
    ),
    "medium": (
        "This function has very few blank lines for its length. Add blank "
        "lines to visually separate logical sections and improve readability."
    ),
}


def _count_blank_lines(lines: list[str], start: int, end: int) -> int:
    """Count blank or whitespace-only lines between start and end (0-based, inclusive)."""
    count = 0
    for i in range(start, min(end + 1, len(lines))):
        if lines[i].strip() == "":
            count += 1
    return count


def _check_function(
    lines: list[str],
    func: dict,
    rel: str,
    lang_label: str,
) -> RiskHint | None:
    """Evaluate one function for blank-line frequency. Returns a hint or None."""
    line_count = func["line_count"]
    start_idx = func["start_line"] - 1
    end_idx = func["end_line"] - 1
    blank_count = _count_blank_lines(lines, start_idx, end_idx)

    if line_count > MIN_LINES_HIGH and blank_count == 0:
        severity = "high"
    elif line_count > MIN_LINES_MEDIUM and blank_count < MIN_BLANK_MEDIUM:
        severity = "medium"
    else:
        return None

    return RiskHint(
        file=rel,
        symbol=func["name"],
        risk_type="readability_smell",
        severity=severity,
        signals=[
            f"{line_count} lines with {blank_count} blank line(s) "
            f"({lang_label}) \u2014 add visual breaks between logical sections"
        ],
        ai_instruction=AI_INSTRUCTIONS[severity],
        review_lens=REVIEW_LENS,
    )


def _scan_python_file(text: str, path: Path) -> list[RiskHint]:
    hints: list[RiskHint] = []
    functions = scan_python_functions(text)
    lines = text.splitlines()
    rel = path.as_posix()

    for func in functions:
        hint = _check_function(lines, func, rel, "Python")
        if hint is not None:
            hints.append(hint)

    return hints


def _scan_rust_file(text: str, path: Path) -> list[RiskHint]:
    hints: list[RiskHint] = []
    stripped = strip_cfg_test_blocks(text)
    functions = scan_rust_functions(stripped)
    lines = stripped.splitlines()
    rel = path.as_posix()

    for func in functions:
        hint = _check_function(lines, func, rel, "Rust")
        if hint is not None:
            hints.append(hint)

    return hints


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_blank_line_frequency")

    try:
        if args.since_ref:
            guard.validate_ref(args.since_ref)
            guard.validate_ref(args.head_ref)
        changed_paths, _base_map = list_changed_paths_with_base_map(
            guard.run_git,
            args.since_ref,
            args.head_ref,
        )
    except RuntimeError:
        return emit_probe_report(report, output_format=args.format)

    report.mode = "commit-range" if args.since_ref else "working-tree"
    report.since_ref = args.since_ref
    report.head_ref = args.head_ref
    files_with_hints: set[str] = set()

    for path in changed_paths:
        if is_review_probe_test_path(path):
            continue

        is_python = path.suffix == ".py" and is_under_target_roots(path, repo_root=REPO_ROOT, target_roots=PYTHON_ROOTS)
        is_rust = path.suffix == ".rs" and is_under_target_roots(path, repo_root=REPO_ROOT, target_roots=RUST_ROOTS)
        if not is_python and not is_rust:
            continue

        report.files_scanned += 1
        text = guard.read_text_from_ref(path, args.head_ref) if args.since_ref else guard.read_text_from_worktree(path)
        if text is None:
            continue

        hints = _scan_python_file(text, path) if is_python else _scan_rust_file(text, path)
        if hints:
            files_with_hints.add(path.as_posix())
            report.risk_hints.extend(hints)

    report.files_with_hints = len(files_with_hints)
    return emit_probe_report(report, output_format=args.format)


if __name__ == "__main__":
    sys.exit(main())
