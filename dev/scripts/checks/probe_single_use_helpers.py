#!/usr/bin/env python3
"""Review probe: detect private functions called only once in Python code.

AI agents aggressively extract tiny helper functions even when the logic is
only used in one place. This fragments the control flow — the reader must
jump between functions to follow what happens. A private function called
exactly once adds indirection without reuse.

Excluded: dunder methods, test helpers, decorators, callbacks.

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

# Minimum function lines to flag — very short helpers (1-4 lines) are fine.
MIN_HELPER_LINES = 5

# Minimum single-use helpers per file to trigger a finding.
FILE_THRESHOLD_MEDIUM = 3
FILE_THRESHOLD_HIGH = 6

# Regex: function definition — `def _name(...):`.
PRIVATE_DEF_RE = re.compile(r"^\s*def\s+(_[a-zA-Z]\w*)\s*\(", re.MULTILINE)

# Names to skip even if they look private.
_SKIP_PREFIXES = frozenset(
    {
        "__",  # Dunder methods
        "_test_",  # Test helpers
        "_fixture_",  # Fixture builders
        "_mock_",  # Mock builders
    }
)

# Common callback/hook names that are registered, not called directly.
_CALLBACK_PATTERNS = frozenset(
    {
        "_on_",
        "_handle_",
        "_hook_",
        "_callback_",
        "_listener_",
    }
)

AI_INSTRUCTION = (
    "This file has private functions that are each called only once. "
    "If a helper doesn't simplify a complex expression or isn't part "
    "of a clear abstraction, inline it at the call site. Single-use "
    "helpers fragment control flow and force readers to jump around."
)

def _should_skip_name(name: str) -> bool:
    """Return True if the function name suggests it's a callback or special."""
    for prefix in _SKIP_PREFIXES:
        if name.startswith(prefix):
            return True
    return any(pattern in name for pattern in _CALLBACK_PATTERNS)

def _count_references(text: str, func_name: str) -> int:
    """Count references to func_name in the file text (excluding its definition)."""
    # Use word boundary to avoid partial matches.
    pattern = re.compile(r"(?<!\bdef\s)" + re.escape(func_name) + r"\b")
    matches = pattern.findall(text)
    return len(matches)

def _scan_python_file(text: str, path: Path) -> list[RiskHint]:
    """Detect single-use private helpers in one Python file."""
    functions = scan_python_functions(text)
    rel = path.as_posix()

    # Build a map of private function names and their line counts.
    private_functions: dict[str, int] = {}
    for func in functions:
        name = func["name"]
        if not name.startswith("_"):
            continue
        if _should_skip_name(name):
            continue
        if func["line_count"] < MIN_HELPER_LINES:
            continue
        private_functions[name] = func["line_count"]

    if not private_functions:
        return []

    # Count references (excluding the def line itself).
    single_use: list[str] = []
    for func_name in private_functions:
        ref_count = _count_references(text, func_name)
        # ref_count of 1 means the function is called exactly once
        # (the def line was excluded by the regex lookbehind).
        if ref_count == 1:
            single_use.append(func_name)

    if len(single_use) < FILE_THRESHOLD_MEDIUM:
        return []

    severity = "high" if len(single_use) >= FILE_THRESHOLD_HIGH else "medium"
    sample = ", ".join(f"`{n}`" for n in single_use[:5])
    return [
        RiskHint(
            file=rel,
            symbol="(file-level)",
            risk_type="design_smell",
            severity=severity,
            signals=[f"{len(single_use)} private functions called only once " f"({sample}) — consider inlining"],
            ai_instruction=AI_INSTRUCTION,
            review_lens=REVIEW_LENS,
        )
    ]

def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_single_use_helpers")

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
