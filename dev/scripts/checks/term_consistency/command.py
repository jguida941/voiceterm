#!/usr/bin/env python3
"""Review probe: detect legacy or mixed terminology in repo-owned surfaces.

Flags changed files that keep old public words after a canonical rename, or
mix multiple terms for the same concept inside one subsystem. This probe stays
advisory so repos can calibrate vocabulary rules before promoting any of them
to a hard naming-contract guard.
"""

from __future__ import annotations

from pathlib import Path
import sys

try:
    from check_bootstrap import REPO_ROOT, import_attr
    from probe_bootstrap import ProbeReport, build_probe_parser, emit_probe_report
except ModuleNotFoundError:  # pragma: no cover
    from dev.scripts.checks.check_bootstrap import REPO_ROOT, import_attr
    from dev.scripts.checks.probe_bootstrap import (
        ProbeReport,
        build_probe_parser,
        emit_probe_report,
    )

try:
    from dev.scripts.devctl.quality_scan_mode import is_adoption_scan
except ModuleNotFoundError:  # pragma: no cover
    repo_root_str = str(Path(__file__).resolve().parents[4])
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
    from dev.scripts.devctl.quality_scan_mode import is_adoption_scan

if __package__:
    from .analysis import (
        TEXT_SUFFIXES,
        analyze_text,
        build_hint,
        matches_rule_path,
        normalize_path,
    )
    from .config import load_probe_config
else:  # pragma: no cover - direct module loading in tests
    from analysis import TEXT_SUFFIXES, analyze_text, build_hint, matches_rule_path, normalize_path
    from config import load_probe_config

list_changed_paths_with_base_map = import_attr("git_change_paths", "list_changed_paths_with_base_map")
GuardContext = import_attr("rust_guard_common", "GuardContext")

guard = GuardContext(REPO_ROOT)


def build_report(
    *,
    repo_root: Path,
    candidate_paths: list[Path],
    base_text_by_path: dict[str, str | None],
    current_text_by_path: dict[str, str | None],
    mode: str,
) -> ProbeReport:
    config = load_probe_config(repo_root)
    report = ProbeReport(command="probe_term_consistency")
    report.mode = mode
    if not config.rules:
        return report

    files_with_hints: set[str] = set()
    for path in candidate_paths:
        relative = normalize_path(path, repo_root)
        if Path(relative).suffix not in TEXT_SUFFIXES:
            continue
        if not any(matches_rule_path(relative, config, rule) for rule in config.rules):
            continue
        current_text = current_text_by_path.get(relative)
        if current_text is None:
            continue
        report.files_scanned += 1
        base_text = base_text_by_path.get(relative)
        for rule in config.rules:
            if not matches_rule_path(relative, config, rule):
                continue
            hint = build_hint(
                path=relative,
                rule=rule,
                before_state=analyze_text(base_text, rule),
                after_state=analyze_text(current_text, rule),
                mode=mode,
            )
            if hint is None:
                continue
            files_with_hints.add(relative)
            report.risk_hints.append(hint)

    report.files_with_hints = len(files_with_hints)
    return report


def _load_text_maps(
    *,
    changed_paths: list[Path],
    base_map: dict[Path, Path],
    since_ref: str | None,
    head_ref: str,
) -> tuple[dict[str, str | None], dict[str, str | None]]:
    base_text_by_path: dict[str, str | None] = {}
    current_text_by_path: dict[str, str | None] = {}
    for path in changed_paths:
        if path.suffix not in TEXT_SUFFIXES:
            continue
        relative = path.as_posix()
        base_path = base_map.get(path, path)
        if since_ref:
            base_text = guard.read_text_from_ref(base_path, since_ref)
            current_text = guard.read_text_from_ref(path, head_ref)
        else:
            base_text = guard.read_text_from_ref(base_path, "HEAD")
            current_text = guard.read_text_from_worktree(path)
        base_text_by_path[relative] = base_text
        current_text_by_path[relative] = current_text
    return base_text_by_path, current_text_by_path


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
    mode = (
        "adoption-scan"
        if is_adoption_scan(since_ref=args.since_ref, head_ref=args.head_ref)
        else ("commit-range" if args.since_ref else "working-tree")
    )
    try:
        if args.since_ref and mode != "adoption-scan":
            guard.validate_ref(args.since_ref)
            guard.validate_ref(args.head_ref)
        changed_paths, base_map = list_changed_paths_with_base_map(
            guard.run_git,
            args.since_ref,
            args.head_ref,
        )
    except RuntimeError:
        report = ProbeReport(command="probe_term_consistency")
        report.mode = mode
        return emit_probe_report(report, output_format=args.format)

    base_text_by_path, current_text_by_path = _load_text_maps(
        changed_paths=changed_paths,
        base_map=base_map,
        since_ref=args.since_ref,
        head_ref=args.head_ref,
    )
    report = build_report(
        repo_root=REPO_ROOT,
        candidate_paths=changed_paths,
        base_text_by_path=base_text_by_path,
        current_text_by_path=current_text_by_path,
        mode=mode,
    )
    report.since_ref = args.since_ref
    report.head_ref = args.head_ref
    return emit_probe_report(report, output_format=args.format)


if __name__ == "__main__":
    sys.exit(main())
