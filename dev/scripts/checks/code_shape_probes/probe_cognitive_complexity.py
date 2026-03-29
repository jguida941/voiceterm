#!/usr/bin/env python3
"""Review probe: detect functions with high cognitive complexity.

Measures reading difficulty using nesting-multiplicative penalties.
Unlike check_structural_complexity (flat branch-point + depth sum),
this probe scores each flow-break keyword at (1 + current_nesting_depth)
so deeply nested control flow is penalized progressively.

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
scan_rust_functions = import_attr("code_shape_function_policy", "scan_rust_functions")
strip_cfg_test_blocks = import_attr("rust_check_text_utils", "strip_cfg_test_blocks")

guard = GuardContext(REPO_ROOT)

PYTHON_ROOTS = resolve_quality_scope_roots("python_probe", repo_root=REPO_ROOT)
RUST_ROOTS = resolve_quality_scope_roots("rust_probe", repo_root=REPO_ROOT)

REVIEW_LENS = "design_quality"

MEDIUM_THRESHOLD = 15
HIGH_THRESHOLD = 25

# Flow-break keywords that increment complexity.
FLOW_BREAK_RE = re.compile(r"\b(if|else\s+if|elif|else|for|while|match|loop)\b")

# Mixed boolean operators: each switch between && and || adds +1.
BOOL_AND_RE = re.compile(r"&&")
BOOL_OR_RE = re.compile(r"\|\|")
PY_AND_RE = re.compile(r"\band\b")
PY_OR_RE = re.compile(r"\bor\b")

AI_INSTRUCTIONS = {
    "medium": (
        "This function has moderate cognitive complexity ({score}). "
        "Reduce nesting by extracting inner blocks into helper functions "
        "and using early returns for guard clauses."
    ),
    "high": (
        "This function has high cognitive complexity ({score}). The deeply "
        "nested control flow makes it hard to read. Refactor by: "
        "(1) extracting nested blocks into named helpers, "
        "(2) using early returns to flatten guard clauses, "
        "(3) keeping each function at one level of abstraction."
    ),
}


def _strip_rust_line_noise(line: str) -> str:
    """Remove line comments and string literals from a Rust line."""
    result: list[str] = []
    i = 0
    in_string = False
    escape_next = False
    quote_char = ""
    while i < len(line):
        ch = line[i]
        if escape_next:
            escape_next = False
            i += 1
            continue
        if in_string:
            if ch == "\\":
                escape_next = True
            elif ch == quote_char:
                in_string = False
            i += 1
            continue
        if ch == "/" and i + 1 < len(line) and line[i + 1] == "/":
            break
        if ch in ('"', "'"):
            in_string = True
            quote_char = ch
            i += 1
            continue
        result.append(ch)
        i += 1
    return "".join(result)


def _strip_python_line_noise(line: str) -> str:
    """Remove line comments and string literals from a Python line."""
    result: list[str] = []
    i = 0
    in_string = False
    escape_next = False
    quote_char = ""
    while i < len(line):
        ch = line[i]
        if escape_next:
            escape_next = False
            i += 1
            continue
        if in_string:
            if ch == "\\":
                escape_next = True
            elif ch == quote_char:
                in_string = False
            i += 1
            continue
        if ch == "#":
            break
        if ch in ('"', "'"):
            in_string = True
            quote_char = ch
            i += 1
            continue
        result.append(ch)
        i += 1
    return "".join(result)


def _count_bool_operator_switches(line: str, *, rust: bool) -> int:
    """Count switches between AND/OR boolean operators on one line."""
    if rust:
        and_positions = [m.start() for m in BOOL_AND_RE.finditer(line)]
        or_positions = [m.start() for m in BOOL_OR_RE.finditer(line)]
    else:
        and_positions = [m.start() for m in PY_AND_RE.finditer(line)]
        or_positions = [m.start() for m in PY_OR_RE.finditer(line)]
    if not and_positions and not or_positions:
        return 0
    merged = sorted(
        [("and", p) for p in and_positions] + [("or", p) for p in or_positions],
        key=lambda x: x[1],
    )
    switches = 0
    for i in range(1, len(merged)):
        if merged[i][0] != merged[i - 1][0]:
            switches += 1
    return switches


def _score_rust_function(body_lines: list[str]) -> int:
    """Compute cognitive complexity for a Rust function body."""
    score = 0
    nesting = 0
    for raw_line in body_lines:
        clean = _strip_rust_line_noise(raw_line)
        stripped = clean.strip()
        if not stripped:
            continue
        score += _count_bool_operator_switches(clean, rust=True)
        for _match in FLOW_BREAK_RE.finditer(clean):
            keyword = _match.group(1)
            if keyword == "else":
                score += 1
            else:
                score += 1 + nesting
        open_braces = clean.count("{")
        close_braces = clean.count("}")
        nesting += open_braces - close_braces
        nesting = max(0, nesting)
    return score


def _score_python_function(body_lines: list[str], base_indent: int) -> int:
    """Compute cognitive complexity for a Python function body."""
    score = 0
    for raw_line in body_lines:
        clean = _strip_python_line_noise(raw_line)
        stripped = clean.strip()
        if not stripped:
            continue
        line_indent = len(raw_line) - len(raw_line.lstrip())
        nesting = max(0, (line_indent - base_indent) // 4 - 1)
        score += _count_bool_operator_switches(clean, rust=False)
        for _match in FLOW_BREAK_RE.finditer(clean):
            keyword = _match.group(1)
            if keyword in ("else", "elif"):
                score += 1
            else:
                score += 1 + nesting
    return score


def _scan_rust_file(text: str, path: Path) -> list[RiskHint]:
    """Scan a Rust file for cognitively complex functions."""
    hints: list[RiskHint] = []
    stripped = strip_cfg_test_blocks(text)
    functions = scan_rust_functions(stripped)
    lines = stripped.splitlines()
    rel = path.as_posix()

    for func in functions:
        start = func["start_line"] - 1
        end = func["end_line"]
        body = lines[start:end]
        score = _score_rust_function(body)
        if score < MEDIUM_THRESHOLD:
            continue
        severity = "high" if score >= HIGH_THRESHOLD else "medium"
        hints.append(
            RiskHint(
                file=rel,
                symbol=func["name"],
                risk_type="readability_smell",
                severity=severity,
                signals=[f"cognitive complexity {score} (threshold {MEDIUM_THRESHOLD})"],
                ai_instruction=AI_INSTRUCTIONS[severity].format(score=score),
                review_lens=REVIEW_LENS,
            )
        )
    return hints


def _scan_python_file(text: str, path: Path) -> list[RiskHint]:
    """Scan a Python file for cognitively complex functions."""
    hints: list[RiskHint] = []
    functions = scan_python_functions(text)
    lines = text.splitlines()
    rel = path.as_posix()

    for func in functions:
        start = func["start_line"] - 1
        end = func["end_line"]
        body = lines[start:end]
        def_line = lines[start] if start < len(lines) else ""
        base_indent = len(def_line) - len(def_line.lstrip())
        score = _score_python_function(body, base_indent)
        if score < MEDIUM_THRESHOLD:
            continue
        severity = "high" if score >= HIGH_THRESHOLD else "medium"
        hints.append(
            RiskHint(
                file=rel,
                symbol=func["name"],
                risk_type="readability_smell",
                severity=severity,
                signals=[f"cognitive complexity {score} (threshold {MEDIUM_THRESHOLD})"],
                ai_instruction=AI_INSTRUCTIONS[severity].format(score=score),
                review_lens=REVIEW_LENS,
            )
        )
    return hints


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_cognitive_complexity")

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
