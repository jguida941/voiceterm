#!/usr/bin/env python3
"""Review probe: detect functions that mix value computation with I/O side effects.

Functions that both compute a return value AND perform disk/stdout writes
violate separation of concerns. The fix is to split into a pure function
that returns data and a thin I/O wrapper that writes it.

This probe always exits 0. It emits structured risk hints for AI
review instead of blocking CI.
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

try:
    if __package__:
        from .common import load_probe_text, should_scan_python_probe_path
    else:  # pragma: no cover
        from dev.scripts.checks.code_shape_probes.common import (
            load_probe_text,
            should_scan_python_probe_path,
        )
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.code_shape_probes.common import (
        load_probe_text,
        should_scan_python_probe_path,
    )

list_changed_paths_with_base_map = import_attr("git_change_paths", "list_changed_paths_with_base_map")
GuardContext = import_attr("rust_guard_common", "GuardContext")
is_review_probe_test_path = import_attr("probe_path_filters", "is_review_probe_test_path")
scan_python_functions = import_attr("code_shape_function_policy", "scan_python_functions")

guard = GuardContext(REPO_ROOT)

TARGET_ROOTS = resolve_quality_scope_roots("python_probe", repo_root=REPO_ROOT)

REVIEW_LENS = "design_quality"

# Function names excluded from analysis (entry points that naturally mix I/O).
_MAIN_FUNCTION_NAMES = frozenset({"main", "__main__", "_main"})

# I/O operation patterns (each matches one side-effect call site).
_IO_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\.write_text\s*\("),
    re.compile(r"\.write_bytes\s*\("),
    re.compile(r"\.write\s*\("),
    re.compile(r"\bopen\s*\(.*['\"][wa]['\"]"),
    re.compile(r"(?<!\w)print\s*\("),
    re.compile(r"\bsys\.stdout\.write\s*\("),
    re.compile(r"\bsys\.stderr\.write\s*\("),
    re.compile(r"\bsubprocess\.run\s*\("),
    re.compile(r"\bsubprocess\.call\s*\("),
    re.compile(r"\bsubprocess\.Popen\s*\("),
)

# Non-None return: matches `return <expr>` where expr is not empty or None.
_NON_NONE_RETURN_RE = re.compile(r"^\s*return\s+(?!None\s*$)(.+)$", re.MULTILINE)

# Logging calls are NOT I/O side effects for this probe.
_LOGGING_LINE_RE = re.compile(r"^\s*logging\.\w+\s*\(")

AI_INSTRUCTIONS = {
    "medium": (
        "This function both computes a value and performs I/O. Split into "
        "a pure function returning data and a thin I/O wrapper: "
        "`content = pure_compute(); path.write_text(content)`."
    ),
    "high": (
        "This function mixes computation with multiple I/O operations. "
        "Extract the pure computation into its own function, then write "
        "a thin wrapper that calls the pure function and handles all I/O."
    ),
}


def _count_io_operations(body: str) -> int:
    """Count distinct I/O operation call sites in a function body.

    Lines that are pure logging calls (logging.info/debug/warning/error)
    are excluded before counting.
    """
    filtered_lines = [
        line for line in body.splitlines()
        if not _LOGGING_LINE_RE.match(line)
    ]
    filtered_body = "\n".join(filtered_lines)
    count = 0
    for pattern in _IO_PATTERNS:
        count += len(pattern.findall(filtered_body))
    return count


def _has_non_none_return(body: str) -> bool:
    """Return True if the function body contains at least one non-None return."""
    return bool(_NON_NONE_RETURN_RE.search(body))


def _scan_function_side_effects(text: str, path: Path) -> list[RiskHint]:
    """Scan one Python file for functions mixing computation with I/O."""
    hints: list[RiskHint] = []
    functions = scan_python_functions(text)
    lines = text.splitlines()
    rel_path = path.as_posix()

    for func in functions:
        func_name = func["name"]
        if func_name in _MAIN_FUNCTION_NAMES:
            continue

        start = func["start_line"] - 1
        end = func["end_line"]
        body_lines = lines[start + 1 : end]
        body = "\n".join(body_lines)

        if not _has_non_none_return(body):
            continue

        io_count = _count_io_operations(body)
        if io_count == 0:
            continue

        severity = "high" if io_count >= 2 else "medium"
        io_label = "I/O operation" if io_count == 1 else "I/O operations"
        signals = [
            f"returns a computed value and performs {io_count} {io_label}"
        ]
        hints.append(
            RiskHint(
                file=rel_path,
                symbol=func_name,
                risk_type="design_smell",
                severity=severity,
                signals=signals,
                ai_instruction=AI_INSTRUCTIONS[severity],
                review_lens=REVIEW_LENS,
            )
        )

    return hints

def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_side_effect_mixing")

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
        if not should_scan_python_probe_path(
            path,
            target_roots=TARGET_ROOTS,
            is_review_probe_test_path=is_review_probe_test_path,
        ):
            continue

        report.files_scanned += 1
        text = load_probe_text(
            path,
            guard=guard,
            since_ref=args.since_ref,
            head_ref=args.head_ref,
        )
        if text is None:
            continue

        hints = _scan_function_side_effects(text, path)
        if hints:
            files_with_hints.add(path.as_posix())
            report.risk_hints.extend(hints)

    report.files_with_hints = len(files_with_hints)
    return emit_probe_report(report, output_format=args.format)


if __name__ == "__main__":
    sys.exit(main())
