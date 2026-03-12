#!/usr/bin/env python3
"""Review probe: detect vague error messages in Rust code.

AI agents often write `bail!("something failed")` or `anyhow!("invalid input")`
without including any runtime context — the variable values that would help
debug the failure in production. When the error fires, you see the static
message but have no idea what the actual inputs or state were.

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
VAGUE_MEDIUM = 2
VAGUE_HIGH = 4

# Regex: bail!("literal string without format args")
# Matches bail!("...") where the string does NOT contain { } format placeholders.
BAIL_VAGUE_RE = re.compile(r"""bail!\s*\(\s*"([^"]*?)"\s*\)""")

# Regex: anyhow!("literal string without format args")
ANYHOW_VAGUE_RE = re.compile(r"""anyhow!\s*\(\s*"([^"]*?)"\s*\)""")

# Regex: .context("literal without format args")
CONTEXT_VAGUE_RE = re.compile(r"""\.context\s*\(\s*"([^"]*?)"\s*\)""")

# Regex: .with_context(|| "literal") — also vague if no format args.
WITH_CONTEXT_VAGUE_RE = re.compile(r"""\.with_context\s*\(\s*\|\s*\|\s*"([^"]*?)"\s*\)""")

# Check if a string contains format placeholders like {var} or {}.
FORMAT_PLACEHOLDER_RE = re.compile(r"\{[^}]*\}")

# Short messages that are likely sufficient without context (1-2 words).
_SHORT_MESSAGE_MAX = 15

AI_INSTRUCTIONS = {
    "medium": (
        "This function has error messages without runtime context. Add "
        "format arguments with variable values so the error is debuggable: "
        'bail!("failed to open config: {path:?}") instead of '
        'bail!("failed to open config").'
    ),
    "high": (
        "This function has many vague error messages that will be nearly "
        "impossible to debug in production. Each bail!/anyhow! should include "
        "the relevant variable values as format arguments. Consider using "
        ".with_context(|| format!(...)) for chained errors."
    ),
}


def _is_vague_message(message: str) -> bool:
    """Return True if the error message lacks runtime context."""
    # Has format placeholders — not vague.
    if FORMAT_PLACEHOLDER_RE.search(message):
        return False
    # Very short messages (e.g., "timeout") are acceptable.
    return not len(message) <= _SHORT_MESSAGE_MAX


def _scan_rust_file(text: str, path: Path) -> list[RiskHint]:
    """Detect vague error messages in one Rust file."""
    hints: list[RiskHint] = []
    stripped = strip_cfg_test_blocks(text)
    functions = scan_rust_functions(stripped)
    lines = stripped.splitlines()
    rel = path.as_posix()

    for func in functions:
        func_name = func["name"]
        start = func["start_line"] - 1
        end = func["end_line"]
        body = "\n".join(lines[start:end])

        vague_messages: list[str] = []

        # Check bail!() calls.
        for match in BAIL_VAGUE_RE.finditer(body):
            msg = match.group(1)
            if _is_vague_message(msg):
                vague_messages.append(f'bail!("{msg}")')

        # Check anyhow!() calls.
        for match in ANYHOW_VAGUE_RE.finditer(body):
            msg = match.group(1)
            if _is_vague_message(msg):
                vague_messages.append(f'anyhow!("{msg}")')

        # Check .context() calls.
        for match in CONTEXT_VAGUE_RE.finditer(body):
            msg = match.group(1)
            if _is_vague_message(msg):
                vague_messages.append(f'.context("{msg}")')

        if len(vague_messages) < VAGUE_MEDIUM:
            continue

        severity = "high" if len(vague_messages) >= VAGUE_HIGH else "medium"
        sample = "; ".join(vague_messages[:3])
        hints.append(
            RiskHint(
                file=rel,
                symbol=func_name,
                risk_type="error_handling",
                severity=severity,
                signals=[
                    f"{len(vague_messages)} error messages without runtime context "
                    f"({sample}) — add {{variable}} format args for debuggability"
                ],
                ai_instruction=AI_INSTRUCTIONS[severity],
                review_lens=REVIEW_LENS,
            )
        )

    return hints


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_vague_errors")

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
