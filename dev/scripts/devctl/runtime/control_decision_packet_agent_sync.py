"""Legacy agent-sync packet attention projection for controller payloads."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .control_decision_packet_lifecycle import (
    packet_by_id,
    packet_lifecycle_attention,
)
from .value_coercion import coerce_string


def agent_sync_packet_attention(
    payload: Mapping[str, object],
    *,
    actor: str = "",
) -> dict[str, object]:
    if not actor:
        return {}
    agent_sync = payload.get("agent_sync")
    if not isinstance(agent_sync, Mapping):
        return {}
    agents = agent_sync.get("agents")
    if not isinstance(agents, Mapping):
        return {}
    actor_state = agents.get(actor)
    if not isinstance(actor_state, Mapping):
        return {}
    pending_raw = actor_state.get("pending_packets_to_me")
    if not isinstance(pending_raw, Sequence) or isinstance(pending_raw, (str, bytes)):
        return {}
    pending_packet_ids = tuple(
        packet_id
        for packet_id in (coerce_string(item).strip() for item in pending_raw)
        if packet_id
    )
    if len(pending_packet_ids) != 1:
        return {}
    packet_id = pending_packet_ids[0]
    return packet_lifecycle_attention(packet_by_id(payload, packet_id), packet_id=packet_id)
