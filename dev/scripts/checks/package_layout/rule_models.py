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
class CompatibilityShimValidation:
    """Validation result for one compatibility shim candidate."""

    is_valid: bool
    metadata: dict[str, str]
    missing_metadata_fields: tuple[str, ...] = ()


__all__ = [
    "CompatibilityShimValidation",
    "DirectoryCrowdingRule",
    "FlatRootRule",
    "NamespaceDocsSyncRule",
    "NamespaceFamilyRule",
]
