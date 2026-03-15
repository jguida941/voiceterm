"""Shared contract records for the reusable AI-governance platform."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlatformLayerSpec:
    """One logical layer in the extracted reusable platform."""

    layer_id: str
    purpose: str
    current_home: str


@dataclass(frozen=True, slots=True)
class ContractField:
    """One named field in a shared runtime contract."""

    name: str
    type_hint: str
    description: str


@dataclass(frozen=True, slots=True)
class ContractSpec:
    """A typed contract that frontends, loops, and repo packs should share."""

    contract_id: str
    owner_layer: str
    purpose: str
    required_fields: tuple[ContractField, ...]


@dataclass(frozen=True, slots=True)
class FrontendSurfaceSpec:
    """One frontend/client surface over the shared backend contracts."""

    surface_id: str
    authority: str
    consumes_contracts: tuple[str, ...]
    notes: str


@dataclass(frozen=True, slots=True)
class RepoBoundarySpec:
    """A repo-local boundary that should stay outside the portable core."""

    boundary_id: str
    lives_in: str
    reason: str


@dataclass(frozen=True, slots=True)
class PortabilityStatusSpec:
    """Current extraction status for one subsystem."""

    surface_id: str
    status: str
    current_owner: str
    next_step: str


@dataclass(frozen=True, slots=True)
class PlatformBlueprint:
    """Machine-readable blueprint for the reusable AI-governance platform."""

    command: str
    schema_version: int
    thesis: str
    layers: tuple[PlatformLayerSpec, ...]
    shared_contracts: tuple[ContractSpec, ...]
    frontend_surfaces: tuple[FrontendSurfaceSpec, ...]
    repo_local_boundaries: tuple[RepoBoundarySpec, ...]
    adoption_flow: tuple[str, ...]
    portability_status: tuple[PortabilityStatusSpec, ...]
