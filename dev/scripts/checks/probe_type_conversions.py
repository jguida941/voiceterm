#!/usr/bin/env python3
"""Review probe: detect redundant type conversion chains in Rust code.

Patterns like `.as_str().to_string()` convert String -> &str -> String,
which is a round-trip that wastes allocation. Similarly `.as_ref().to_owned()`
converts T -> &T -> T. These indicate confused ownership — the author
doesn't understand when they have an owned vs borrowed value.

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

REVIEW_LENS = "ownership"

# Round-trip conversion patterns (each is a wasted allocation).
CONVERSION_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (
        re.compile(r"\.\s*as_str\s*\(\s*\)\s*\.\s*to_string\s*\(\s*\)"),
        ".as_str().to_string()",
        "String→&str→String round-trip. Use .clone() if you need a copy, " "or pass &str if the caller only reads.",
    ),
    (
        re.compile(r"\.\s*as_ref\s*\(\s*\)\s*\.\s*to_owned\s*\(\s*\)"),
        ".as_ref().to_owned()",
        "T→&T→T round-trip. Use .clone() or restructure ownership.",
    ),
    (
        re.compile(r"\.\s*to_string\s*\(\s*\)\s*\.\s*as_str\s*\(\s*\)"),
        ".to_string().as_str()",
        "Creates a temporary String just to get &str. " "Use the original &str directly.",
    ),
    (
        re.compile(r"\.\s*to_owned\s*\(\s*\)\s*\.\s*as_ref\s*\(\s*\)"),
        ".to_owned().as_ref()",
        "Creates an owned copy just to borrow it. " "Use the original reference directly.",
    ),
    (
        re.compile(r"\.\s*clone\s*\(\s*\)\s*\.\s*as_str\s*\(\s*\)"),
        ".clone().as_str()",
        "Clones a String just to borrow it as &str. " "Borrow the original instead.",
    ),
    (
        re.compile(r"\.\s*to_string\s*\(\s*\)\s*\.\s*into\s*\(\s*\)"),
        ".to_string().into()",
        "Double conversion — .to_string() already produces a String. " "Use .to_string() or .into() alone.",
    ),
]

AI_INSTRUCTION = (
    "This code has a redundant type conversion chain that allocates "
    "and immediately converts back. Simplify the ownership: use .clone() "
    "when you need an owned copy, pass references when you only read, "
    "or restructure to avoid the conversion entirely."
)


def _scan_rust_file(text: str, path: Path) -> list[RiskHint]:
    """Detect redundant type conversions in one Rust file."""
    hints: list[RiskHint] = []
    stripped = strip_cfg_test_blocks(text)
    functions = scan_rust_functions(stripped)
    lines = stripped.splitlines()
    rel = path.as_posix()

    for func in functions:
        start = func["start_line"] - 1
        end = func["end_line"]
        body = "\n".join(lines[start:end])

        signals: list[str] = []
        for pattern, label, explanation in CONVERSION_PATTERNS:
            matches = pattern.findall(body)
            if matches:
                signals.append(f"{len(matches)}x {label} — {explanation}")

        if signals:
            hints.append(
                RiskHint(
                    file=rel,
                    symbol=func["name"],
                    risk_type="ownership_smell",
                    severity="medium",
                    signals=signals,
                    ai_instruction=AI_INSTRUCTION,
                    review_lens=REVIEW_LENS,
                )
            )

    return hints


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_type_conversions")

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
