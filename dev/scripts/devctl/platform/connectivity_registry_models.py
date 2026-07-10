"""Typed connectivity registry projected into SYSTEM_MAP and guards."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .contracts import CrossLinkSpec


@dataclass(frozen=True, slots=True)
class ConnectivityFieldRow:
    """One typed field plus its declared writer/reader projection evidence."""

    field_name: str
    type_hint: str
    field_kind: str
    writer_ids: tuple[str, ...]
    reader_ids: tuple[str, ...] = ()
    projection_ids: tuple[str, ...] = ()
    derived_from: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ConnectivityWriterRow:
    """One source/projection writer known to the connectivity registry."""

    writer_id: str
    path: str
    authority_kind: str


@dataclass(frozen=True, slots=True)
class ConnectivityContractRow:
    """One platform contract and the fields/surfaces connected to it."""

    contract_id: str
    owner_layer: str
    runtime_model: str
    writer: ConnectivityWriterRow
    fields: tuple[ConnectivityFieldRow, ...]
    projection_ids: tuple[str, ...] = ()
    reader_ids: tuple[str, ...] = ()
    cross_links: tuple[CrossLinkSpec, ...] = ()


@dataclass(frozen=True, slots=True)
class MissingConnectionFinding:
    """One declared reader connection that lacks AST-visible evidence."""

    contract_id: str
    declared_reader_surface: str
    expected_evidence_kind: str
    suggested_wire_locations: tuple[str, ...]
    classification: str
    justification: str = ""
    override_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable payload."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ConnectivityRegistrySnapshot:
    """Generated read model for typed contract/writer/reader connectivity."""

    schema_version: int
    contract_id: str
    source_contract_count: int
    connected_contracts: tuple[ConnectivityContractRow, ...]
    governed_surface_ids: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable payload."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ConnectivityRegistrySummary:
    """Bounded summary carried by startup and render surfaces."""

    schema_version: int
    contract_id: str
    source_contract_count: int
    connected_contract_count: int
    source_field_count: int
    zero_reader_field_count: int
    reader_ids: tuple[str, ...]
    governed_surface_ids: tuple[str, ...]
    warning_count: int
    aspirational_gap_count: int = 0
    missing_connection_finding_count: int = 0
    mistakenly_declared_count: int = 0
    deferred_consumer_count: int = 0
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable payload."""
        return asdict(self)


__all__ = [
    "ConnectivityContractRow",
    "ConnectivityFieldRow",
    "ConnectivityRegistrySummary",
    "ConnectivityRegistrySnapshot",
    "ConnectivityWriterRow",
    "MissingConnectionFinding",
]
