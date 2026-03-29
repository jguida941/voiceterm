#!/usr/bin/env python3
"""Review probe: detect Rust match expressions with overly complex arms.

Match arms with many lines of procedural code indicate that logic should be
extracted into named handler functions, keeping the match as a thin dispatch
table.

This probe always exits 0.
"""

from __future__ import annotations

import re
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
scan_rust_functions = import_attr("code_shape_function_policy", "scan_rust_functions")
strip_cfg_test_blocks = import_attr("rust_check_text_utils", "strip_cfg_test_blocks")
mask_rust_comments_and_strings = import_attr("rust_check_text_utils", "mask_rust_comments_and_strings")

guard = GuardContext(REPO_ROOT)

TARGET_ROOTS = resolve_quality_scope_roots("rust_probe", repo_root=REPO_ROOT)

REVIEW_LENS = "design_quality"

# Thresholds for individual arm body length.
ARM_BODY_MEDIUM = 5
ARM_BODY_HIGH = 10

# Dispatch-table smell: many arms each with non-trivial bodies.
DISPATCH_ARM_COUNT = 10
DISPATCH_ARM_MIN_LINES = 3

# Regex to detect `match <expr> {` on a single line (after comment/string masking).
MATCH_START_RE = re.compile(r"\bmatch\b\s+")

# Regex to detect arm patterns: line ending with `=>` or `=> {`.
ARM_PATTERN_RE = re.compile(r"=>\s*\{?\s*$")

AI_INSTRUCTIONS = {
    "medium": (
        "This match expression has arms with 5+ lines of logic. Extract "
        "each complex arm into a named handler function so the match "
        "becomes a clean dispatch table."
    ),
    "high": (
        "This match expression has arms with 10+ lines of procedural code. "
        "Extract arm logic into handler functions: "
        "`Event::Click(btn) => handle_click(btn),` — keeping the match "
        "as a thin dispatch layer."
    ),
}


def _find_match_expressions(masked_lines: list[str]) -> list[tuple[int, int]]:
    """Return (start_line_idx, open_brace_idx) for each match expression."""
    matches: list[tuple[int, int]] = []
    for idx, line in enumerate(masked_lines):
        stripped = line.strip()
        if not MATCH_START_RE.search(stripped):
            continue
        # Find the opening brace on this line or subsequent lines.
        brace_pos = line.find("{")
        if brace_pos >= 0:
            matches.append((idx, idx))
        else:
            # Opening brace might be on the next line.
            for scan_idx in range(idx + 1, min(idx + 4, len(masked_lines))):
                if "{" in masked_lines[scan_idx]:
                    matches.append((idx, scan_idx))
                    break
    return matches


def _find_closing_brace(masked_lines: list[str], brace_line: int) -> int:
    """Return line index of the closing brace matching the first '{' on brace_line."""
    depth = 0
    for idx in range(brace_line, len(masked_lines)):
        line = masked_lines[idx]
        depth += line.count("{") - line.count("}")
        if depth <= 0:
            return idx
    return len(masked_lines) - 1


def _parse_arms(
    masked_lines: list[str],
    body_start: int,
    body_end: int,
) -> list[int]:
    """Return list of body-line counts for each arm in a match block.

    Arms are delimited by lines containing '=>' at the match brace depth.
    """
    arm_body_lengths: list[int] = []
    current_arm_start: int | None = None
    depth = 0

    for idx in range(body_start, body_end + 1):
        line = masked_lines[idx]

        if idx == body_start:
            # Count braces after the opening '{' on the match line.
            depth = line.count("{") - line.count("}")
            continue

        open_count = line.count("{")
        close_count = line.count("}")
        new_depth = depth + open_count - close_count

        # An arm pattern at depth 1 (inside the match block, not nested).
        stripped = line.strip()
        is_arm_start = depth == 1 and "=>" in stripped

        if is_arm_start:
            if current_arm_start is not None:
                body_lines = idx - current_arm_start - 1
                if body_lines > 0:
                    arm_body_lengths.append(body_lines)
            current_arm_start = idx

        depth = new_depth

    # Last arm ends at the closing brace.
    if current_arm_start is not None:
        body_lines = body_end - current_arm_start - 1
        if body_lines > 0:
            arm_body_lengths.append(body_lines)

    return arm_body_lengths


