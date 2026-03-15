"""Backward-compatible package-layout rules facade."""

from __future__ import annotations

if __package__:
    from .rule_models import (
        CompatibilityShimValidation,
        DirectoryCrowdingRule,
        FlatRootRule,
        NamespaceDocsSyncRule,
        NamespaceFamilyRule,
    )
    from .rule_parsing import (
        docs_contain_tokens,
        is_under_root,
        load_directory_crowding_rules,
        load_flat_root_rules,
        load_namespace_docs_sync_rules,
        load_namespace_family_rules,
        recommended_namespace_path,
    )
    from .shim_validation import (
        STANDARD_SHIM_METADATA_FIELDS,
        detect_compatibility_shim,
        is_backward_compat_shim,
    )
else:  # pragma: no cover - standalone script fallback
    from rule_models import (
        CompatibilityShimValidation,
        DirectoryCrowdingRule,
        FlatRootRule,
        NamespaceDocsSyncRule,
        NamespaceFamilyRule,
    )
    from rule_parsing import (
        docs_contain_tokens,
        is_under_root,
        load_directory_crowding_rules,
        load_flat_root_rules,
        load_namespace_docs_sync_rules,
        load_namespace_family_rules,
        recommended_namespace_path,
    )
    from shim_validation import (
        STANDARD_SHIM_METADATA_FIELDS,
        detect_compatibility_shim,
        is_backward_compat_shim,
    )

__all__ = [
    "CompatibilityShimValidation",
    "DirectoryCrowdingRule",
    "FlatRootRule",
    "NamespaceDocsSyncRule",
    "NamespaceFamilyRule",
    "STANDARD_SHIM_METADATA_FIELDS",
    "detect_compatibility_shim",
    "docs_contain_tokens",
    "is_backward_compat_shim",
    "is_under_root",
    "load_directory_crowding_rules",
    "load_flat_root_rules",
    "load_namespace_docs_sync_rules",
    "load_namespace_family_rules",
    "recommended_namespace_path",
]
