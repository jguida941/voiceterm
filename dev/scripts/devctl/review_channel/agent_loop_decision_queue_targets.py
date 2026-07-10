"""Queue-targeted agent-loop decisions for scoped packets without live rows."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from ..runtime.value_coercion import (
    coerce_mapping,
    coerce_text,
)
from .agent_sync_readers import agent_sync_pending_packet_ids
from .agent_loop_decision_queue_source import queue_target_route, source_row
from .agent_loop_decision_route_scope import (
    coerce_count,
    first_pending_loop_attention_packet_for_actor,
    normalize_role,
    role_for_packet,
)


_KNOWN_PENDING_ACTORS = ("codex", "claude", "cursor", "operator")
RouteDecisionConfidenceClass = Literal[
    "agent_sync_pending_packet_inference",
    "queue_pending_count_inference",
    "queue_scoped_packet",
]

AGENT_SYNC_PENDING_PACKET_INFERENCE: RouteDecisionConfidenceClass = (
    "agent_sync_pending_packet_inference"
)
QUEUE_PENDING_COUNT_INFERENCE: RouteDecisionConfidenceClass = (
    "queue_pending_count_inference"
)


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
    2. ``agent_sync.agents[actor].pending_packets_to_me`` and legacy
       ``queue.pending_<actor>`` counters open a route scan. Rows are emitted
       for pending loop-attention packets, so typed findings wake the target
       actor while operator review-only notices remain receipt-only.
    """
    decisions: list[tuple[tuple[str, str, str], dict[str, object]]] = []
    seen_local: set[tuple[str, str, str]] = set(seen_keys)

    route = queue_target_route(review_state, target_agent=target_agent)
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
    decision["source_work_board_row"] = source_row(route)
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
        pending_packet_ids = agent_sync_pending_packet_ids(review_state, actor_id)
        pending_count = coerce_count(queue.get(f"pending_{actor_id}")) or len(
            pending_packet_ids
        )
        if pending_count <= 0:
            continue
        if target_agent and actor_id != target_agent:
            continue
        packet = first_pending_loop_attention_packet_for_actor(
            review_state,
            actor_id,
            packet_ids=pending_packet_ids,
        )
        if not packet:
            continue
        packet_id = coerce_text(packet.get("packet_id"))
        if not packet_id:
            continue
        role = role_for_packet(actor_id, packet)
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
            "confidence_class": AGENT_SYNC_PENDING_PACKET_INFERENCE
            if pending_packet_ids
            else QUEUE_PENDING_COUNT_INFERENCE,
            "source_event_id": coerce_text(packet.get("latest_event_id")),
            "source_surface": "agent_sync.pending_packets_to_me"
            if pending_packet_ids
            else f"queue.pending_{actor_id}",
        }
        decisions.append((key, decision))
    return decisions


def _normalize_role(value: object) -> str:
    return normalize_role(value)
