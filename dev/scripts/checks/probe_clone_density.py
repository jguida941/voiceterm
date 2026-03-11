#!/usr/bin/env python3
"""Review probe: detect excessive .clone() usage in Rust production code.

Functions with many .clone() calls suggest ownership confusion — the author
is cloning to satisfy the borrow checker instead of restructuring ownership.
Arc::clone() is excluded (idiomatic for shared ownership).

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
scan_rust_functions = import_attr(
    "code_shape_function_policy", "scan_rust_functions"
)
strip_cfg_test_blocks = import_attr("rust_check_text_utils", "strip_cfg_test_blocks")

REPO_ROOT = Path(__file__).resolve().parents[3]
guard = GuardContext(REPO_ROOT)

TARGET_ROOTS = resolve_quality_scope_roots("rust_probe", repo_root=REPO_ROOT)

REVIEW_LENS = "ownership"

# Thresholds.
CLONE_MEDIUM = 5
CLONE_HIGH = 8

# Regex: .clone() calls.
CLONE_RE = re.compile(r"\.\s*clone\s*\(\s*\)")

# Regex: Arc::clone() — idiomatic, should be excluded.
ARC_CLONE_RE = re.compile(r"Arc\s*::\s*clone\s*\(")

# Regex: .to_string() — a form of cloning for string types.
TO_STRING_RE = re.compile(r"\.\s*to_string\s*\(\s*\)")

# Regex: .to_owned() — another clone variant.
TO_OWNED_RE = re.compile(r"\.\s*to_owned\s*\(\s*\)")

# Functions where cloning is expected (builder patterns, snapshot creation).
_CLONE_ALLOWLIST_PREFIXES = frozenset({
    "clone",       # Clone trait impl
    "snapshot",    # Snapshot creation functions
    "deep_copy",   # Explicit deep copy
    "duplicate",   # Explicit duplication
})

AI_INSTRUCTIONS = {
    "medium": (
        "This function has multiple .clone() calls suggesting ownership "
        "confusion. Consider restructuring to use references (&T), "
        "Cow<T> for conditional ownership, or passing owned values "
        "through the call chain instead of cloning at each step."
    ),
    "high": (
        "This function has excessive cloning indicating a fundamental "
        "ownership design issue. Restructure the data flow: pass "
        "references where possible, use Cow<T> for read-mostly/write-rarely "
        "patterns, or restructure the function to take ownership of its "
        "inputs instead of cloning them."
    ),
}
def _scan_rust_file(text: str, path: Path) -> list[RiskHint]:
    """Detect functions with excessive cloning in one Rust file."""
    hints: list[RiskHint] = []
    stripped = strip_cfg_test_blocks(text)
    functions = scan_rust_functions(stripped)
    lines = stripped.splitlines()
    rel = path.as_posix()

    for func in functions:
        func_name = func["name"]

        # Skip allowlisted function name prefixes.
        if any(func_name.startswith(p) for p in _CLONE_ALLOWLIST_PREFIXES):
            continue

        start = func["start_line"] - 1
        end = func["end_line"]
        body = "\n".join(lines[start:end])

        # Count clone variants, excluding Arc::clone.
        clone_count = len(CLONE_RE.findall(body))
        arc_clone_count = len(ARC_CLONE_RE.findall(body))
        to_string_count = len(TO_STRING_RE.findall(body))
        to_owned_count = len(TO_OWNED_RE.findall(body))

        # Non-Arc clones are the signal.
        effective_clones = clone_count - arc_clone_count
        if effective_clones < 0:
            effective_clones = 0

        # Total ownership-copying operations.
        total = effective_clones + to_string_count + to_owned_count

        if total < CLONE_MEDIUM:
            continue

        severity = "high" if total >= CLONE_HIGH else "medium"
        parts = []
        if effective_clones:
            parts.append(f"{effective_clones} .clone()")
        if to_string_count:
            parts.append(f"{to_string_count} .to_string()")
        if to_owned_count:
            parts.append(f"{to_owned_count} .to_owned()")
        if arc_clone_count:
            parts.append(f"{arc_clone_count} Arc::clone (excluded)")

        hints.append(
            RiskHint(
                file=rel,
                symbol=func_name,
                risk_type="ownership_smell",
                severity=severity,
                signals=[
                    f"{' + '.join(parts)} — {total} ownership-copying "
                    f"operations (consider references or Cow<T>)"
                ],
                ai_instruction=AI_INSTRUCTIONS[severity],
                review_lens=REVIEW_LENS,
            )
        )

    return hints


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_clone_density")

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
        if path.suffix != ".rs":
            continue
        if not is_under_target_roots(
            path, repo_root=REPO_ROOT, target_roots=TARGET_ROOTS
        ):
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
