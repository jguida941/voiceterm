#!/usr/bin/env python3
"""Review probe: detect functions with excessive boolean parameters.

Functions with 3+ boolean parameters are hard to call correctly —
callers end up writing ``foo(True, False, True, False)`` which is
unreadable.  The fix is to bundle related bools into an options
struct (Rust) or dataclass (Python).

This probe always exits 0.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    from check_bootstrap import (
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

list_changed_paths_with_base_map = import_attr(
    "git_change_paths", "list_changed_paths_with_base_map"
)
GuardContext = import_attr("rust_guard_common", "GuardContext")
is_review_probe_test_path = import_attr(
    "probe_path_filters", "is_review_probe_test_path"
)
scan_python_functions = import_attr(
    "code_shape_function_policy", "scan_python_functions"
)
scan_rust_functions = import_attr(
    "code_shape_function_policy", "scan_rust_functions"
)
strip_cfg_test_blocks = import_attr("rust_check_text_utils", "strip_cfg_test_blocks")

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)

PYTHON_ROOTS = resolve_quality_scope_roots("python_probe", repo_root=REPO_ROOT)
RUST_ROOTS = resolve_quality_scope_roots("rust_probe", repo_root=REPO_ROOT)

REVIEW_LENS = "design_quality"

# Thresholds.
BOOL_PARAM_MEDIUM = 3
BOOL_PARAM_HIGH = 5

# Regex: Python `: bool` in a function signature line.
PY_BOOL_PARAM_RE = re.compile(r"(\w+)\s*:\s*bool\b")

# Regex: Rust `name: bool` in a function signature.
RS_BOOL_PARAM_RE = re.compile(r"(\w+)\s*:\s*bool\b")

AI_INSTRUCTIONS = {
    "medium": (
        "This function has multiple boolean parameters. Create an "
        "options struct (Rust) or dataclass (Python) to bundle related "
        "flags, making call sites self-documenting."
    ),
    "high": (
        "This function has many boolean parameters, making call sites "
        "unreadable (e.g. foo(True, False, True, False)). Refactor into "
        "an options struct/dataclass grouping related flags."
    ),
}
def _extract_python_signature(lines: list[str], func: dict) -> str:
    """Extract multi-line function signature from def to first `:`."""
    start = func["start_line"] - 1
    sig_lines: list[str] = []
    for i in range(start, min(start + 10, len(lines))):
        sig_lines.append(lines[i])
        if ":" in lines[i] and not lines[i].strip().startswith("def"):
            break
        if lines[i].rstrip().endswith(":"):
            break
    return " ".join(sig_lines)


def _extract_rust_signature(lines: list[str], func: dict) -> str:
    """Extract multi-line function signature from fn to opening `{`."""
    start = func["start_line"] - 1
    sig_lines: list[str] = []
    for i in range(start, min(start + 15, len(lines))):
        sig_lines.append(lines[i])
        if "{" in lines[i]:
            break
    return " ".join(sig_lines)


def _scan_python_file(text: str, path: Path) -> list[RiskHint]:
    hints: list[RiskHint] = []
    functions = scan_python_functions(text)
    lines = text.splitlines()
    rel = path.as_posix()

    for func in functions:
        sig = _extract_python_signature(lines, func)
        bool_params = PY_BOOL_PARAM_RE.findall(sig)
        count = len(bool_params)
        if count < BOOL_PARAM_MEDIUM:
            continue

        severity = "high" if count >= BOOL_PARAM_HIGH else "medium"
        param_names = ", ".join(bool_params[:6])
        hints.append(
            RiskHint(
                file=rel,
                symbol=func["name"],
                risk_type="design_smell",
                severity=severity,
                signals=[
                    f"{count} bool parameters ({param_names}) — "
                    f"bundle into options dataclass"
                ],
                ai_instruction=AI_INSTRUCTIONS[severity],
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
        sig = _extract_rust_signature(lines, func)
        bool_params = RS_BOOL_PARAM_RE.findall(sig)
        count = len(bool_params)
        if count < BOOL_PARAM_MEDIUM:
            continue

        severity = "high" if count >= BOOL_PARAM_HIGH else "medium"
        param_names = ", ".join(bool_params[:6])
        hints.append(
            RiskHint(
                file=rel,
                symbol=func["name"],
                risk_type="design_smell",
                severity=severity,
                signals=[
                    f"{count} bool parameters ({param_names}) — "
                    f"bundle into options struct"
                ],
                ai_instruction=AI_INSTRUCTIONS[severity],
                review_lens=REVIEW_LENS,
            )
        )

    return hints


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_boolean_params")

    try:
        if args.since_ref:
            guard.validate_ref(args.since_ref)
            guard.validate_ref(args.head_ref)
        changed_paths, _base_map = list_changed_paths_with_base_map(
            guard.run_git, args.since_ref, args.head_ref,
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

        is_python = path.suffix == ".py" and is_under_target_roots(
            path, repo_root=REPO_ROOT, target_roots=PYTHON_ROOTS
        )
        is_rust = path.suffix == ".rs" and is_under_target_roots(
            path, repo_root=REPO_ROOT, target_roots=RUST_ROOTS
        )
        if not is_python and not is_rust:
            continue

        report.files_scanned += 1
        text = (
            guard.read_text_from_ref(path, args.head_ref)
            if args.since_ref
            else guard.read_text_from_worktree(path)
        )
        if text is None:
            continue

        hints = (
            _scan_python_file(text, path)
            if is_python
            else _scan_rust_file(text, path)
        )
        if hints:
            files_with_hints.add(path.as_posix())
            report.risk_hints.extend(hints)

    report.files_with_hints = len(files_with_hints)
    return emit_probe_report(report, output_format=args.format)


if __name__ == "__main__":
    sys.exit(main())
