"""Typed models for the static SystemCatalog and derived AgentDispatchPacket.

SystemCatalog owns "what exists" -- a static inventory of commands, guards,
probes, surfaces, and report types built from existing registries.

AgentDispatchPacket owns "what to run" -- a derived routing recommendation
composed from classify_lane(), live quality policy, and the catalog.

Neither model creates new runtime authority. They project existing typed state
into agent-consumable packets.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CatalogCommand:
    """One devctl command in the static catalog."""

    name: str
    handler_module: str
    read_only: bool = False


@dataclass(frozen=True, slots=True)
class CatalogGuard:
    """One guard script in the static catalog."""

    script_id: str
    relative_path: str
    languages: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CatalogProbe:
    """One review probe in the static catalog."""

    script_id: str
    relative_path: str


@dataclass(frozen=True, slots=True)
class CatalogSurface:
    """One frontend surface in the static catalog."""

    surface_id: str
    authority: str
    consumes_contracts: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SystemCatalog:
    """Static capability inventory built from existing registries.

    Feeds context-graph as capability nodes and the discover command as
    the primary consumer.
    """

    schema_version: int
    commands: tuple[CatalogCommand, ...]
    guards: tuple[CatalogGuard, ...]
    probes: tuple[CatalogProbe, ...]
    surfaces: tuple[CatalogSurface, ...]
    total_commands: int = 0
    total_guards: int = 0
    total_probes: int = 0
    total_surfaces: int = 0


@dataclass(frozen=True, slots=True)
class AgentDispatchPacket:
    """Derived routing recommendation for a bounded change set.

    Composed from classify_lane(), live quality policy, and the system
    catalog. Recommends what guards/probes to run without becoming a
    second policy store.
    """

    lane: str
    bundle_name: str
    applicable_guards: tuple[str, ...]
    applicable_probes: tuple[str, ...]
    preflight_commands: tuple[str, ...] = ()
    context_level: str = "standard"
    changed_paths: tuple[str, ...] = ()
    evidence: tuple[str, ...] = field(default_factory=tuple)
