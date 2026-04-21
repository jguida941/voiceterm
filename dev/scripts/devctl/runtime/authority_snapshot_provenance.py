"""Provenance extraction for authority snapshot builders."""

from __future__ import annotations

from collections.abc import Mapping

from .authority_snapshot_parse_support import mapping_or_empty as _mapping
from .surface_provenance import (
    build_surface_source_identity,
    source_identity_from_mapping,
    surface_provenance_from_mapping,
)


def authority_snapshot_provenance_kwargs(
    payload: Mapping[str, object],
) -> dict[str, object]:
    provenance = surface_provenance_from_mapping(payload)
    return provenance.with_updates(
        source_identity=_source_identity_from_payload(payload),
        source_contract=_source_contract_from_payload(payload),
    ).as_kwargs()


def _source_identity_from_payload(payload: Mapping[str, object]) -> dict[str, str]:
    raw_identity = source_identity_from_mapping(payload.get("source_identity"))
    if raw_identity:
        return raw_identity
    bridge_liveness = _mapping(payload.get("bridge_liveness"))
    governance = _mapping(payload.get("governance"))
    push_enforcement = _mapping(governance.get("push_enforcement")) or _mapping(
        bridge_liveness.get("push_enforcement")
    )
    commit_pipeline = _mapping(payload.get("commit_pipeline"))
    return build_surface_source_identity(
        generation_id=str(
            payload.get("generation_id") or commit_pipeline.get("generation_id") or ""
        ),
        head_sha=str(
            payload.get("head_sha")
            or push_enforcement.get("current_head_commit")
            or commit_pipeline.get("commit_sha")
            or ""
        ),
        worktree_hash=str(
            payload.get("worktree_hash")
            or bridge_liveness.get("last_worktree_hash")
            or push_enforcement.get("current_worktree_identity")
            or ""
        ),
    )


def _source_contract_from_payload(payload: Mapping[str, object]) -> str:
    return str(
        payload.get("source_contract")
        or payload.get("contract_id")
        or payload.get("command")
        or ""
    ).strip()
