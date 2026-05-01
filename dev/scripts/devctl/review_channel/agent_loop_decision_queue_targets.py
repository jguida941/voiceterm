"""Queue-targeted agent-loop decisions for scoped packets without live rows."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.value_coercion import (
    coerce_mapping,
    coerce_text,
)

_ROLE_ALIASES = {
    "coder": "implementer",
    "coding": "implementer",
    "implementation": "implementer",
    "implementer": "implementer",
    "review": "reviewer",
    "reviewer": "reviewer",
    "dashboard": "dashboard",
    "observer": "dashboard",
    "operator": "operator",
}


def queue_target_decisions(
    *,
    review_state: Mapping[str, object],
    dashboard: Mapping[str, object],
    target_agent: str,
    seen_keys: set[tuple[str, str, str]],
) -> list[tuple[tuple[str, str, str], dict[str, object]]]:
    """Build decisions for scoped queue packets not present on the work-board."""
    route = _queue_target_route(review_state, target_agent=target_agent)
    if not route:
        return []
    key = (
        route["actor_id"],
        route["role"],
        route["session_id"],
    )
    if key in seen_keys:
        return []
    from ..runtime.agent_loop_decision import build_agent_loop_decision

    decision = build_agent_loop_decision(
        review_state=review_state,
        dashboard=dashboard,
        actor_id=route["actor_id"],
        actor_role=route["role"],
        session_id=route["session_id"],
        requested_packet_id=route["packet_id"],
    ).to_dict()
    decision["source_work_board_row"] = _source_row(route)
    return [(key, decision)]


def _queue_target_route(
    review_state: Mapping[str, object],
    *,
    target_agent: str,
) -> dict[str, str]:
    queue = coerce_mapping(review_state.get("queue"))
    source = coerce_mapping(queue.get("derived_next_instruction_source"))
    actor_id = coerce_text(source.get("to_agent"))
    if not actor_id or (target_agent and actor_id != target_agent):
        return {}
    role = _normalize_role(source.get("target_role"))
    session_id = coerce_text(source.get("target_session_id"))
    packet_id = coerce_text(source.get("packet_id"))
    if not packet_id or not (role or session_id):
        return {}
    return {
        "actor_id": actor_id,
        "role": role,
        "session_id": session_id,
        "packet_id": packet_id,
        "source_event_id": _packet_event_id(review_state, packet_id),
    }


def _source_row(route: Mapping[str, str]) -> dict[str, object]:
    key = (route["actor_id"], route["role"], route["session_id"])
    return {
        "route_key": "|".join(key),
        "status": "queue_targeted",
        "confidence_class": "queue_scoped_packet",
        "source_event_id": route.get("source_event_id", ""),
        "source_surface": "queue.derived_next_instruction_source",
    }


def _packet_event_id(review_state: Mapping[str, object], packet_id: str) -> str:
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return ""
    for row in packets:
        if not isinstance(row, Mapping):
            continue
        if coerce_text(row.get("packet_id")) == packet_id:
            return coerce_text(row.get("latest_event_id"))
    return ""


def _normalize_role(value: object) -> str:
    role = coerce_text(value)
    if not role:
        return ""
    key = role.lower().replace("-", "_").replace(" ", "_")
    return _ROLE_ALIASES.get(key, key)
