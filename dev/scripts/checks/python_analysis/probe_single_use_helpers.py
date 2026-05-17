"""Implementation for the single-use-helper review probe."""

from __future__ import annotations

from dataclasses import dataclass
import sys
from pathlib import Path

try:
    from check_bootstrap import (
        REPO_ROOT,
        import_attr,
        is_under_target_roots,
        resolve_quality_scope_roots,
    )
    from probe_support.bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        count_python_call_sites_by_symbol,
        emit_probe_report,
        load_current_text_by_path,
    )
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        import_attr,
        is_under_target_roots,
        resolve_quality_scope_roots,
    )
    from dev.scripts.checks.probe_support.bootstrap import (
        ProbeReport,
        RiskHint,
        build_probe_parser,
        count_python_call_sites_by_symbol,
        emit_probe_report,
        load_current_text_by_path,
    )

list_changed_paths_with_base_map = import_attr("git_change_paths", "list_changed_paths_with_base_map")
GuardContext = import_attr("rust_guard_common", "GuardContext")
is_review_probe_test_path = import_attr("probe_path_filters", "is_review_probe_test_path")
scan_python_functions = import_attr("code_shape_function_policy", "scan_python_functions")

guard = GuardContext(REPO_ROOT)

PYTHON_ROOTS = resolve_quality_scope_roots("python_probe", repo_root=REPO_ROOT)

REVIEW_LENS = "design_quality"
MIN_HELPER_LINES = 5
FILE_THRESHOLD_MEDIUM = 3
FILE_THRESHOLD_HIGH = 6

_SKIP_PREFIXES = frozenset(
    {
        "__",
        "_test_",
        "_fixture_",
        "_mock_",
    }
)

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
RELOCATION_AI_INSTRUCTION = (
    "A private single-use helper appears to have been moved into another file "
    "without reducing indirection. Do not satisfy this probe by relocating the "
    "helper; inline it or extract a real abstraction with multiple callers."
)


@dataclass(frozen=True, slots=True)
class HelperCandidate:
    """One private helper candidate tracked across the changed file set."""

    name: str
    line_count: int


def _should_skip_name(name: str) -> bool:
    """Return True if the function name suggests it's a callback or special."""
    for prefix in _SKIP_PREFIXES:
        if name.startswith(prefix):
            return True
    return any(pattern in name for pattern in _CALLBACK_PATTERNS)


def _helper_candidates(text: str) -> tuple[HelperCandidate, ...]:
    """Return private helper candidates from one file before reference counting."""
    functions = scan_python_functions(text)
    candidates: list[HelperCandidate] = []
    for func in functions:
        name = func["name"]
        if not name.startswith("_"):
            continue
        if _should_skip_name(name):
            continue
        if func["line_count"] < MIN_HELPER_LINES:
            continue
        candidates.append(HelperCandidate(name=name, line_count=int(func["line_count"])))
    return tuple(candidates)


def _single_use_helpers_by_file(
    text_by_path: dict[Path, str],
) -> dict[Path, tuple[HelperCandidate, ...]]:
    """Detect single-use helpers across the changed file set, not one file at a time."""
    candidates_by_file = {path: _helper_candidates(text) for path, text in text_by_path.items()}
    definition_count_by_name: dict[str, int] = {}
    for candidates in candidates_by_file.values():
        for candidate in candidates:
            definition_count_by_name[candidate.name] = definition_count_by_name.get(candidate.name, 0) + 1
    corpus_call_count_by_name = count_python_call_sites_by_symbol(
        {path.as_posix(): text for path, text in text_by_path.items()}
    )
    local_call_counts_by_path = {
        path: count_python_call_sites_by_symbol({path.as_posix(): text})
        for path, text in text_by_path.items()
    }

    single_use_by_file: dict[Path, tuple[HelperCandidate, ...]] = {}
    for path, candidates in candidates_by_file.items():
        single_use: list[HelperCandidate] = []
        for candidate in candidates:
            if definition_count_by_name[candidate.name] == 1:
                call_count = corpus_call_count_by_name.get(candidate.name, 0)
            else:
                call_count = local_call_counts_by_path[path].get(candidate.name, 0)
            if call_count == 1:
                single_use.append(candidate)
        if single_use:
            single_use_by_file[path] = tuple(single_use)
    return single_use_by_file


def _current_path_for_base(
    current_paths: tuple[Path, ...],
    base_path_by_current_path: dict[Path, Path],
    *,
    base_path: Path,
) -> Path | None:
    for current_path in current_paths:
        if base_path_by_current_path.get(current_path, current_path) == base_path:
            return current_path
    return None


