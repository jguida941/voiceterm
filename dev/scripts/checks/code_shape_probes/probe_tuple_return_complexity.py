#!/usr/bin/env python3
"""Review probe: detect Rust functions returning tuples with 3+ elements.

Large tuple returns produce unreadable call sites where each element is
accessed by position (.0, .1, .2) instead of a descriptive field name.
Define a named struct so call sites document what each value represents.

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

guard = GuardContext(REPO_ROOT)

TARGET_ROOTS = resolve_quality_scope_roots("rust_probe", repo_root=REPO_ROOT)

REVIEW_LENS = "design_quality"

AI_INSTRUCTIONS = {
    "medium": (
        "This function returns a 3-element tuple. Define a named struct "
        "with descriptive field names so call sites access results by "
        "name instead of position."
    ),
    "high": (
        "This function returns a {count}-element tuple — call sites are "
        "unreadable. Define a named struct (e.g., "
        "`struct Result {{ field1: T, field2: U, ... }}`) "
        "with descriptive field names instead."
    ),
}

# Regex: match `-> ` in a function signature to locate the return type.
ARROW_RE = re.compile(r"->\s*")

# Regex: match `Result<...>` wrapping a tuple (excluded from detection).
RESULT_WRAP_RE = re.compile(r"^Result\s*<")


def _count_top_level_tuple_elements(type_text: str) -> int:
    """Count comma-separated elements at the top level of a tuple type.

    Tracks angle-bracket depth so nested generics like ``Result<T, E>``
    are treated as a single element.  Returns 0 when the text is not a
    parenthesized tuple.
    """
    text = type_text.strip()
    if not text.startswith("("):
        return 0

    # Walk past the opening paren, tracking depth for nested delimiters.
    depth_angle = 0
    depth_paren = 0
    commas = 0
    i = 1  # skip leading '('
    while i < len(text):
        ch = text[i]
        if ch == "<":
            depth_angle += 1
        elif ch == ">" and depth_angle > 0:
            depth_angle -= 1
        elif ch == "(":
            depth_paren += 1
        elif ch == ")":
            if depth_paren == 0:
                # Closing paren of the outermost tuple.
                break
            depth_paren -= 1
        elif ch == "," and depth_angle == 0 and depth_paren == 0:
            commas += 1
        i += 1

    return commas + 1 if commas > 0 else 1


def _extract_return_type(sig_text: str) -> str | None:
    """Extract the return type string from a combined signature block.

    Returns None when the signature has no ``->`` or when the outer
    return type is ``Result<(...)>`` (the tuple is wrapped, not bare).
    """
    match = ARROW_RE.search(sig_text)
    if not match:
        return None

    raw = sig_text[match.end():].strip()
    # Strip trailing opening brace and where-clauses that follow the type.
    # Walk forward to find the balanced end of the type expression.
    depth_angle = 0
    depth_paren = 0
    end = 0
    for idx, ch in enumerate(raw):
        if ch == "{" and depth_angle == 0 and depth_paren == 0:
            end = idx
            break
        if ch == "<":
            depth_angle += 1
        elif ch == ">" and depth_angle > 0:
            depth_angle -= 1
        elif ch == "(":
            depth_paren += 1
        elif ch == ")":
            depth_paren -= 1
    else:
        end = len(raw)

    ret_type = raw[:end].strip().rstrip(",").strip()
    if not ret_type:
        return None

    # Exclude Result<(T, U, V), E> — the tuple is inside Result, not bare.
    if RESULT_WRAP_RE.match(ret_type):
        return None

    return ret_type


def _build_signature_block(lines: list[str], start: int) -> str:
    """Combine function signature lines from ``fn`` through opening ``{``."""
    parts: list[str] = []
    for line in lines[start:]:
        parts.append(line)
        if "{" in line:
            break
    return " ".join(parts)


def _scan_rust_file(text: str, path: Path) -> list[RiskHint]:
    """Detect functions returning large tuples in one Rust file."""
    hints: list[RiskHint] = []
    stripped = strip_cfg_test_blocks(text)
    functions = scan_rust_functions(stripped)
    lines = stripped.splitlines()
    rel = path.as_posix()

    for func in functions:
        func_name = func["name"]
        start = func["start_line"] - 1  # 0-based index

        sig_block = _build_signature_block(lines, start)
        ret_type = _extract_return_type(sig_block)
        if ret_type is None:
            continue

        count = _count_top_level_tuple_elements(ret_type)
        if count < 3:
            continue

        severity = "high" if count >= 4 else "medium"
        instruction = AI_INSTRUCTIONS[severity].format(count=count)

        hints.append(
            RiskHint(
                file=rel,
                symbol=func_name,
                risk_type="design_smell",
                severity=severity,
                signals=[
                    f"returns {count}-element tuple — define a named "
                    f"struct with descriptive fields instead"
                ],
                ai_instruction=instruction,
                review_lens=REVIEW_LENS,
            )
        )

    return hints


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_tuple_return_complexity")

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
        text = (
            guard.read_text_from_ref(path, args.head_ref)
            if args.since_ref
            else guard.read_text_from_worktree(path)
        )
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
