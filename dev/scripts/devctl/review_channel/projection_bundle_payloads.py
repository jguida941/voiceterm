"""Payload builders for review-channel projection bundles."""

from __future__ import annotations

from collections.abc import Sequence

from ..runtime.surface_provenance import (
    attach_surface_provenance,
    surface_provenance_from_mapping,
)
from .context_refs import normalize_context_pack_refs


def build_full_projection(
    *,
    action: str,
    review_state: dict[str, object],
    agent_registry: dict[str, object],
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": 1,
        "command": "review-channel",
        "action": action,
        "timestamp": review_state.get("timestamp"),
        "ok": review_state.get("ok"),
    }
    payload["snapshot_id"] = review_state.get("snapshot_id")
    payload["zref"] = review_state.get("zref")
    payload["review_state"] = review_state
    payload["authority_snapshot"] = review_state.get("authority_snapshot")
    payload["agent_registry"] = agent_registry
    payload["warnings"] = review_state.get("warnings", [])
    payload["errors"] = review_state.get("errors", [])
    return attach_surface_provenance(
        payload,
        provenance=surface_provenance_from_mapping(review_state),
    )


def build_actions_projection(review_state: dict[str, object]) -> dict[str, object]:
    action_rows: list[dict[str, object]] = []
    packets = review_state.get("packets")
    if isinstance(packets, Sequence) and not isinstance(packets, (str, bytes)):
        for packet in packets:
            if isinstance(packet, dict):
                action_rows.append(_action_row(packet))
    payload = {
        "schema_version": 1,
        "command": "review-channel",
        "timestamp": review_state.get("timestamp"),
        "snapshot_id": review_state.get("snapshot_id"),
        "zref": review_state.get("zref"),
    }
    payload["actions"] = action_rows
    return attach_surface_provenance(
        payload,
        provenance=surface_provenance_from_mapping(review_state),
    )


def _action_row(packet: dict[str, object]) -> dict[str, object]:
    row = {
        "packet_id": packet.get("packet_id"),
        "requested_action": packet.get("requested_action"),
        "policy_hint": packet.get("policy_hint"),
        "approval_required": packet.get("approval_required"),
        "status": packet.get("status"),
    }
    row["target_kind"] = packet.get("target_kind")
    row["target_ref"] = packet.get("target_ref")
    row["target_revision"] = packet.get("target_revision")
    row["pipeline_generation"] = packet.get("pipeline_generation")
    row["staged_snapshot_hash"] = packet.get("staged_snapshot_hash")
    row["guard_results_summary"] = packet.get("guard_results_summary")
    row["context_pack_refs"] = normalize_context_pack_refs(
        packet.get("context_pack_refs")
    )
    return row
