"""Compatibility-redirect discovery for approved package-layout shims."""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path

if __package__:
    from .bootstrap import (
        DirectoryCrowdingRule,
        NamespaceFamilyRule,
        detect_compatibility_shim,
        resolve_shim_target_path,
    )
    from .rule_resolution import resolve_layout_rules
else:  # pragma: no cover - standalone script fallback
    from bootstrap import (
        DirectoryCrowdingRule,
        NamespaceFamilyRule,
        detect_compatibility_shim,
        resolve_shim_target_path,
    )
    from rule_resolution import resolve_layout_rules


def _record_redirect(
    redirects: dict[str, dict],
    *,
    repo_root: Path,
    path: Path,
    metadata: dict[str, str],
    policy_source: str,
) -> None:
    target = str(metadata.get("target") or "").strip()
    if not target:
        return
    relative = path.relative_to(repo_root).as_posix()
    resolved_target = resolve_shim_target_path(repo_root, target)
    redirects.setdefault(
        relative,
        {
            "path": relative,
            "target": target,
            "resolved_target": (
                resolved_target.relative_to(repo_root).as_posix()
                if resolved_target is not None
                else ""
            ),
            "target_exists": resolved_target is not None,
            "policy_source": policy_source,
        },
    )


def _collect_directory_redirects(
    *,
    repo_root: Path,
    redirects: dict[str, dict],
    crowding_rules: tuple[DirectoryCrowdingRule, ...],
) -> None:
    for rule in crowding_rules:
        root_abs = repo_root / rule.root
        if not root_abs.is_dir():
            continue
        for child in root_abs.iterdir():
            if not child.is_file() or not any(
                fnmatch(child.name, pattern) for pattern in rule.include_globs
            ):
                continue
            validation = detect_compatibility_shim(
                child,
                namespace_subdir=rule.recommended_subdir,
                shim_contains_all=rule.shim_contains_all,
                shim_max_nonblank_lines=rule.shim_max_nonblank_lines,
                shim_required_metadata_fields=rule.shim_required_metadata_fields,
            )
            if validation.is_valid:
                _record_redirect(
                    redirects,
                    repo_root=repo_root,
                    path=child,
                    metadata=validation.metadata,
                    policy_source=f"directory_crowding:{rule.root.as_posix()}",
                )


def _collect_family_redirects(
    *,
    repo_root: Path,
    redirects: dict[str, dict],
    family_rules: tuple[NamespaceFamilyRule, ...],
) -> None:
    for rule in family_rules:
        root_abs = repo_root / rule.root
        if not root_abs.is_dir():
            continue
        for path in root_abs.glob(f"{rule.flat_prefix}*.py"):
            if not path.is_file():
                continue
            validation = detect_compatibility_shim(
                path,
                namespace_subdir=rule.namespace_subdir,
                shim_max_nonblank_lines=rule.shim_max_nonblank_lines,
                shim_required_metadata_fields=rule.shim_required_metadata_fields,
            )
            if validation.is_valid:
                _record_redirect(
                    redirects,
                    repo_root=repo_root,
                    path=path,
                    metadata=validation.metadata,
                    policy_source=(
                        f"namespace_family:{rule.root.as_posix()}:{rule.flat_prefix}"
                    ),
                )


def collect_compatibility_redirects(
    *,
    repo_root: Path,
    crowding_rules: tuple[DirectoryCrowdingRule, ...] | None = None,
    family_rules: tuple[NamespaceFamilyRule, ...] | None = None,
) -> list[dict]:
    """Return canonical shim-target redirects for active compatibility shims."""
    active_crowding_rules = crowding_rules
    active_family_rules = family_rules
    if active_crowding_rules is None or active_family_rules is None:
        _flat_rules, resolved_family_rules, _docs_sync_rules, resolved_crowding_rules = (
            resolve_layout_rules(repo_root)
        )
        if active_crowding_rules is None:
            active_crowding_rules = resolved_crowding_rules
        if active_family_rules is None:
            active_family_rules = resolved_family_rules

    redirects: dict[str, dict] = {}
    _collect_directory_redirects(
        repo_root=repo_root,
        redirects=redirects,
        crowding_rules=active_crowding_rules,
    )
    _collect_family_redirects(
        repo_root=repo_root,
        redirects=redirects,
        family_rules=active_family_rules,
    )
    return [redirects[path] for path in sorted(redirects)]
