"""Shared bootstrap for package-layout guard modules."""

from __future__ import annotations

from pathlib import Path

try:
    from check_bootstrap import (
        REPO_ROOT,
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        import_local_or_repo_module,
        import_repo_module,
        resolve_guard_config,
        utc_timestamp,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - package-style import fallback
    if exc.name != "check_bootstrap":
        raise
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        build_since_ref_format_parser,
        emit_runtime_error,
        import_attr,
        import_local_or_repo_module,
        import_repo_module,
        resolve_guard_config,
        utc_timestamp,
    )

_rules_module = import_local_or_repo_module(
    "package_layout.rules",
    "dev.scripts.checks.package_layout.rules",
    repo_root=REPO_ROOT,
)
_quality_scan_mode_module = import_repo_module(
    "dev.scripts.devctl.quality_scan_mode",
    repo_root=REPO_ROOT,
)

CompatibilityShimValidation = _rules_module.CompatibilityShimValidation
DirectoryCrowdingRule = _rules_module.DirectoryCrowdingRule
FlatRootRule = _rules_module.FlatRootRule
NamespaceDocsSyncRule = _rules_module.NamespaceDocsSyncRule
NamespaceFamilyRule = _rules_module.NamespaceFamilyRule
STANDARD_SHIM_METADATA_FIELDS = _rules_module.STANDARD_SHIM_METADATA_FIELDS
detect_compatibility_shim = _rules_module.detect_compatibility_shim
docs_contain_tokens = _rules_module.docs_contain_tokens
is_backward_compat_shim = _rules_module.is_backward_compat_shim
is_under_root = _rules_module.is_under_root
load_directory_crowding_rules = _rules_module.load_directory_crowding_rules
load_flat_root_rules = _rules_module.load_flat_root_rules
load_namespace_docs_sync_rules = _rules_module.load_namespace_docs_sync_rules
load_namespace_family_rules = _rules_module.load_namespace_family_rules
recommended_namespace_path = _rules_module.recommended_namespace_path
resolve_shim_target_path = _rules_module.resolve_shim_target_path
is_adoption_scan = _quality_scan_mode_module.is_adoption_scan

__all__ = [
    "CompatibilityShimValidation",
    "DirectoryCrowdingRule",
    "FlatRootRule",
    "NamespaceDocsSyncRule",
    "NamespaceFamilyRule",
    "REPO_ROOT",
    "STANDARD_SHIM_METADATA_FIELDS",
    "build_since_ref_format_parser",
    "detect_compatibility_shim",
    "docs_contain_tokens",
    "emit_runtime_error",
    "import_attr",
    "is_adoption_scan",
    "is_backward_compat_shim",
    "is_under_root",
    "load_directory_crowding_rules",
    "load_flat_root_rules",
    "load_namespace_docs_sync_rules",
    "load_namespace_family_rules",
    "recommended_namespace_path",
    "resolve_shim_target_path",
    "resolve_guard_config",
    "utc_timestamp",
]
