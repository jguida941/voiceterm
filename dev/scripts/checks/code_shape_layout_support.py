"""Backward-compatible re-export surface for package-layout support."""

from __future__ import annotations

try:
    from package_layout.support import (
        FlatRootRule,
        NamespaceDocsSyncRule,
        NamespaceFamilyRule,
        collect_flat_root_violations,
        collect_namespace_docs_sync_violations,
        collect_namespace_layout_violations,
    )
except ModuleNotFoundError:  # pragma: no cover - import fallback for package-style test loading
    from dev.scripts.checks.package_layout.support import (
        FlatRootRule,
        NamespaceDocsSyncRule,
        NamespaceFamilyRule,
        collect_flat_root_violations,
        collect_namespace_docs_sync_violations,
        collect_namespace_layout_violations,
    )

__all__ = [
    "FlatRootRule",
    "NamespaceDocsSyncRule",
    "NamespaceFamilyRule",
    "collect_flat_root_violations",
    "collect_namespace_docs_sync_violations",
    "collect_namespace_layout_violations",
]
