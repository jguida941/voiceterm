#!/usr/bin/env python3
"""Review probe: detect Rust functions accepting 3+ &mut parameters.

Functions taking many mutable references obscure which parameters are
modified, making it hard for callers to reason about side effects.
The fix is to bundle related mutable state into a context struct.

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

try:
    if __package__:
        from .common import extract_rust_signature
    else:  # pragma: no cover
        from dev.scripts.checks.code_shape_probes.common import extract_rust_signature
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.code_shape_probes.common import extract_rust_signature

list_changed_paths_with_base_map = import_attr("git_change_paths", "list_changed_paths_with_base_map")
GuardContext = import_attr("rust_guard_common", "GuardContext")
is_review_probe_test_path = import_attr("probe_path_filters", "is_review_probe_test_path")
scan_rust_functions = import_attr("code_shape_function_policy", "scan_rust_functions")
strip_cfg_test_blocks = import_attr("rust_check_text_utils", "strip_cfg_test_blocks")

guard = GuardContext(REPO_ROOT)

TARGET_ROOTS = resolve_quality_scope_roots("rust_probe", repo_root=REPO_ROOT)

REVIEW_LENS = "ownership"

# Thresholds.
MUT_PARAM_MEDIUM = 3
MUT_PARAM_HIGH = 4

# Regex: &mut patterns in function signatures.
MUT_REF_RE = re.compile(r"&\s*mut\s+")

# Regex: &mut self — excluded from the count.
MUT_SELF_RE = re.compile(r"&\s*mut\s+self\b")

AI_INSTRUCTIONS = {
    "medium": (
        "This function takes {count} mutable references. Callers can't see "
        "which parameter gets modified. Aggregate related mutable state "
        "into a context struct so the mutation surface is clear."
    ),
    "high": (
        "This function takes {count} mutable references — too many for "
        "callers to reason about. Create a context struct that bundles "
        "the related mutable state (e.g., `struct Context {{ state: &mut "
        "State, timers: &mut Timers }}`)."
    ),
}

def _scan_rust_file(text: str, path: Path) -> list[RiskHint]:
    """Detect functions with excessive &mut parameters in one Rust file."""
    hints: list[RiskHint] = []
    stripped = strip_cfg_test_blocks(text)
    functions = scan_rust_functions(stripped)
    lines = stripped.splitlines()
    rel = path.as_posix()

    for func in functions:
        sig = extract_rust_signature(lines, func)

        # Count all &mut occurrences, then subtract &mut self.
        all_mut = len(MUT_REF_RE.findall(sig))
        self_mut = len(MUT_SELF_RE.findall(sig))
        count = all_mut - self_mut

        if count < MUT_PARAM_MEDIUM:
            continue

        severity = "high" if count >= MUT_PARAM_HIGH else "medium"
        hints.append(
            RiskHint(
                file=rel,
                symbol=func["name"],
                risk_type="ownership_smell",
                severity=severity,
                signals=[
                    f"{count} &mut parameters (excluding &mut self) — "
                    f"bundle related mutable state into a context struct"
                ],
                ai_instruction=AI_INSTRUCTIONS[severity].format(count=count),
                review_lens=REVIEW_LENS,
            )
        )

    return hints


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_mutable_parameter_density")

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
