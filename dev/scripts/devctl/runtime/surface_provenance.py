"""Shared provenance helpers for startup/review projection payloads."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

_PROVENANCE_KEYS = (
    "snapshot_id",
    "zref",
    "source_identity",
    "source_contract",
    "source_command",
    "observed_fields",
    "inferred_fields",
)


class SurfaceProvenance:
    """Shared proof-tick provenance carried by runtime projection payloads."""

    __slots__ = _PROVENANCE_KEYS

    def __init__(self, values: Mapping[str, object] | None = None) -> None:
        mapping = values or {}
        self.snapshot_id = str(mapping.get("snapshot_id") or "").strip()
        self.zref = str(mapping.get("zref") or "").strip()
        self.source_identity = source_identity_from_mapping(
            mapping.get("source_identity")
        )
        self.source_contract = str(mapping.get("source_contract") or "").strip()
        self.source_command = str(mapping.get("source_command") or "").strip()
        self.observed_fields = _string_items(mapping.get("observed_fields"))
        self.inferred_fields = _string_items(mapping.get("inferred_fields"))

    def as_kwargs(self) -> dict[str, object]:
        return {key: getattr(self, key) for key in _PROVENANCE_KEYS}

    def with_updates(self, **updates: object) -> "SurfaceProvenance":
        values = self.as_kwargs()
        values.update(updates)
        return SurfaceProvenance(values)


def build_surface_source_identity(
    *,
    head_sha: str = "",
    worktree_hash: str = "",
    generation_id: str = "",
) -> dict[str, str]:
    """Return the shared source-identity tuple for one emitted surface."""
    identity: dict[str, str] = {}
    if generation_id:
        identity["generation_id"] = str(generation_id).strip()
    if head_sha:
        identity["head_sha"] = str(head_sha).strip()
    if worktree_hash:
        identity["worktree_hash"] = str(worktree_hash).strip()
    return identity


def source_identity_from_mapping(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(key).strip(): str(item or "").strip()
        for key, item in value.items()
        if str(key).strip() and str(item or "").strip()
    }


def surface_provenance_from_mapping(
    value: object,
    *,
    source_identity: Mapping[str, object] | None = None,
) -> SurfaceProvenance:
    if not isinstance(value, Mapping):
        value = {}
    mapping = dict(value)
    if source_identity is not None:
        mapping["source_identity"] = source_identity
    return SurfaceProvenance(mapping)


def surface_provenance_from_object(
    value: object,
    *,
    source_identity: Mapping[str, object] | None = None,
) -> SurfaceProvenance:
    mapping = {
        key: getattr(value, key, "")
        for key in _PROVENANCE_KEYS
        if value is not None
    }
    return surface_provenance_from_mapping(
        mapping,
        source_identity=source_identity,
    )


def surface_provenance_kwargs(value: object) -> dict[str, object]:
    return surface_provenance_from_mapping(value).as_kwargs()


def attach_surface_provenance(
    payload: Mapping[str, object] | None,
    *,
    provenance: SurfaceProvenance | None = None,
) -> dict[str, Any]:
    """Copy one mapping-like payload and attach the shared provenance tuple."""
    mapping = dict(payload or {})
    resolved = provenance or surface_provenance_from_mapping(mapping)
    for key in _PROVENANCE_KEYS:
        mapping.pop(key, None)
    if resolved.snapshot_id:
        mapping["snapshot_id"] = resolved.snapshot_id
    if resolved.zref:
        mapping["zref"] = resolved.zref
    if resolved.source_identity:
        mapping["source_identity"] = resolved.source_identity
    if resolved.source_contract:
        mapping["source_contract"] = resolved.source_contract
    if resolved.source_command:
        mapping["source_command"] = resolved.source_command
    if resolved.observed_fields:
        mapping["observed_fields"] = list(resolved.observed_fields)
    if resolved.inferred_fields:
        mapping["inferred_fields"] = list(resolved.inferred_fields)
    return mapping


def _string_items(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())
