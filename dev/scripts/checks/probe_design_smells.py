#!/usr/bin/env python3
"""Review probe: detect design-quality smells in Python source files.

Targets AI-generated anti-patterns such as excessive getattr() usage
(duck-typing instead of typed models), untyped ``object`` parameters
with attribute access, and duplicated private format helpers that
should be extracted to a shared presenter.

This probe always exits 0. It emits structured risk hints for AI
review instead of blocking CI.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
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

TARGET_ROOTS = resolve_quality_scope_roots("python_probe", repo_root=REPO_ROOT)

REVIEW_LENS = "design_quality"

# Thresholds.
GETATTR_DENSITY_MEDIUM = 4
GETATTR_DENSITY_HIGH = 8
FORMAT_HELPER_THRESHOLD = 3
MIN_FUNCTION_LINES = 4

# Receivers where getattr() is expected (argparse Namespace, etc.).
GETATTR_RECEIVER_ALLOWLIST = frozenset({"args", "self", "cls"})

# Regex patterns.
GETATTR_RE = re.compile(r"getattr\s*\(\s*(\w+)\s*,\s*[\"']")
OBJECT_PARAM_RE = re.compile(r"(?:^|\s)(\w+)\s*:\s*object(?:\s*\||\s*[,)])")
FORMAT_HELPER_RE = re.compile(r"^def\s+(_fmt_\w+|_format_\w+)\s*\(", re.MULTILINE)

AI_INSTRUCTIONS = {
    "getattr_density": (
        "This function accesses an object via getattr() many times "
        "instead of using typed attribute access. Create a dataclass "
        "or NamedTuple for the object, then replace getattr() calls "
        "with direct attribute access for type safety and readability."
    ),
    "untyped_object_param": (
        "This function declares a parameter as 'object' but accesses "
        "specific attributes via getattr(). Replace the 'object' type "
        "hint with a concrete typed class (dataclass, Protocol, or "
        "TypedDict) so attribute access is checked at type-check time."
    ),
    "format_helper_sprawl": (
        "This file contains multiple private format helper functions. "
        "If similar helpers exist in other files, extract them to a "
        "shared presenter or formatter module to prevent drift."
    ),
}

def _count_getattr_by_receiver(body: str) -> Counter:
    """Count getattr() calls grouped by receiver variable name.

    Receivers in the allowlist (e.g. ``args`` for argparse.Namespace)
    are excluded because getattr() is idiomatic there.
    """
    return Counter(m.group(1) for m in GETATTR_RE.finditer(body) if m.group(1) not in GETATTR_RECEIVER_ALLOWLIST)

def _find_object_params(def_line: str) -> set[str]:
    """Return parameter names annotated as `: object` on a def line."""
    return {m.group(1) for m in OBJECT_PARAM_RE.finditer(def_line)}

def _getattr_density_signal(body: str) -> tuple[list[str], str | None, Counter]:
    signals: list[str] = []
    signal_key: str | None = None
    receiver_counts = _count_getattr_by_receiver(body)
    top_receiver = receiver_counts.most_common(1)
    if not top_receiver:
        return signals, signal_key, receiver_counts
    receiver, count = top_receiver[0]
    if count >= GETATTR_DENSITY_HIGH:
        signals.append(f"{count} getattr() calls on '{receiver}' (replace with typed model)")
        signal_key = "getattr_density"
    elif count >= GETATTR_DENSITY_MEDIUM:
        signals.append(f"{count} getattr() calls on '{receiver}' (consider typed model)")
        signal_key = "getattr_density"
    return signals, signal_key, receiver_counts

def _object_param_signal(def_line: str, body: str) -> tuple[list[str], str | None]:
    for param in _find_object_params(def_line):
        param_getattr_count = sum(1 for match in GETATTR_RE.finditer(body) if match.group(1) == param)
        if param_getattr_count >= 2:
            return (
                [f"parameter '{param}: object' accessed via getattr() {param_getattr_count} times"],
                "untyped_object_param",
            )
    return [], None

def _scan_function_smells(text: str, path: Path) -> list[RiskHint]:
    """Scan one Python file for per-function design smells."""
    hints: list[RiskHint] = []
    functions = scan_python_functions(text)
    lines = text.splitlines()
    rel_path = path.as_posix()

    for func in functions:
        if func["line_count"] < MIN_FUNCTION_LINES:
            continue

        start = func["start_line"] - 1
        end = func["end_line"]
        func_name = func["name"]
        def_line = lines[start] if start < len(lines) else ""
        body_lines = lines[start + 1 : end]
        body = "\n".join(body_lines)

        signals, signal_key, receiver_counts = _getattr_density_signal(body)
        if not signal_key:
            signals, signal_key = _object_param_signal(def_line, body)

        if signals:
            severity = (
                "high" if receiver_counts and receiver_counts.most_common(1)[0][1] >= GETATTR_DENSITY_HIGH else "medium"
            )
            ai_instruction = AI_INSTRUCTIONS.get(signal_key or "", AI_INSTRUCTIONS["getattr_density"])
            hints.append(
                RiskHint(
                    file=rel_path,
                    symbol=func_name,
                    risk_type="design_smell",
                    severity=severity,
                    signals=signals,
                    ai_instruction=ai_instruction,
                    review_lens=REVIEW_LENS,
                )
            )

    return hints

def _scan_file_level_smells(text: str, path: Path) -> list[RiskHint]:
    """Scan for file-level design smells (format helper sprawl)."""
    hints: list[RiskHint] = []
    helper_matches = FORMAT_HELPER_RE.findall(text)
    if len(helper_matches) >= FORMAT_HELPER_THRESHOLD:
        helper_names = ", ".join(helper_matches[:5])
        hints.append(
            RiskHint(
                file=path.as_posix(),
                symbol="(file-level)",
                risk_type="design_smell",
                severity="low",
                signals=[
                    f"{len(helper_matches)} private format helpers " f"({helper_names}) — consider shared presenter"
                ],
                ai_instruction=AI_INSTRUCTIONS["format_helper_sprawl"],
                review_lens=REVIEW_LENS,
            )
        )
    return hints

def _should_scan_path(path: Path) -> bool:
    if path.suffix != ".py":
        return False
    if not is_under_target_roots(path, repo_root=REPO_ROOT, target_roots=TARGET_ROOTS):
        return False
    return not is_review_probe_test_path(path)

def _load_probe_text(path: Path, *, since_ref: str | None, head_ref: str) -> str | None:
    if since_ref:
        return guard.read_text_from_ref(path, head_ref)
    return guard.read_text_from_worktree(path)

def _extend_report_for_path(report: ProbeReport, path: Path, text: str, files_with_hints: set[str]) -> None:
    func_hints = _scan_function_smells(text, path)
    file_hints = _scan_file_level_smells(text, path)
    all_hints = func_hints + file_hints
    if not all_hints:
        return
    files_with_hints.add(path.as_posix())
    report.risk_hints.extend(all_hints)

def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_design_smells")

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
        if not _should_scan_path(path):
            continue

        report.files_scanned += 1
        text = _load_probe_text(path, since_ref=args.since_ref, head_ref=args.head_ref)
        if text is None:
            continue
        _extend_report_for_path(report, path, text, files_with_hints)

    report.files_with_hints = len(files_with_hints)
    return emit_probe_report(report, output_format=args.format)

if __name__ == "__main__":
    sys.exit(main())
