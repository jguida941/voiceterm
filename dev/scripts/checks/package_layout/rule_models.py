"""Data records for package-layout policy."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FlatRootRule:
    """Allow only specific new top-level modules under one directory root."""

    root: Path
    include_globs: tuple[str, ...]
    allowed_new_globs: tuple[str, ...]
    guidance: str = ""
    recommended_subdir: str = ""
    shim_contains_all: tuple[str, ...] = ()
    shim_max_nonblank_lines: int = 0
    shim_required_metadata_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class NamespaceFamilyRule:
    """Require crowded flat module families to move into a namespace directory."""

    root: Path
    flat_prefix: str
    namespace_subdir: str
    min_family_size: int
    enforcement_mode: str = "freeze"
    guidance: str = ""
    shim_max_nonblank_lines: int = 0
    shim_required_metadata_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class NamespaceDocsSyncRule:
    """Require docs to reference newly introduced namespace-module roots."""

    namespace_root: Path
    required_docs: tuple[Path, ...]
    required_token: str = ""
    required_tokens: tuple[str, ...] = ()


@dataclass(frozen=True)
class DirectoryCrowdingRule:
    """Govern overcrowded flat roots and freeze further growth when needed."""

    root: Path
    include_globs: tuple[str, ...]
    max_files: int
    enforcement_mode: str = "freeze"
    guidance: str = ""
    recommended_subdir: str = ""
    shim_contains_all: tuple[str, ...] = ()
    shim_max_nonblank_lines: int = 0
    shim_required_metadata_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class RootRoleRule:
    """Describe which flat-root file roles are allowed under one root."""

    root: Path
    include_globs: tuple[str, ...]
    public_entrypoint_globs: tuple[str, ...] = ()
    generated_artifact_globs: tuple[str, ...] = ()
    doc_authority_globs: tuple[str, ...] = ()
    support_suffixes: tuple[str, ...] = ()
    max_support_modules: int = 0
    max_implementation_modules: int = 0
    guidance: str = ""
    shim_max_nonblank_lines: int = 0
    shim_required_metadata_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class CompatibilityShimValidation:
    """Validation result for one compatibility shim candidate."""

    is_valid: bool
    metadata: dict[str, str]
    missing_metadata_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class PackageRoleState:
    """Live role census for one declared package root."""

    root: str
    include_globs: tuple[str, ...]
    public_entrypoint_globs: tuple[str, ...]
    generated_artifact_globs: tuple[str, ...]
    doc_authority_globs: tuple[str, ...]
    support_suffixes: tuple[str, ...]
    max_support_modules: int
    max_implementation_modules: int
    total_files: int = 0
    compat_shim_files: int = 0
    public_entrypoint_files: int = 0
    generated_artifact_files: int = 0
    doc_authority_files: int = 0
    support_module_files: int = 0
    implementation_module_files: int = 0
    debt_detected: bool = False


@dataclass(frozen=True)
class CompatibilityRedirectState:
    """One approved compatibility redirect with full shim provenance."""

    path: str
    target: str
    resolved_target: str
    target_exists: bool
    policy_source: str
    owner: str = ""
    reason: str = ""
    expiry: str = ""


@dataclass(frozen=True)
class LayoutDebtItem:
    """One instance of live package-layout debt."""

    kind: str
    root: str
    detail: str
    current_files: int = 0
    max_files: int = 0
    enforcement_mode: str = ""


@dataclass(frozen=True)
class OrganizationSurface:
    """Unified machine-readable view of package-layout organization state."""

    package_roles: tuple[PackageRoleState, ...]
    compatibility_redirects: tuple[CompatibilityRedirectState, ...]
    layout_debt: tuple[LayoutDebtItem, ...]
    total_roles: int = 0
    total_redirects: int = 0
    total_debt_items: int = 0
    redirects_with_missing_targets: int = 0


__all__ = [
    "CompatibilityRedirectState",
    "CompatibilityShimValidation",
    "DirectoryCrowdingRule",
    "FlatRootRule",
    "LayoutDebtItem",
    "NamespaceDocsSyncRule",
    "NamespaceFamilyRule",
    "OrganizationSurface",
    "PackageRoleState",
    "RootRoleRule",
]
