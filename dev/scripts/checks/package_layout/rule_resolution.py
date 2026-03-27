"""Shared package-layout rule loading helpers."""

from __future__ import annotations

from pathlib import Path

if __package__:
    from .bootstrap import (
        DirectoryCrowdingRule,
        FlatRootRule,
        NamespaceDocsSyncRule,
        NamespaceFamilyRule,
        load_directory_crowding_rules,
        load_flat_root_rules,
        load_namespace_docs_sync_rules,
        load_namespace_family_rules,
        resolve_guard_config,
    )
else:  # pragma: no cover - standalone script fallback
    from bootstrap import (
        DirectoryCrowdingRule,
        FlatRootRule,
        NamespaceDocsSyncRule,
        NamespaceFamilyRule,
        load_directory_crowding_rules,
        load_flat_root_rules,
        load_namespace_docs_sync_rules,
        load_namespace_family_rules,
        resolve_guard_config,
    )


def resolve_layout_rules(
    repo_root: Path,
) -> tuple[
    tuple[FlatRootRule, ...],
    tuple[NamespaceFamilyRule, ...],
    tuple[NamespaceDocsSyncRule, ...],
    tuple[DirectoryCrowdingRule, ...],
]:
    """Load the active package-layout rule sets with code-shape fallback."""
    package_layout = resolve_guard_config("package_layout", repo_root=repo_root)
    code_shape = resolve_guard_config("code_shape", repo_root=repo_root)
    flat_rules = load_flat_root_rules(package_layout.get("flat_root_rules"))
    family_rules = load_namespace_family_rules(
        package_layout.get("namespace_family_rules")
    ) or load_namespace_family_rules(code_shape.get("namespace_family_rules"))
    docs_sync_rules = load_namespace_docs_sync_rules(
        package_layout.get("namespace_docs_sync_rules")
    ) or load_namespace_docs_sync_rules(code_shape.get("namespace_docs_sync_rules"))
    crowding_rules = load_directory_crowding_rules(
        package_layout.get("directory_crowding_rules")
    ) or load_directory_crowding_rules(code_shape.get("directory_crowding_rules"))
    return flat_rules, family_rules, docs_sync_rules, crowding_rules
