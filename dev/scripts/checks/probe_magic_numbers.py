#!/usr/bin/env python3
"""Review probe: detect magic number patterns in Python source files.

Flags unnamed numeric literals used in slicing, comparisons, and
assignments that should be named constants. Named constants make the
intent discoverable and prevent silent drift when limits change.

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
scan_python_functions = import_attr("code_shape_function_policy", "scan_python_functions")

guard = GuardContext(REPO_ROOT)

PYTHON_ROOTS = resolve_quality_scope_roots("python_probe", repo_root=REPO_ROOT)

REVIEW_LENS = "design_quality"

# Thresholds.
MAGIC_SLICE_MEDIUM = 2
MAGIC_SLICE_HIGH = 4

# Regex: slice with magic number — [:N], [N:], [N:M]
# Captures the numeric value and excludes common non-magic slices ([:1], [-1:]).
MAGIC_SLICE_RE = re.compile(
    r"\[(?:"
    r":(\d+)"  # [:N] — take first N
    r"|(\d+):"  # [N:] — skip first N
    r"|(\d+):(\d+)"  # [N:M] — explicit range
    r")\]"
)

# Numbers that are NOT magic (too small/common to be worth naming).
_NON_MAGIC_NUMBERS = frozenset({0, 1, 2, -1})

# Regex: numeric comparison thresholds — if x >= N, if len(x) > N, count < N.
MAGIC_COMPARE_RE = re.compile(r"(?:if|elif|while)\s+.*?(?:>=|<=|>|<|==|!=)\s*(\d{2,})")

AI_INSTRUCTIONS = {
    "slice": (
        "This function uses magic numbers in slice operations. Define "
        "named constants (e.g., MAX_DISPLAY_ITEMS = 10, HASH_PREVIEW_LEN = 12) "
        "to make the limit discoverable and changeable from one place."
    ),
    "threshold": (
        "This function uses unnamed numeric thresholds in conditionals. "
        "Define named constants to document what the number represents "
        "and ensure consistency if the same threshold appears elsewhere."
    ),
}

def _is_magic(n: int) -> bool:
    """Return True if the number is likely a magic number worth flagging."""
    return n not in _NON_MAGIC_NUMBERS and n >= 3

def _scan_function_slices(body: str, func_name: str, rel_path: str) -> list[RiskHint]:
    """Detect magic number slicing in one Python function."""
    hints: list[RiskHint] = []
    magic_slices: list[str] = []

    for match in MAGIC_SLICE_RE.finditer(body):
        groups = match.groups()
        # Extract the numeric values from whichever group matched.
        nums = [int(g) for g in groups if g is not None]
        if any(_is_magic(n) for n in nums):
            magic_slices.append(match.group(0))

    if len(magic_slices) < MAGIC_SLICE_MEDIUM:
        return hints

    severity = "high" if len(magic_slices) >= MAGIC_SLICE_HIGH else "medium"
    sample = ", ".join(magic_slices[:5])
    hints.append(
        RiskHint(
            file=rel_path,
            symbol=func_name,
            risk_type="design_smell",
            severity=severity,
            signals=[f"{len(magic_slices)} magic-number slices ({sample}) — " f"define named constants"],
            ai_instruction=AI_INSTRUCTIONS["slice"],
            review_lens=REVIEW_LENS,
        )
    )
    return hints

def _scan_python_file(text: str, path: Path) -> list[RiskHint]:
    hints: list[RiskHint] = []
    functions = scan_python_functions(text)
    lines = text.splitlines()
    rel = path.as_posix()

    for func in functions:
        start = func["start_line"] - 1
        end = func["end_line"]
        body = "\n".join(lines[start + 1 : end])
        hints.extend(_scan_function_slices(body, func["name"], rel))

    return hints

def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_magic_numbers")

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
        if path.suffix != ".py":
            continue
        if not is_under_target_roots(path, repo_root=REPO_ROOT, target_roots=PYTHON_ROOTS):
            continue
        if is_review_probe_test_path(path):
            continue

        report.files_scanned += 1
        text = guard.read_text_from_ref(path, args.head_ref) if args.since_ref else guard.read_text_from_worktree(path)
        if text is None:
            continue

        hints = _scan_python_file(text, path)
        if hints:
            files_with_hints.add(path.as_posix())
            report.risk_hints.extend(hints)

    report.files_with_hints = len(files_with_hints)
    return emit_probe_report(report, output_format=args.format)

if __name__ == "__main__":
    sys.exit(main())
