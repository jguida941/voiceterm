"""Queue source rows for queue-targeted agent-loop decisions."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.value_coercion import coerce_mapping, coerce_text
from .agent_loop_decision_route_scope import normalize_role

QUEUE_SCOPED_PACKET = "queue_scoped_packet"


def queue_target_route(
    review_state: Mapping[str, object],
    *,
    target_agent: str,
) -> dict[str, str]:
    queue = coerce_mapping(review_state.get("queue"))
    source = coerce_mapping(queue.get("derived_next_instruction_source"))
    actor_id = coerce_text(source.get("to_agent"))
    if not actor_id or (target_agent and actor_id != target_agent):
        return {}
    role = normalize_role(source.get("target_role"))
    session_id = coerce_text(source.get("target_session_id"))
    packet_id = coerce_text(source.get("packet_id"))
    if not packet_id or not (role or session_id):
        return {}
    return {
        "actor_id": actor_id,
        "role": role,
        "session_id": session_id,
        "packet_id": packet_id,
        "source_event_id": packet_event_id(review_state, packet_id),
    }


def source_row(route: Mapping[str, str]) -> dict[str, object]:
    key = (route["actor_id"], route["role"], route["session_id"])
    return {
        "route_key": "|".join(key),
        "status": "queue_targeted",
        "confidence_class": QUEUE_SCOPED_PACKET,
        "source_event_id": route.get("source_event_id", ""),
        "source_surface": "queue.derived_next_instruction_source",
    }


def packet_event_id(review_state: Mapping[str, object], packet_id: str) -> str:
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return ""
    for row in packets:
        if not isinstance(row, Mapping):
            continue
        if coerce_text(row.get("packet_id")) == packet_id:
            return coerce_text(row.get("latest_event_id"))
    return ""
