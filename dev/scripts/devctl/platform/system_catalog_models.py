"""Typed models for SystemCatalog entries and AgentDispatchPacket.

SystemCatalog holds a frozen inventory of commands, guards, probes,
surfaces, and contracts built from existing registries.

AgentDispatchPacket carries per-request routing derived from lane
classification and language-scoped guard/probe filtering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Entry dataclasses -- each mirrors one row in a registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CommandEntry:
    """One registered devctl command."""

    name: str
    path: str
    category: str
    description: str = ""


@dataclass(frozen=True, slots=True)
class GuardEntry:
    """One registered guard script (layer 1 -- blocks merge)."""

    name: str
    path: str
    category: str
    description: str = ""
    languages: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProbeEntry:
    """One registered review probe (layer 2 -- advisory)."""

    name: str
    path: str
    category: str
    description: str = ""
    languages: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SurfaceEntry:
    """One registered frontend or discovery surface."""

    name: str
    path: str
    category: str
    description: str = ""


@dataclass(frozen=True, slots=True)
class ContractEntry:
    """One registered runtime state contract."""

    name: str
    path: str
    category: str
    description: str = ""
    fields: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# SystemCatalog -- frozen, generated from code registries
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SystemCatalog:
    """Typed, generated-from-code capability registry.

    Every field is populated by scanning existing Python registries at
    build time. The catalog is immutable once built and carries a UTC
    timestamp so consumers know when it was generated.
    """

    commands: tuple[CommandEntry, ...] = ()
    guards: tuple[GuardEntry, ...] = ()
    probes: tuple[ProbeEntry, ...] = ()
    surfaces: tuple[SurfaceEntry, ...] = ()
    contracts: tuple[ContractEntry, ...] = ()
    generated_at_utc: str = ""
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe dictionary for discover/view consumers."""
        return {
            "schema_version": self.schema_version,
            "generated_at_utc": self.generated_at_utc,
            "commands": [_command_to_dict(e) for e in self.commands],
            "guards": [_guard_to_dict(e) for e in self.guards],
            "probes": [_probe_to_dict(e) for e in self.probes],
            "surfaces": [_surface_to_dict(e) for e in self.surfaces],
            "contracts": [_contract_to_dict(e) for e in self.contracts],
            "total_commands": len(self.commands),
            "total_guards": len(self.guards),
            "total_probes": len(self.probes),
            "total_surfaces": len(self.surfaces),
            "total_contracts": len(self.contracts),
        }


# ---------------------------------------------------------------------------
# AgentDispatchPacket -- derived routing for a bounded change set
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AgentDispatchPacket:
    """Routing recommendation for a set of changed paths.

    Composed from classify_lane() output and the catalog's guard/probe
    inventory. Recommends what guards and probes to run, which bundle
    applies, and the preflight command to execute.
    """

    changed_paths: tuple[str, ...] = ()
    applicable_guards: tuple[str, ...] = ()
    applicable_probes: tuple[str, ...] = ()
    recommended_bundle: str = ""
    preflight_command: str = ""
    context_level: str = "standard"
    lane: str = ""
    evidence: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def _surface_to_dict(entry: SurfaceEntry) -> dict[str, str]:
    return {
        "name": entry.name,
        "path": entry.path,
        "category": entry.category,
        "description": entry.description,
    }


def _command_to_dict(entry: CommandEntry) -> dict[str, str]:
    return {
        "name": entry.name,
        "path": entry.path,
        "category": entry.category,
        "description": entry.description,
    }


def _guard_to_dict(entry: GuardEntry) -> dict[str, Any]:
    return {
        "name": entry.name,
        "path": entry.path,
        "category": entry.category,
        "description": entry.description,
        "languages": list(entry.languages),
    }


def _probe_to_dict(entry: ProbeEntry) -> dict[str, Any]:
    return {
        "name": entry.name,
        "path": entry.path,
        "category": entry.category,
        "description": entry.description,
        "languages": list(entry.languages),
    }


def _contract_to_dict(entry: ContractEntry) -> dict[str, Any]:
    return {
        "name": entry.name,
        "path": entry.path,
        "category": entry.category,
        "description": entry.description,
        "fields": list(entry.fields),
    }
