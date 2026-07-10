"""Packet list helpers for the claude-loop/agent-loop surfaces."""

from __future__ import annotations

from typing import Any

from ...review_channel.packet_contract import packet_route_matches_scope

_PACKET_FIELDS = (
    "packet_id",
    "kind",
    "from_agent",
    "to_agent",
    "summary",
    "status",
    "lifecycle_current_state",
    "requested_action",
    "policy_hint",
    "target_ref",
    "target_revision",
    "target_role",
    "target_session_id",
    "posted_at",
    "acked_at_utc",
    "acked_by",
    "applied_at_utc",
    "delivery_observed_at_utc",
    "execution_started_at_utc",
    "execution_started_by",
    "execution_failed_at_utc",
    "execution_failed_reason",
    "apply_pending_after_execution_at_utc",
    "apply_pending_after_execution_reason",
    "semantic_zref",
)


def scoped_packets(
    raw_packets: object,
    *,
    actor_id: str,
    actor_role: str = "",
    session_id: str = "",
) -> list[dict[str, Any]]:
    """Return compact packet rows visible to one actor scope."""
    packets: list[dict[str, Any]] = []
    if not isinstance(raw_packets, list):
        return packets
    actor = str(actor_id or "").strip()
    for packet in raw_packets:
        if not isinstance(packet, dict):
            continue
        if actor and str(packet.get("to_agent") or "").strip() != actor:
            continue
        if not packet_route_matches_scope(
            packet,
            target_role=actor_role,
            target_session_id=session_id,
        ):
            continue
        packets.append(
            {field: packet.get(field) for field in _PACKET_FIELDS}
        )
    return packets


__all__ = ["scoped_packets"]
