"""Scan helpers for the compatibility-shim review probe."""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path

if __package__:
    from .bootstrap import detect_compatibility_shim, import_attr
    from .probe_compatibility_hints import (
        build_file_level_hints,
        build_heavy_family_hint,
        build_heavy_root_hint,
        build_missing_metadata_hint,
        build_temporary_repo_callers_hint,
        build_temporary_unused_hint,
    )
    from .probe_compatibility_rules import (
        PublicShimContract,
        ShimFamilyRule,
        ShimFinding,
        ShimRootRule,
    )
    from .probe_compatibility_usage import classify_shim_lifecycle, match_public_contract
else:  # pragma: no cover - standalone script fallback
    from bootstrap import detect_compatibility_shim, import_attr
    from probe_compatibility_hints import (
        build_file_level_hints,
        build_heavy_family_hint,
        build_heavy_root_hint,
        build_missing_metadata_hint,
        build_temporary_repo_callers_hint,
        build_temporary_unused_hint,
    )
    from probe_compatibility_rules import (
        PublicShimContract,
        ShimFamilyRule,
        ShimFinding,
        ShimRootRule,
    )
    from probe_compatibility_usage import classify_shim_lifecycle, match_public_contract

RiskHint = import_attr("probe_bootstrap", "RiskHint")
is_review_probe_test_path = import_attr(
    "probe_path_filters",
    "is_review_probe_test_path",
)


def iter_root_candidates(repo_root: Path, rule: ShimRootRule) -> list[Path]:
    """Enumerate non-test shim candidates for one root rule."""
    root_abs = repo_root / rule.root
    if not root_abs.is_dir():
        return []
    paths = [
        child
        for child in root_abs.iterdir()
        if child.is_file() and any(fnmatch(child.name, pattern) for pattern in rule.include_globs)
    ]
    return sorted(
        path
        for path in paths
        if not is_review_probe_test_path(path.relative_to(repo_root))
    )


def iter_family_candidates(repo_root: Path, rule: ShimFamilyRule) -> list[Path]:
    """Enumerate non-test shim candidates for one family rule."""
    root_abs = repo_root / rule.root
    if not root_abs.is_dir():
        return []
    return sorted(
        path
        for path in root_abs.glob(f"{rule.flat_prefix}*.py")
        if path.is_file()
        and not is_review_probe_test_path(path.relative_to(repo_root))
    )


def _validate_root_shim(
    repo_root: Path,
    path: Path,
    *,
    rule: ShimRootRule,
) -> ShimFinding | None:
    validation = detect_compatibility_shim(
        path,
        namespace_subdir=rule.namespace_subdir,
        shim_contains_all=rule.shim_contains_all,
        shim_max_nonblank_lines=rule.shim_max_nonblank_lines,
        shim_required_metadata_fields=rule.required_metadata_fields,
    )
    if not validation.is_valid and not validation.missing_metadata_fields:
        return None
    return ShimFinding(
        relative_path=path.relative_to(repo_root),
        metadata=validation.metadata,
        missing_metadata_fields=validation.missing_metadata_fields,
        is_valid=validation.is_valid,
    )


def _validate_family_shim(
    repo_root: Path,
    path: Path,
    *,
    rule: ShimFamilyRule,
) -> ShimFinding | None:
    validation = detect_compatibility_shim(
        path,
        namespace_subdir=rule.namespace_subdir,
        shim_max_nonblank_lines=rule.shim_max_nonblank_lines,
        shim_required_metadata_fields=rule.required_metadata_fields,
    )
    if not validation.is_valid and not validation.missing_metadata_fields:
        return None
    return ShimFinding(
        relative_path=path.relative_to(repo_root),
        metadata=validation.metadata,
        missing_metadata_fields=validation.missing_metadata_fields,
        is_valid=validation.is_valid,
    )


def root_rule_triggered(
    rule: ShimRootRule,
    *,
    candidate_paths: list[Path],
    adoption_scan: bool,
) -> bool:
    """Return whether one root rule should run for the current change set."""
    if adoption_scan:
        return True
    return any(
        path.parent == rule.root
        and any(fnmatch(path.name, pattern) for pattern in rule.include_globs)
        for path in candidate_paths
    )


