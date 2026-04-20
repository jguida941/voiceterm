"""Shared provenance helpers for startup/review projection payloads."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


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


def attach_surface_provenance(
    payload: Mapping[str, object] | None,
    *,
    source_identity: Mapping[str, object] | None = None,
    source_contract: str = "",
    source_command: str = "",
    observed_fields: tuple[str, ...] = (),
    inferred_fields: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Copy one mapping-like payload and attach the shared provenance tuple."""
    mapping = dict(payload or {})
    for key in (
        "source_identity",
        "source_contract",
        "source_command",
        "observed_fields",
        "inferred_fields",
    ):
        mapping.pop(key, None)
    if source_identity:
        mapping["source_identity"] = {
            str(key).strip(): str(value or "").strip()
            for key, value in source_identity.items()
            if str(key).strip() and str(value or "").strip()
        }
    if source_contract:
        mapping["source_contract"] = str(source_contract).strip()
    if source_command:
        mapping["source_command"] = str(source_command).strip()
    if observed_fields:
        mapping["observed_fields"] = [field for field in observed_fields if field]
    if inferred_fields:
        mapping["inferred_fields"] = [field for field in inferred_fields if field]
    return mapping
