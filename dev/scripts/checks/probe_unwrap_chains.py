#!/usr/bin/env python3
"""Review probe: detect .unwrap()/.expect() chains in Rust production code.

Functions with multiple unwrap/expect calls in non-test code indicate
missing error propagation. These should use the `?` operator or proper
error handling to avoid panics in production.

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
scan_rust_functions = import_attr("code_shape_function_policy", "scan_rust_functions")
strip_cfg_test_blocks = import_attr("rust_check_text_utils", "strip_cfg_test_blocks")

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)

TARGET_ROOTS = resolve_quality_scope_roots("rust_probe", repo_root=REPO_ROOT)

REVIEW_LENS = "error_handling"

# Thresholds.
UNWRAP_MEDIUM = 3
UNWRAP_HIGH = 5

# Regex: .unwrap() calls — excludes comments and string literals.
UNWRAP_RE = re.compile(r"\.\s*unwrap\s*\(\s*\)")

# Regex: .expect("...") calls.
EXPECT_RE = re.compile(r"\.\s*expect\s*\(\s*\"")

# Functions where unwrap is acceptable (test helpers, builder patterns, etc.).
_UNWRAP_ALLOWLIST_FUNCTIONS = frozenset(
    {
        "main",  # main() is the top-level entry point; panics there are acceptable
        "test_",  # test function prefix (belt-and-suspenders with test path skip)
    }
)

# Patterns in function body that indicate unwrap is justified.
_JUSTIFIED_UNWRAP_PATTERNS = [
    "// unwrap: ",  # Explicit rationale comment
    "// SAFETY:",  # Safety comment for unsafe-adjacent code
    "// panic: ",  # Explicit panic justification
    "debug_assert",  # Debug-only assertion context
]

AI_INSTRUCTIONS = {
    "medium": (
        "This function has multiple .unwrap()/.expect() calls that will "
        "panic on failure. Replace with the ? operator to propagate errors "
        "to the caller, or use .unwrap_or_default() / .unwrap_or_else() "
        "for recoverable cases."
    ),
    "high": (
        "This function has extensive unwrap/expect usage creating multiple "
        "potential panic points. Refactor error handling to use Result<T, E> "
        "return types with the ? operator. Each unwrap is a crash waiting "
        "to happen in production."
    ),
}


def _has_justified_unwraps(body: str) -> bool:
    """Check if unwraps in the body have explicit justification comments."""
    return any(pattern in body for pattern in _JUSTIFIED_UNWRAP_PATTERNS)


def _scan_rust_file(text: str, path: Path) -> list[RiskHint]:
    """Detect functions with excessive unwrap/expect in one Rust file."""
    hints: list[RiskHint] = []
    stripped = strip_cfg_test_blocks(text)
    functions = scan_rust_functions(stripped)
    lines = stripped.splitlines()
    rel = path.as_posix()

    for func in functions:
        func_name = func["name"]

        # Skip test helpers and allowlisted functions.
        if any(func_name.startswith(prefix) for prefix in _UNWRAP_ALLOWLIST_FUNCTIONS):
            continue

        start = func["start_line"] - 1
        end = func["end_line"]
        body = "\n".join(lines[start:end])

        # Count unwrap + expect calls.
        unwrap_count = len(UNWRAP_RE.findall(body))
        expect_count = len(EXPECT_RE.findall(body))
        total = unwrap_count + expect_count

        if total < UNWRAP_MEDIUM:
            continue

        # Skip if the function has explicit justification comments.
        if _has_justified_unwraps(body):
            continue

        severity = "high" if total >= UNWRAP_HIGH else "medium"
        parts = []
        if unwrap_count:
            parts.append(f"{unwrap_count} .unwrap()")
        if expect_count:
            parts.append(f"{expect_count} .expect()")

        hints.append(
            RiskHint(
                file=rel,
                symbol=func_name,
                risk_type="error_handling",
                severity=severity,
                signals=[f"{' + '.join(parts)} calls ({total} total) — " f"use ? operator or proper error handling"],
                ai_instruction=AI_INSTRUCTIONS[severity],
                review_lens=REVIEW_LENS,
            )
        )

    return hints


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_unwrap_chains")

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
