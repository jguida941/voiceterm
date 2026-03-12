#!/usr/bin/env python3
"""Review probe: detect defensive over-checking patterns in Python code.

AI agents frequently produce redundant type-checking patterns such as:
    if isinstance(x, str): ...
    elif isinstance(x, int): ...
    elif isinstance(x, float): ...
    elif isinstance(x, bool): ...

Instead of: isinstance(x, (str, int, float, bool)) or match/case.
This probe flags functions with 3+ consecutive isinstance checks on the
same variable — a signal that the type dispatch should be consolidated.

This probe always exits 0.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
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

list_changed_paths_with_base_map = import_attr("git_change_paths", "list_changed_paths_with_base_map")
GuardContext = import_attr("rust_guard_common", "GuardContext")
is_review_probe_test_path = import_attr("probe_path_filters", "is_review_probe_test_path")
scan_python_functions = import_attr("code_shape_function_policy", "scan_python_functions")

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)

PYTHON_ROOTS = resolve_quality_scope_roots("python_probe", repo_root=REPO_ROOT)

REVIEW_LENS = "design_quality"

# Thresholds.
ISINSTANCE_MEDIUM = 3
ISINSTANCE_HIGH = 5

# Regex: isinstance(variable, Type) — captures the variable name.
ISINSTANCE_RE = re.compile(r"isinstance\s*\(\s*(\w+)\s*,")

AI_INSTRUCTIONS = {
    "medium": (
        "This function has multiple isinstance() checks on the same variable. "
        "Consolidate into a single isinstance(x, (A, B, C)) call, or use "
        "match/case (Python 3.10+) for structural pattern matching."
    ),
    "high": (
        "This function has excessive isinstance() checks suggesting a type "
        "dispatch table. Use match/case for clean pattern matching, or define "
        "a Protocol/ABC and let polymorphism handle the dispatch."
    ),
}


def _build_isinstance_hint(
    *,
    rel_path: str,
    func_name: str,
    var_name: str,
    count: int,
) -> RiskHint:
    severity = "high" if count >= ISINSTANCE_HIGH else "medium"
    signal = (
        f"{count} isinstance() checks on `{var_name}` — consolidate into "
        f"isinstance({var_name}, (A, B, ...)) or use match/case"
    )
    return RiskHint(
        file=rel_path,
        symbol=func_name,
        risk_type="design_smell",
        severity=severity,
        signals=[signal],
        ai_instruction=AI_INSTRUCTIONS[severity],
        review_lens=REVIEW_LENS,
    )


def _scan_python_file(text: str, path: Path) -> list[RiskHint]:
    """Detect isinstance over-checking in one Python file."""
    hints: list[RiskHint] = []
    functions = scan_python_functions(text)
    lines = text.splitlines()
    rel = path.as_posix()

    for func in functions:
        func_name = func["name"]
        start = func["start_line"] - 1
        end = func["end_line"]
        body = "\n".join(lines[start + 1 : end])

        # Count isinstance checks per variable.
        var_counts = Counter(m.group(1) for m in ISINSTANCE_RE.finditer(body))

        # Find variables with too many isinstance checks.
        for var_name, count in var_counts.most_common():
            if count < ISINSTANCE_MEDIUM:
                break
            hints.append(
                _build_isinstance_hint(
                    rel_path=rel,
                    func_name=func_name,
                    var_name=var_name,
                    count=count,
                )
            )

    return hints


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_defensive_overchecking")

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
