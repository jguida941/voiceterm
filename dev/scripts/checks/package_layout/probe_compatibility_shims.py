"""Review probe: detect stale compatibility-shim debt.

Targets thin wrapper files that stay structurally valid but start hiding
migration debt:

- missing canonical shim metadata (`shim-owner`, `shim-reason`,
  `shim-expiry`, `shim-target`)
- invalid or expired shim expiry dates
- shim targets that no longer resolve to a live repo path
- shim-heavy roots and crowded namespace families that are not converging

This probe always exits 0. It emits structured risk hints for review.
"""

from __future__ import annotations

from pathlib import Path
import sys

if __package__:
    from .bootstrap import (
        REPO_ROOT,
        STANDARD_SHIM_METADATA_FIELDS,
        import_attr,
        is_adoption_scan,
    )
    from .probe_compatibility_hints import AI_INSTRUCTIONS, REVIEW_LENS
    from .probe_compatibility_rules import (
        DEFAULT_FAMILY_SHIM_BUDGET,
        DEFAULT_ROOT_SHIM_BUDGET,
        DEFAULT_SHIM_MAX_NONBLANK_LINES,
        PublicShimContract,
        ShimFamilyRule,
        ShimFinding,
        ShimProbePolicy,
        ShimRootRule,
        load_shim_probe_policy,
        load_shim_probe_rules,
    )
    from .probe_compatibility_scan import (
        build_family_hints,
        build_root_hints,
        family_rule_triggered,
        root_rule_triggered,
    )
else:  # pragma: no cover - standalone script fallback
    from bootstrap import (
        REPO_ROOT,
        STANDARD_SHIM_METADATA_FIELDS,
        import_attr,
        is_adoption_scan,
    )
    from probe_compatibility_hints import AI_INSTRUCTIONS, REVIEW_LENS
    from probe_compatibility_rules import (
        DEFAULT_FAMILY_SHIM_BUDGET,
        DEFAULT_ROOT_SHIM_BUDGET,
        DEFAULT_SHIM_MAX_NONBLANK_LINES,
        PublicShimContract,
        ShimFamilyRule,
        ShimFinding,
        ShimProbePolicy,
        ShimRootRule,
        load_shim_probe_policy,
        load_shim_probe_rules,
    )
    from probe_compatibility_scan import (
        build_family_hints,
        build_root_hints,
        family_rule_triggered,
        root_rule_triggered,
    )

ProbeReport = import_attr("probe_bootstrap", "ProbeReport")
build_probe_parser = import_attr("probe_bootstrap", "build_probe_parser")
emit_probe_report = import_attr("probe_bootstrap", "emit_probe_report")

list_changed_paths_with_base_map = import_attr("git_change_paths", "list_changed_paths_with_base_map")
GuardContext = import_attr("rust_guard_common", "GuardContext")
guard = GuardContext(REPO_ROOT)


def build_report(
    *,
    repo_root: Path,
    candidate_paths: list[Path],
    current_text_by_path: dict[str, str | None],
    mode: str,
    policy: ShimProbePolicy | None = None,
) -> ProbeReport:
    del current_text_by_path
    report = ProbeReport(command="probe_compatibility_shims")
    report.mode = mode
    active_policy = policy if policy is not None else load_shim_probe_policy(repo_root)
    active_root_rules = active_policy.root_rules
    active_family_rules = active_policy.family_rules
    active_public_contracts = active_policy.public_contracts
    active_usage_scan_exclude_roots = active_policy.usage_scan_exclude_roots
    adoption_scan = mode == "adoption-scan"
    scanned_files: set[str] = set()
    files_with_hints: set[str] = set()

    for rule in active_root_rules:
        if not root_rule_triggered(
            rule,
            candidate_paths=candidate_paths,
            adoption_scan=adoption_scan,
        ):
            continue
        hints = build_root_hints(
            repo_root=repo_root,
            rule=rule,
            scanned_files=scanned_files,
            public_contracts=active_public_contracts,
            usage_scan_exclude_roots=active_usage_scan_exclude_roots,
        )
        report.risk_hints.extend(hints)
        files_with_hints.update(hint.file for hint in hints)

    for rule in active_family_rules:
        if not family_rule_triggered(
            rule,
            candidate_paths=candidate_paths,
            adoption_scan=adoption_scan,
        ):
            continue
        hints = build_family_hints(
            repo_root=repo_root,
            rule=rule,
            scanned_files=scanned_files,
            public_contracts=active_public_contracts,
        )
        report.risk_hints.extend(hints)
        files_with_hints.update(hint.file for hint in hints)

    report.files_scanned = len(scanned_files)
    report.files_with_hints = len(files_with_hints)
    return report


def main() -> int:
    args = build_probe_parser(__doc__ or "").parse_args()
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
        report = ProbeReport(command="probe_compatibility_shims")
        report.mode = (
            "adoption-scan"
            if is_adoption_scan(since_ref=args.since_ref, head_ref=args.head_ref)
            else ("commit-range" if args.since_ref else "working-tree")
        )
        return emit_probe_report(report, output_format=args.format)

    current_text_by_path: dict[str, str | None] = {}
    for path in changed_paths:
        if path.suffix != ".py":
            continue
        relative = path.as_posix()
        text = (
            guard.read_text_from_ref(path, args.head_ref)
            if args.since_ref
            else guard.read_text_from_worktree(path)
        )
        current_text_by_path[relative] = text

    mode = (
        "adoption-scan"
        if is_adoption_scan(since_ref=args.since_ref, head_ref=args.head_ref)
        else ("commit-range" if args.since_ref else "working-tree")
    )
    report = build_report(
        repo_root=REPO_ROOT,
        candidate_paths=changed_paths,
        current_text_by_path=current_text_by_path,
        mode=mode,
    )
    report.since_ref = args.since_ref
    report.head_ref = args.head_ref
    return emit_probe_report(report, output_format=args.format)


__all__ = [
    "AI_INSTRUCTIONS",
    "DEFAULT_FAMILY_SHIM_BUDGET",
    "DEFAULT_ROOT_SHIM_BUDGET",
    "DEFAULT_SHIM_MAX_NONBLANK_LINES",
    "PublicShimContract",
    "REVIEW_LENS",
    "STANDARD_SHIM_METADATA_FIELDS",
    "ShimFamilyRule",
    "ShimFinding",
    "ShimProbePolicy",
    "ShimRootRule",
    "build_report",
    "load_shim_probe_policy",
    "load_shim_probe_rules",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