def _collect_relocated_helpers(
    *,
    current_single_use: dict[Path, tuple[HelperCandidate, ...]],
    base_single_use: dict[Path, tuple[HelperCandidate, ...]],
    base_path_by_current_path: dict[Path, Path],
) -> dict[Path, tuple[str, ...]]:
    """Return moved single-use helpers keyed by their new file path."""
    current_paths = tuple(current_single_use)
    current_names_by_file = {
        path: {candidate.name for candidate in candidates}
        for path, candidates in current_single_use.items()
    }
    relocated_by_current_path: dict[Path, list[str]] = {}
    for base_path, base_candidates in base_single_use.items():
        current_same_path = _current_path_for_base(
            current_paths,
            base_path_by_current_path,
            base_path=base_path,
        )
        current_same_names = current_names_by_file.get(current_same_path, set()) if current_same_path else set()
        for candidate in base_candidates:
            if candidate.name in current_same_names:
                continue
            destinations = [
                path
                for path, names in current_names_by_file.items()
                if path != current_same_path and candidate.name in names
            ]
            if len(destinations) != 1:
                continue
            relocated_by_current_path.setdefault(destinations[0], []).append(
                f"`{candidate.name}` from `{base_path.as_posix()}`"
            )
    return {path: tuple(entries) for path, entries in relocated_by_current_path.items() if entries}


def _hint_for_file(
    *,
    path: Path,
    single_use: tuple[HelperCandidate, ...],
    relocated_entries: tuple[str, ...],
) -> RiskHint | None:
    regular_count = len(single_use)
    has_relocation = bool(relocated_entries)
    if regular_count < FILE_THRESHOLD_MEDIUM and not has_relocation:
        return None
    severity = "high" if regular_count >= FILE_THRESHOLD_HIGH or has_relocation else "medium"
    signals: list[str] = []
    if regular_count >= FILE_THRESHOLD_MEDIUM:
        sample = ", ".join(f"`{candidate.name}`" for candidate in single_use[:5])
        signals.append(
            f"{regular_count} private functions called only once ({sample}) — consider inlining"
        )
    if has_relocation:
        sample = ", ".join(relocated_entries[:3])
        signals.append(
            "single-use helper relocation detected ("
            + sample
            + ") — moving the helper did not remove the indirection"
        )
    return RiskHint(
        file=path.as_posix(),
        symbol="(file-level)",
        risk_type="design_smell",
        severity=severity,
        signals=signals,
        ai_instruction=RELOCATION_AI_INSTRUCTION if has_relocation else AI_INSTRUCTION,
        review_lens=REVIEW_LENS,
    )


def _scan_python_files(
    current_text_by_path: dict[Path, str],
    *,
    base_text_by_path: dict[Path, str],
    base_path_by_current_path: dict[Path, Path],
) -> list[RiskHint]:
    """Detect single-use helpers plus same-diff relocation across changed files."""
    current_single_use = _single_use_helpers_by_file(current_text_by_path)
    base_single_use = _single_use_helpers_by_file(base_text_by_path)
    relocated_by_current_path = _collect_relocated_helpers(
        current_single_use=current_single_use,
        base_single_use=base_single_use,
        base_path_by_current_path=base_path_by_current_path,
    )
    hints: list[RiskHint] = []
    for path in sorted(current_text_by_path):
        hint = _hint_for_file(
            path=path,
            single_use=current_single_use.get(path, ()),
            relocated_entries=relocated_by_current_path.get(path, ()),
        )
        if hint is not None:
            hints.append(hint)
    return hints


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    report = ProbeReport(command="probe_single_use_helpers")

    try:
        if args.since_ref:
            guard.validate_ref(args.since_ref)
            guard.validate_ref(args.head_ref)
        changed_paths, base_map = list_changed_paths_with_base_map(
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
    current_text_by_path = {
        Path(relative): text
        for relative, text in load_current_text_by_path(
            changed_paths=changed_paths,
            since_ref=args.since_ref,
            head_ref=args.head_ref,
            read_text_from_ref=guard.read_text_from_ref,
            read_text_from_worktree=guard.read_text_from_worktree,
            include_path=lambda path: (
                path.suffix == ".py"
                and is_under_target_roots(path, repo_root=REPO_ROOT, target_roots=PYTHON_ROOTS)
                and not is_review_probe_test_path(path)
            ),
        ).items()
    }
    base_text_by_path: dict[Path, str] = {}
    base_path_by_current_path: dict[Path, Path] = {}

    for path in current_text_by_path:
        report.files_scanned += 1
        base_path = base_map.get(path, path)
        base_path_by_current_path[path] = base_path
        base_text = (
            guard.read_text_from_ref(base_path, args.since_ref)
            if args.since_ref
            else guard.read_text_from_ref(base_path, "HEAD")
        )
        if base_text is not None:
            base_text_by_path.setdefault(base_path, base_text)

    hints = _scan_python_files(
        current_text_by_path,
        base_text_by_path=base_text_by_path,
        base_path_by_current_path=base_path_by_current_path,
    )
    for hint in hints:
        files_with_hints.add(hint.file)
    report.risk_hints.extend(hints)

    report.files_with_hints = len(files_with_hints)
    return emit_probe_report(report, output_format=args.format)


__all__ = [
    "AI_INSTRUCTION",
    "FILE_THRESHOLD_HIGH",
    "FILE_THRESHOLD_MEDIUM",
    "HelperCandidate",
    "MIN_HELPER_LINES",
    "RELOCATION_AI_INSTRUCTION",
    "_collect_relocated_helpers",
    "_current_path_for_base",
    "_helper_candidates",
    "_hint_for_file",
    "_scan_python_files",
    "_should_skip_name",
    "_single_use_helpers_by_file",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
