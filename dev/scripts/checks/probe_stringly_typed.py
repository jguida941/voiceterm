#!/usr/bin/env python3
"""Review probe: detect stringly-typed dispatch patterns.

Flags functions that compare the same variable against 3+ string
literals (``if x == "foo" elif x == "bar" elif x == "baz"``).
These should be proper enums (Python ``StrEnum``, Rust ``enum``).

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
STRING_COMPARE_MEDIUM = 3
STRING_COMPARE_HIGH = 5

# Python: variable == "literal" or variable == 'literal'
PY_STR_CMP_RE = re.compile(r"\b(\w+)\s*==\s*[\"']([^\"']+)[\"']")

# Python: "literal" in {set} pattern — detects action/status sets
PY_STR_SET_RE = re.compile(
    r'\{[^}]*"[^"]*"(?:\s*,\s*"[^"]*"){2,}[^}]*\}'
)

# Rust: "literal" => in match arms
RS_STR_MATCH_RE = re.compile(r'"([^"]+)"\s*=>')

AI_INSTRUCTIONS = {
    "medium": (
        "This function compares a variable against multiple string "
        "literals. Define an enum (Python StrEnum / Rust enum) to "
        "replace the magic strings with typed variants."
    ),
    "high": (
        "This function has extensive string-based dispatch. Replace "
        "magic string comparisons with a proper enum type. This "
        "prevents typos, enables exhaustiveness checking, and makes "
        "the valid values discoverable."
    ),
}
def _scan_python_function_body(
    body: str, func_name: str, rel_path: str
) -> list[RiskHint]:
    """Detect string-comparison chains in one Python function."""
    hints: list[RiskHint] = []
    var_counts: Counter = Counter()

    for match in PY_STR_CMP_RE.finditer(body):
        var_name = match.group(1)
        var_counts[var_name] += 1

    for var, count in var_counts.most_common(3):
        if count < STRING_COMPARE_MEDIUM:
            continue
        # Collect the literal values being compared.
        literals = [
            m.group(2)
            for m in PY_STR_CMP_RE.finditer(body)
            if m.group(1) == var
        ]
        sample = ", ".join(f'"{v}"' for v in literals[:5])
        severity = "high" if count >= STRING_COMPARE_HIGH else "medium"
        hints.append(
            RiskHint(
                file=rel_path,
                symbol=func_name,
                risk_type="design_smell",
                severity=severity,
                signals=[
                    f"'{var}' compared against {count} string literals "
                    f"({sample}) — use enum"
                ],
                ai_instruction=AI_INSTRUCTIONS[severity],
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
        hints.extend(
            _scan_python_function_body(body, func["name"], rel)
        )

    return hints


def _scan_rust_file(text: str, path: Path) -> list[RiskHint]:
    """Detect match arms with 3+ string literal patterns per function."""
    hints: list[RiskHint] = []
    stripped = strip_cfg_test_blocks(text)
    functions = scan_rust_functions(stripped)
    lines = stripped.splitlines()
    rel = path.as_posix()

    # Trait impl functions where string matching IS the correct pattern.
    _RUST_PARSER_FUNCTIONS = frozenset({
        "from_str", "try_from", "from", "deserialize", "parse",
    })

    for func in functions:
        if func["name"] in _RUST_PARSER_FUNCTIONS:
            continue

        start = func["start_line"] - 1
        end = func["end_line"]
        body = "\n".join(lines[start:end])

        str_arms = RS_STR_MATCH_RE.findall(body)
        count = len(str_arms)
        if count < STRING_COMPARE_MEDIUM:
            continue

        sample = ", ".join(f'"{v}"' for v in str_arms[:5])
        severity = "high" if count >= STRING_COMPARE_HIGH else "medium"
        hints.append(
            RiskHint(
                file=rel,
                symbol=func["name"],
                risk_type="design_smell",
                severity=severity,
                signals=[
                    f"match with {count} string-literal arms "
                    f"({sample}) — use enum"
                ],
                ai_instruction=AI_INSTRUCTIONS[severity],
                review_lens=REVIEW_LENS,
            )
        )

    return hints


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_stringly_typed")

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
