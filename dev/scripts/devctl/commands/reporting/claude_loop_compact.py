"""Compact machine output for provider-neutral agent-loop."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

_PACKET_FIELDS = (
    "packet_id",
    "plan_id",
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
    "anchor_refs",
    "intake_ref",
    "posted_at",
)


def compact_agent_loop_output(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return the proof-first JSON contract agents should inspect."""
    return {
        "schema_version": 1,
        "contract_id": "AgentLoopOutput",
        "command": "agent-loop",
        "timestamp": payload.get("timestamp"),
        "loop_request": dict(_mapping(payload.get("loop_request"))),
        "agent_loop_decision": dict(_mapping(payload.get("agent_loop_decision"))),
        "proof_evidence": dict(_mapping(payload.get("proof_evidence"))),
        "typed_snapshot_freshness": dict(
            _mapping(payload.get("typed_snapshot_freshness"))
        ),
        "packet_attention": _compact_packet_attention(
            _mapping(payload.get("packet_attention"))
        ),
        "pending_packets": _compact_packets(payload.get("pending_packets")),
        "control_packets": _compact_packets(payload.get("control_packets")),
    }


def _compact_packet_attention(attention: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "observation_actor_id",
        "observation_session_id",
        "latest_inbox_event_id",
        "latest_attention_packet_id",
        "last_observed_event_id",
        "pending_packet_count",
        "superseded_packet_id",
        "pivot_required",
        "wake_required",
        "stale_reason",
        "pivot_reasons",
    )
    return {key: attention.get(key) for key in keys if key in attention}


def _compact_packets(value: object, *, limit: int = 5) -> list[dict[str, Any]]:
    packets = value if isinstance(value, Sequence) and not isinstance(value, str) else ()
    rows: list[dict[str, Any]] = []
    for packet in packets:
        if not isinstance(packet, Mapping):
            continue
        rows.append({key: packet.get(key) for key in _PACKET_FIELDS if key in packet})
        if len(rows) >= limit:
            break
    return rows


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


__all__ = ["compact_agent_loop_output"]
