"""Typed connectivity registry projected into SYSTEM_MAP and guards."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


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


__all__ = [
    "ConnectivityContractRow",
    "ConnectivityFieldRow",
    "ConnectivityRegistrySnapshot",
    "ConnectivityWriterRow",
]
