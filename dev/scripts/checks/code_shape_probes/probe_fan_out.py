#!/usr/bin/env python3
"""Review probe: detect functions with excessive call fan-out.

Functions that call many distinct targets act as hub functions — they
orchestrate too many concerns and become change magnets.  The fix is to
split grouped calls into sub-orchestrators, each responsible for one
aspect of the work.

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

# Thresholds: distinct call targets per function.
FAN_OUT_MEDIUM = 15
FAN_OUT_HIGH = 20

# Regex to detect function/method call targets.
CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")

# Keywords that look like calls but are not function invocations.
_SHARED_EXCLUDES = frozenset({"if", "for", "while", "return"})
_PYTHON_EXCLUDES = frozenset({
    "class", "def", "lambda", "assert", "raise", "except", "with",
    # Built-in type constructors and conversions (noise, not real fan-out).
    "str", "int", "float", "bool", "list", "dict", "set", "tuple",
    "type", "len", "range", "enumerate", "zip", "map", "filter",
    "sorted", "reversed", "isinstance", "issubclass", "hasattr",
    "getattr", "setattr", "super",
})
_RUST_EXCLUDES = frozenset({"match", "loop", "unsafe", "where"})

PYTHON_EXCLUDES = _SHARED_EXCLUDES | _PYTHON_EXCLUDES
RUST_EXCLUDES = _SHARED_EXCLUDES | _RUST_EXCLUDES

# Regex to detect Rust macro calls (name! or name!{).
RUST_MACRO_RE = re.compile(r"\b([A-Za-z_]\w*)\s*!")

AI_INSTRUCTIONS = {
    "medium": (
        "This function calls {count} different functions — it orchestrates "
        "too many concerns. Extract groups of related calls into "
        "sub-orchestrators, each responsible for one aspect of the work."
    ),
    "high": (
        "This function calls {count} different functions — a hub function "
        "with excessive coupling. Break into focused sub-functions: "
        "separate setup, computation, and output phases into their own "
        "orchestrators."
    ),
}


def _extract_function_body(lines: list[str], func: dict) -> list[str]:
    """Return the body lines for a scanned function dict."""
    start = func["start_line"] - 1
    end = func["end_line"]
    return lines[start:end]


def _count_python_calls(body_lines: list[str]) -> int:
    """Count unique call targets in a Python function body."""
    targets: set[str] = set()
    for line in body_lines:
        for match in CALL_RE.finditer(line):
            name = match.group(1)
            if name not in PYTHON_EXCLUDES:
                targets.add(name)
    return len(targets)


def _count_rust_calls(body_lines: list[str]) -> int:
    """Count unique call targets in a Rust function body."""
    targets: set[str] = set()
    macros: set[str] = set()
    for line in body_lines:
        for match in CALL_RE.finditer(line):
            name = match.group(1)
            if name not in RUST_EXCLUDES:
                targets.add(name)
        for match in RUST_MACRO_RE.finditer(line):
            macros.add(match.group(1))
    # Macros are tracked but counted toward the total fan-out.
    return len(targets | macros)


def _scan_python_file(text: str, path: Path) -> list[RiskHint]:
    hints: list[RiskHint] = []
    functions = scan_python_functions(text)
    lines = text.splitlines()
    rel = path.as_posix()

    for func in functions:
        body = _extract_function_body(lines, func)
        count = _count_python_calls(body)
        if count < FAN_OUT_MEDIUM:
            continue

        severity = "high" if count >= FAN_OUT_HIGH else "medium"
        hints.append(
            RiskHint(
                file=rel,
                symbol=func["name"],
                risk_type="coupling_smell",
                severity=severity,
                signals=[f"{count} distinct calls — hub function, split into sub-orchestrators"],
                ai_instruction=AI_INSTRUCTIONS[severity].format(count=count),
                review_lens=REVIEW_LENS,
            )
        )

    return hints


def _scan_rust_file(text: str, path: Path) -> list[RiskHint]:
    hints: list[RiskHint] = []
    stripped = strip_cfg_test_blocks(text)
    functions = scan_rust_functions(stripped)
    lines = stripped.splitlines()
    rel = path.as_posix()

    for func in functions:
        body = _extract_function_body(lines, func)
        count = _count_rust_calls(body)
        if count < FAN_OUT_MEDIUM:
            continue

        severity = "high" if count >= FAN_OUT_HIGH else "medium"
        hints.append(
            RiskHint(
                file=rel,
                symbol=func["name"],
                risk_type="coupling_smell",
                severity=severity,
                signals=[f"{count} distinct calls — hub function, split into sub-orchestrators"],
                ai_instruction=AI_INSTRUCTIONS[severity].format(count=count),
                review_lens=REVIEW_LENS,
            )
        )

    return hints


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_fan_out")

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
