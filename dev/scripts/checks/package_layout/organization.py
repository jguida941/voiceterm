"""Build the unified package-layout organization surface."""

from __future__ import annotations

from dataclasses import asdict
from fnmatch import fnmatch
from pathlib import Path

if __package__:
    from .bootstrap import (
        RootRoleRule,
        detect_compatibility_shim,
    )
    from .rule_models import (
        CompatibilityRedirectState,
        LayoutDebtItem,
        OrganizationSurface,
        PackageRoleState,
    )
    from .rule_resolution import resolve_root_role_rules
else:  # pragma: no cover - standalone script fallback
    from bootstrap import (
        RootRoleRule,
        detect_compatibility_shim,
    )
    from rule_models import (
        CompatibilityRedirectState,
        LayoutDebtItem,
        OrganizationSurface,
        PackageRoleState,
    )
    from rule_resolution import resolve_root_role_rules


def build_organization_surface(
    *,
    repo_root: Path,
    compatibility_redirects: list[dict],
    crowded_directories: list[dict],
    crowded_namespace_families: list[dict],
    root_role_findings: list[dict],
    root_role_rules: tuple[RootRoleRule, ...] | None = None,
) -> dict:
    """Assemble the unified organization surface as a JSON-safe dict."""
    active_rules = root_role_rules or resolve_root_role_rules(repo_root)

    roles = _build_role_census(repo_root=repo_root, rules=active_rules)
    redirects = _build_redirect_entries(compatibility_redirects)
    debt = _build_debt_entries(
        crowded_directories=crowded_directories,
        crowded_namespace_families=crowded_namespace_families,
        root_role_findings=root_role_findings,
    )
    missing_targets = sum(1 for r in redirects if not r.target_exists)

    surface = OrganizationSurface(
        package_roles=tuple(roles),
        compatibility_redirects=tuple(redirects),
        layout_debt=tuple(debt),
        total_roles=len(roles),
        total_redirects=len(redirects),
        total_debt_items=len(debt),
        redirects_with_missing_targets=missing_targets,
    )
    return _to_json_safe(asdict(surface))


def organization_surface_to_dict(surface: OrganizationSurface) -> dict:
    """Serialize to a JSON-safe dict."""
    return _to_json_safe(asdict(surface))


def _to_json_safe(obj: object) -> object:
    """Recursively convert tuples to lists for JSON compatibility."""
    if isinstance(obj, dict):
        return {k: _to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_json_safe(item) for item in obj]
    return obj


def _build_role_census(
    *,
    repo_root: Path,
    rules: tuple[RootRoleRule, ...],
) -> list[PackageRoleState]:
    """Build the full role census for ALL declared roots, not just those with debt."""
    results: list[PackageRoleState] = []
    for rule in rules:
        root_dir = repo_root / rule.root
        if not root_dir.exists() or not root_dir.is_dir():
            continue

        files = [
            path
            for path in root_dir.iterdir()
            if path.is_file()
            and any(fnmatch(path.name, g) for g in rule.include_globs)
        ]

        counts = _classify_files(repo_root, files, rule)
        support_count = counts["support_module"]
        impl_count = counts["implementation_module"]
        debt = (
            support_count > rule.max_support_modules
            or impl_count > rule.max_implementation_modules
        )

        results.append(
            PackageRoleState(
                root=rule.root.as_posix(),
                include_globs=rule.include_globs,
                public_entrypoint_globs=rule.public_entrypoint_globs,
                generated_artifact_globs=rule.generated_artifact_globs,
                doc_authority_globs=rule.doc_authority_globs,
                support_suffixes=rule.support_suffixes,
                max_support_modules=rule.max_support_modules,
                max_implementation_modules=rule.max_implementation_modules,
                total_files=len(files),
                compat_shim_files=counts["compat_shim"],
                public_entrypoint_files=counts["public_entrypoint"],
                generated_artifact_files=counts["generated_artifact"],
                doc_authority_files=counts["doc_authority"],
                support_module_files=support_count,
                implementation_module_files=impl_count,
                debt_detected=debt,
            )
        )
    return results


