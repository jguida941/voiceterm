"""Connectivity-registry metadata helpers for graph nodes."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from ..platform.connectivity_registry import summarize_connectivity_registry
from ..platform.connectivity_registry_models import (
    ConnectivityContractRow,
    ConnectivityFieldRow,
    ConnectivityRegistrySnapshot,
)
from ..platform.contracts import CrossLinkSpec


@dataclass(frozen=True, slots=True)
class RegistryContractMetadata:
    """Bounded metadata for one registry-backed contract node."""

    connectivity_registry_contract_id: str
    owner_layer: str
    writer_id: str
    reader_ids: tuple[str, ...]
    projection_ids: tuple[str, ...]
    cross_links: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["reader_ids"] = list(self.reader_ids)
        payload["projection_ids"] = list(self.projection_ids)
        payload["cross_links"] = list(self.cross_links)
        return payload


@dataclass(frozen=True, slots=True)
class RegistrySnapshotMetadata:
    """Bounded GraphNode metadata for the registry contract node."""

    connectivity_registry_contract_id: str
    connected_contract_count: int
    source_field_count: int
    zero_reader_field_count: int
    reader_ids: tuple[str, ...]
    governed_surface_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["reader_ids"] = list(self.reader_ids)
        payload["governed_surface_ids"] = list(self.governed_surface_ids)
        return payload


@dataclass(frozen=True, slots=True)
class RegistryFieldMetadata:
    """Bounded metadata for one registry-backed field node."""

    field_kind: str
    writer_ids: tuple[str, ...]
    reader_ids: tuple[str, ...]
    projection_ids: tuple[str, ...]
    derived_from: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["writer_ids"] = list(self.writer_ids)
        payload["reader_ids"] = list(self.reader_ids)
        payload["projection_ids"] = list(self.projection_ids)
        payload["derived_from"] = list(self.derived_from)
        return payload


def registry_contract_metadata(
    registry: ConnectivityRegistrySnapshot,
    row: ConnectivityContractRow,
) -> dict[str, object]:
    return RegistryContractMetadata(
        connectivity_registry_contract_id=registry.contract_id,
        owner_layer=row.owner_layer,
        writer_id=row.writer.writer_id,
        reader_ids=tuple(row.reader_ids),
        projection_ids=tuple(row.projection_ids),
        cross_links=tuple(_cross_link_metadata(link) for link in row.cross_links),
    ).to_dict()


def registry_snapshot_metadata(
    registry: ConnectivityRegistrySnapshot | None,
) -> dict[str, object]:
    if registry is None:
        return {}
    summary = summarize_connectivity_registry(registry)
    return RegistrySnapshotMetadata(
        connectivity_registry_contract_id=registry.contract_id,
        connected_contract_count=summary.connected_contract_count,
        source_field_count=summary.source_field_count,
        zero_reader_field_count=summary.zero_reader_field_count,
        reader_ids=summary.reader_ids,
        governed_surface_ids=summary.governed_surface_ids,
    ).to_dict()


def registry_field_metadata(field: ConnectivityFieldRow) -> dict[str, object]:
    return RegistryFieldMetadata(
        field_kind=field.field_kind,
        writer_ids=tuple(field.writer_ids),
        reader_ids=tuple(field.reader_ids),
        projection_ids=tuple(field.projection_ids),
        derived_from=tuple(field.derived_from),
    ).to_dict()


def _cross_link_metadata(link: CrossLinkSpec) -> dict[str, object]:
    return asdict(link)


__all__ = [
    "registry_contract_metadata",
    "registry_field_metadata",
    "registry_snapshot_metadata",
]