def family_rule_triggered(
    rule: ShimFamilyRule,
    *,
    candidate_paths: list[Path],
    adoption_scan: bool,
) -> bool:
    """Return whether one family rule should run for the current change set."""
    if adoption_scan:
        return True
    return any(
        path.parent == rule.root
        and path.name.startswith(rule.flat_prefix)
        and path.suffix == ".py"
        for path in candidate_paths
    )


def build_root_hints(
    *,
    repo_root: Path,
    rule: ShimRootRule,
    scanned_files: set[str],
    public_contracts: tuple[PublicShimContract, ...],
    usage_scan_exclude_roots: tuple[Path, ...],
) -> list[RiskHint]:
    """Build root-level hints and update the scanned-file set."""
    findings = [
        finding
        for path in iter_root_candidates(repo_root, rule)
        for finding in (_validate_root_shim(repo_root, path, rule=rule),)
        if finding is not None
    ]
    scanned_files.update(finding.relative_path.as_posix() for finding in findings)
    hints: list[RiskHint] = []
    missing_metadata = [
        finding for finding in findings if finding.missing_metadata_fields
    ]
    valid_findings = [finding for finding in findings if finding.is_valid]
    if missing_metadata:
        hints.append(build_missing_metadata_hint(root=rule.root, findings=missing_metadata))
    lifecycle = classify_shim_lifecycle(
        repo_root,
        valid_findings,
        public_contracts=public_contracts,
        usage_scan_exclude_roots=usage_scan_exclude_roots,
    )
    public_shim_count = sum(1 for item in lifecycle if item.is_public)
    temporary_with_refs = [
        item for item in lifecycle if not item.is_public and item.has_repo_references
    ]
    temporary_unused = [
        item for item in lifecycle if not item.is_public and not item.has_repo_references
    ]
    temporary_findings = [item.finding for item in lifecycle if not item.is_public]
    if temporary_with_refs:
        hints.append(
            build_temporary_repo_callers_hint(
                root=rule.root,
                lifecycles=temporary_with_refs,
            )
        )
    if temporary_unused:
        hints.append(
            build_temporary_unused_hint(
                root=rule.root,
                lifecycles=temporary_unused,
            )
        )
    if temporary_findings and len(temporary_findings) > rule.max_shims:
        hints.append(
            build_heavy_root_hint(
                rule=rule,
                valid_findings=temporary_findings,
                public_shim_count=public_shim_count,
            )
        )
    for finding in valid_findings:
        hints.extend(build_file_level_hints(repo_root, finding))
    return hints


def build_family_hints(
    *,
    repo_root: Path,
    rule: ShimFamilyRule,
    scanned_files: set[str],
    public_contracts: tuple[PublicShimContract, ...],
) -> list[RiskHint]:
    """Build family-level hints and update the scanned-file set."""
    findings = [
        finding
        for path in iter_family_candidates(repo_root, rule)
        for finding in (_validate_family_shim(repo_root, path, rule=rule),)
        if finding is not None
    ]
    scanned_files.update(finding.relative_path.as_posix() for finding in findings)
    valid_findings = [finding for finding in findings if finding.is_valid]
    hints: list[RiskHint] = []
    temporary_findings = [
        finding
        for finding in valid_findings
        if match_public_contract(finding.relative_path, public_contracts) is None
    ]
    public_shim_count = len(valid_findings) - len(temporary_findings)
    if temporary_findings and len(temporary_findings) > rule.max_shims:
        hints.append(
            build_heavy_family_hint(
                rule=rule,
                valid_findings=temporary_findings,
                public_shim_count=public_shim_count,
            )
        )
    for finding in valid_findings:
        hints.extend(build_file_level_hints(repo_root, finding))
    return hints


__all__ = [
    "build_family_hints",
    "build_root_hints",
    "family_rule_triggered",
    "iter_family_candidates",
    "iter_root_candidates",
    "root_rule_triggered",
]