def _classify_files(
    repo_root: Path,
    files: list[Path],
    rule: RootRoleRule,
) -> dict[str, int]:
    """Classify files by role and return counts."""
    counts = {
        "compat_shim": 0,
        "public_entrypoint": 0,
        "generated_artifact": 0,
        "doc_authority": 0,
        "support_module": 0,
        "implementation_module": 0,
    }
    for path in files:
        role = _classify_one(path, rule)
        counts[role] += 1
    return counts


def _classify_one(path: Path, rule: RootRoleRule) -> str:
    """Classify a single file by its declared role."""
    if detect_compatibility_shim(
        path,
        namespace_subdir="",
        shim_max_nonblank_lines=rule.shim_max_nonblank_lines,
        shim_required_metadata_fields=rule.shim_required_metadata_fields,
    ).is_valid:
        return "compat_shim"
    name = path.name
    if any(fnmatch(name, g) for g in rule.generated_artifact_globs):
        return "generated_artifact"
    if any(fnmatch(name, g) for g in rule.doc_authority_globs):
        return "doc_authority"
    if any(fnmatch(name, g) for g in rule.public_entrypoint_globs):
        return "public_entrypoint"
    if any(path.stem.endswith(s) for s in rule.support_suffixes):
        return "support_module"
    return "implementation_module"


def _build_redirect_entries(
    compatibility_redirects: list[dict],
) -> list[CompatibilityRedirectState]:
    """Convert raw redirect dicts to typed state objects."""
    return [
        CompatibilityRedirectState(
            path=str(r.get("path") or ""),
            target=str(r.get("target") or ""),
            resolved_target=str(r.get("resolved_target") or ""),
            target_exists=bool(r.get("target_exists", False)),
            policy_source=str(r.get("policy_source") or ""),
            owner=str(r.get("owner") or ""),
            reason=str(r.get("reason") or ""),
            expiry=str(r.get("expiry") or ""),
        )
        for r in compatibility_redirects
    ]


def _build_debt_entries(
    *,
    crowded_directories: list[dict],
    crowded_namespace_families: list[dict],
    root_role_findings: list[dict],
) -> list[LayoutDebtItem]:
    """Consolidate all layout debt sources into a flat typed list."""
    debt: list[LayoutDebtItem] = []

    for d in crowded_directories:
        debt.append(
            LayoutDebtItem(
                kind="crowded_directory",
                root=str(d.get("root") or ""),
                detail=f"{d.get('current_files', 0)} files (max {d.get('max_files', 0)})",
                current_files=int(d.get("current_files", 0)),
                max_files=int(d.get("max_files", 0)),
                enforcement_mode=str(d.get("enforcement_mode") or ""),
            )
        )

    for f in crowded_namespace_families:
        debt.append(
            LayoutDebtItem(
                kind="crowded_namespace_family",
                root=str(f.get("root") or ""),
                detail=(
                    f"{f.get('flat_prefix', '')}* has "
                    f"{f.get('current_files', 0)} files "
                    f"(threshold {f.get('min_family_size', 0)})"
                ),
                current_files=int(f.get("current_files", 0)),
                max_files=int(f.get("min_family_size", 0)),
                enforcement_mode=str(f.get("enforcement_mode") or ""),
            )
        )

    for r in root_role_findings:
        debt.append(
            LayoutDebtItem(
                kind="role_debt",
                root=str(r.get("root") or ""),
                detail=(
                    f"{r.get('support_module_files', 0)} support modules "
                    f"(max {r.get('max_support_modules', 0)}), "
                    f"{r.get('implementation_module_files', 0)} implementation modules "
                    f"(max {r.get('max_implementation_modules', 0)})"
                ),
            )
        )

    return debt
