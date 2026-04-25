"""Typed models for the generated SYSTEM_MAP managed block."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .connectivity_registry_models import ConnectivityRegistrySnapshot


@dataclass(frozen=True, slots=True)
class SystemMapRootSummary:
    """Bounded file-count summary for one architecture root."""

    root: str
    python_file_count: int
    top_level_counts: tuple[tuple[str, int], ...] = ()


@dataclass(frozen=True, slots=True)
class SystemMapSurfaceSummary:
    """Policy-owned generated surface included in the connectivity index."""

    surface_id: str
    renderer: str
    output_path: str
    tracked: bool
    local_only: bool


@dataclass(frozen=True, slots=True)
class SystemMapSnapshot:
    """Generated connectivity snapshot projected into SYSTEM_MAP.md."""

    schema_version: int
    contract_id: str
    generated_section_id: str
    tracked_roots: tuple[SystemMapRootSummary, ...]
    governed_surfaces: tuple[SystemMapSurfaceSummary, ...]
    connectivity_registry: ConnectivityRegistrySnapshot
    required_commands: tuple[str, ...]
    source_policy_path: str
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable payload."""
        return asdict(self)
