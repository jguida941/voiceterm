"""Queue-targeted agent-loop decisions for scoped packets without live rows."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.value_coercion import (
    coerce_mapping,
    coerce_text,
)
from ..runtime.review_packet_inbox_actionable import (
    is_actionable as _is_runtime_actionable_packet,
)
from ..runtime.review_packet_inbox_liveness import (
    is_live_pending as _is_live_pending_packet,
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


_KNOWN_PENDING_ACTORS = ("codex", "claude", "cursor", "operator")


def queue_target_decisions(
    *,
    review_state: Mapping[str, object],
    dashboard: Mapping[str, object],
    target_agent: str,
    seen_keys: set[tuple[str, str, str]],
) -> list[tuple[tuple[str, str, str], dict[str, object]]]:
    """Build decisions for scoped queue packets not present on the work-board.

    Two paths emit rows here:
    1. ``queue.derived_next_instruction_source.to_agent`` — set only for
       queue-selected packets that name an active next instruction.
    2. ``queue.pending_<actor>`` counters — broad pending counters only
       open a route scan. Rows are emitted for pending runtime-actionable
       packets only, so communication-only notices do not become loop wake debt.
    """
    decisions: list[tuple[tuple[str, str, str], dict[str, object]]] = []
    seen_local: set[tuple[str, str, str]] = set(seen_keys)

    route = _queue_target_route(review_state, target_agent=target_agent)
    if route:
        key = (route["actor_id"], route["role"], route["session_id"])
        if key not in seen_local:
            decision = _build_route_decision(
                review_state=review_state,
                dashboard=dashboard,
                route=route,
            )
            decisions.append((key, decision))
            seen_local.add(key)

    decisions.extend(
        _pending_packet_decisions(
            review_state=review_state,
            dashboard=dashboard,
            target_agent=target_agent,
            seen_keys=seen_local,
        )
    )
    return decisions


def _build_route_decision(
    *,
    review_state: Mapping[str, object],
    dashboard: Mapping[str, object],
    route: Mapping[str, str],
) -> dict[str, object]:
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
    return decision


def _pending_packet_decisions(
    *,
    review_state: Mapping[str, object],
    dashboard: Mapping[str, object],
    target_agent: str,
    seen_keys: set[tuple[str, str, str]],
) -> list[tuple[tuple[str, str, str], dict[str, object]]]:
    """Emit decisions for actors with pending inbox packets but no live row."""
    queue = coerce_mapping(review_state.get("queue"))
    decisions: list[tuple[tuple[str, str, str], dict[str, object]]] = []
    for actor_id in _KNOWN_PENDING_ACTORS:
        pending_count = _coerce_count(queue.get(f"pending_{actor_id}"))
        if pending_count <= 0:
            continue
        if target_agent and actor_id != target_agent:
            continue
        packet = _first_pending_runtime_actionable_packet_for_actor(
            review_state,
            actor_id,
        )
        if not packet:
            continue
        packet_id = coerce_text(packet.get("packet_id"))
        if not packet_id:
            continue
        role = _normalize_role(packet.get("target_role"))
        session_id = coerce_text(packet.get("target_session_id"))
        key = (actor_id, role, session_id)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        from ..runtime.agent_loop_decision import build_agent_loop_decision

        decision = build_agent_loop_decision(
            review_state=review_state,
            dashboard=dashboard,
            actor_id=actor_id,
            actor_role=role,
            session_id=session_id,
            requested_packet_id=packet_id,
        ).to_dict()
        decision["source_work_board_row"] = {
            "route_key": "|".join(key),
            "status": "queue_targeted_by_pending_count",
            "confidence_class": "queue_pending_count_inference",
            "source_event_id": coerce_text(packet.get("latest_event_id")),
            "source_surface": f"queue.pending_{actor_id}",
        }
        decisions.append((key, decision))
    return decisions


def _coerce_count(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _first_pending_runtime_actionable_packet_for_actor(
    review_state: Mapping[str, object],
    actor_id: str,
) -> Mapping[str, object] | None:
    """Return the first pending actionable packet routed to ``actor_id``."""
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return None
    for row in packets:
        if not isinstance(row, Mapping):
            continue
        if coerce_text(row.get("to_agent")) != actor_id:
            continue
        if not _is_live_pending_packet(row):
            continue
        if not _is_runtime_actionable_packet(row):
            continue
        return row
    return None


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