def _scan_rust_file(text: str, path: Path) -> list[RiskHint]:
    """Detect functions with complex match arms in one Rust file."""
    hints: list[RiskHint] = []
    stripped = strip_cfg_test_blocks(text)
    functions = scan_rust_functions(stripped)
    masked = mask_rust_comments_and_strings(stripped)
    masked_lines = masked.splitlines()
    original_lines = stripped.splitlines()
    rel = path.as_posix()

    for func in functions:
        func_name = func["name"]
        func_start = func["start_line"] - 1
        func_end = func["end_line"]

        # Find match expressions within this function's line range.
        func_masked = masked_lines[func_start:func_end]
        match_starts = _find_match_expressions(func_masked)

        worst_severity: str | None = None
        signals: list[str] = []

        for match_keyword_offset, brace_offset in match_starts:
            abs_brace = func_start + brace_offset
            abs_close = _find_closing_brace(masked_lines, abs_brace)

            arm_lengths = _parse_arms(masked_lines, abs_brace, abs_close)
            if not arm_lengths:
                continue

            # Signal 1 & 2: individual arm length.
            max_arm = max(arm_lengths) if arm_lengths else 0
            if max_arm > ARM_BODY_HIGH:
                worst_severity = "high"
                match_line = func_start + match_keyword_offset + 1
                signals.append(
                    f"match at line {match_line}: arm with {max_arm} lines "
                    f"(>{ARM_BODY_HIGH} threshold)"
                )
            elif max_arm > ARM_BODY_MEDIUM:
                if worst_severity != "high":
                    worst_severity = "medium"
                match_line = func_start + match_keyword_offset + 1
                signals.append(
                    f"match at line {match_line}: arm with {max_arm} lines "
                    f"(>{ARM_BODY_MEDIUM} threshold)"
                )

            # Signal 3: dispatch table smell.
            big_arms = sum(1 for length in arm_lengths if length > DISPATCH_ARM_MIN_LINES)
            if len(arm_lengths) > DISPATCH_ARM_COUNT and big_arms > DISPATCH_ARM_COUNT:
                worst_severity = "high"
                match_line = func_start + match_keyword_offset + 1
                signals.append(
                    f"match at line {match_line}: {len(arm_lengths)} arms, "
                    f"{big_arms} with >{DISPATCH_ARM_MIN_LINES} lines "
                    f"(dispatch table smell)"
                )

        if worst_severity and signals:
            hints.append(
                RiskHint(
                    file=rel,
                    symbol=func_name,
                    risk_type="design_smell",
                    severity=worst_severity,
                    signals=signals,
                    ai_instruction=AI_INSTRUCTIONS[worst_severity],
                    review_lens=REVIEW_LENS,
                )
            )

    return hints


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_match_arm_complexity")

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
        if path.suffix != ".rs":
            continue
        if not is_under_target_roots(path, repo_root=REPO_ROOT, target_roots=TARGET_ROOTS):
            continue
        if is_review_probe_test_path(path):
            continue

        report.files_scanned += 1
        text = guard.read_text_from_ref(path, args.head_ref) if args.since_ref else guard.read_text_from_worktree(path)
        if text is None:
            continue

        hints = _scan_rust_file(text, path)
        if hints:
            files_with_hints.add(path.as_posix())
            report.risk_hints.extend(hints)

    report.files_with_hints = len(files_with_hints)
    return emit_probe_report(report, output_format=args.format)


if __name__ == "__main__":
    sys.exit(main())
