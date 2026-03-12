#!/usr/bin/env python3
"""Review probe: detect unnecessary intermediate variables in Python code.

AI agents frequently write:
    result = some_expression()
    return result

instead of simply `return some_expression()`. This wastes a name and a line
without adding clarity. If the variable name is meaningful (e.g., `validated_config`),
it stays; if it's generic (`result`, `ret`, `output`, `tmp`, `value`), it's noise.

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

list_changed_paths_with_base_map = import_attr("git_change_paths", "list_changed_paths_with_base_map")
GuardContext = import_attr("rust_guard_common", "GuardContext")
is_review_probe_test_path = import_attr("probe_path_filters", "is_review_probe_test_path")
scan_python_functions = import_attr("code_shape_function_policy", "scan_python_functions")

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)

PYTHON_ROOTS = resolve_quality_scope_roots("python_probe", repo_root=REPO_ROOT)

REVIEW_LENS = "design_quality"

# Generic variable names that add no information.
GENERIC_NAMES = frozenset(
    {
        "result",
        "results",
        "ret",
        "retval",
        "return_value",
        "output",
        "out",
        "tmp",
        "temp",
        "val",
        "value",
        "data",
        "rv",
        "res",
        "response",
    }
)

# Minimum instances per function to flag.
THRESHOLD_MEDIUM = 2
THRESHOLD_HIGH = 4

# Regex: detect `name = expr` on one line, `return name` on the very next line.
# The variable name must be word-only and the assignment must not be augmented (+=, etc.).
ASSIGN_RETURN_RE = re.compile(
    r"^(\s+)(\w+)\s*=\s*(.+)\n"  # Line 1: assignment
    r"\1return\s+\2\s*$",  # Line 2: return same variable (same indent)
    re.MULTILINE,
)

AI_INSTRUCTION = (
    "This function assigns an expression to a generic variable name only to "
    "immediately return it. Remove the intermediate variable and return the "
    "expression directly. Use intermediate variables only when the name "
    "communicates meaningful intent (e.g., `validated_config` not `result`)."
)


def _scan_python_file(text: str, path: Path) -> list[RiskHint]:
    """Detect unnecessary intermediates in one Python file."""
    hints: list[RiskHint] = []
    functions = scan_python_functions(text)
    lines = text.splitlines()
    rel = path.as_posix()

    for func in functions:
        func_name = func["name"]
        start = func["start_line"] - 1
        end = func["end_line"]
        body = "\n".join(lines[start + 1 : end])

        # Find all assign-then-return patterns.
        matches = ASSIGN_RETURN_RE.findall(body)
        generic_matches = [(indent, var_name, expr) for indent, var_name, expr in matches if var_name in GENERIC_NAMES]

        if not generic_matches:
            continue

        count = len(generic_matches)
        if count < THRESHOLD_MEDIUM:
            continue

        severity = "high" if count >= THRESHOLD_HIGH else "medium"
        sample_vars = ", ".join(f"`{m[1]}`" for m in generic_matches[:3])
        hints.append(
            RiskHint(
                file=rel,
                symbol=func_name,
                risk_type="design_smell",
                severity=severity,
                signals=[
                    f"{count} assign-then-return patterns with generic names "
                    f"({sample_vars}) — return the expression directly"
                ],
                ai_instruction=AI_INSTRUCTION,
                review_lens=REVIEW_LENS,
            )
        )

    return hints


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_unnecessary_intermediates")

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
