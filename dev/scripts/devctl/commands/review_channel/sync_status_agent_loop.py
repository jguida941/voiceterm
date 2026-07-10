"""Sync-status helpers for agent loop and route-scoped attention output."""

from __future__ import annotations

from ...review_channel.event_models import event_id_rank as _event_id_rank
from ...review_channel.agent_loop_decision_projection import (
    agent_loop_decisions_for_work_board,
)
from ...runtime.value_coercion import coerce_int as _coerce_int


def canonical_active_packets_for_sync_status(
    *,
    review_state: dict[str, object],
    agent_ids: dict[str, object],
    route_rows: list[dict[str, object]],
) -> dict[str, str]:
    """Collapse route-level active packets only when the agent is unambiguous."""
    from ...review_channel.active_packet_authority import (
        current_active_packet_for_agent,
    )

    route_ids = _active_route_ids_by_actor(route_rows)
    canonical: dict[str, str] = {}
    for agent_id in agent_ids:
        ids = route_ids.get(str(agent_id), ())
        if len(ids) == 1:
            canonical[str(agent_id)] = ids[0]
        elif len(ids) > 1:
            canonical[str(agent_id)] = ""
        else:
            canonical[str(agent_id)] = current_active_packet_for_agent(
                review_state, str(agent_id)
            )
    return canonical


def canonical_active_packet_ambiguity(
    route_rows: list[dict[str, object]],
) -> dict[str, object]:
    ambiguous: dict[str, object] = {}
    route_ids = _active_route_ids_by_actor(route_rows)
    for actor_id, ids in route_ids.items():
        if len(ids) <= 1:
            continue
        ambiguous[actor_id] = {
            "scope_state": "session_ambiguous",
            "route_attention_packet_ids": list(ids),
        }
    return ambiguous


def apply_route_attention_scope_to_agents(
    agents_block: dict[str, object],
    *,
    route_rows: list[dict[str, object]],
) -> dict[str, object]:
    route_ids = _active_route_ids_by_actor(route_rows)
    if not route_ids:
        return agents_block
    updated: dict[str, object] = dict(agents_block)
    for actor_id, ids in route_ids.items():
        row = agents_block.get(actor_id)
        if not isinstance(row, dict):
            continue
        attention = str(row.get("attention_packet_id") or "").strip()
        ambiguous = len(ids) > 1 or bool(attention and attention not in ids)
        if not ambiguous:
            continue
        scoped = dict(row)
        scoped["attention_packet_id"] = ""
        scoped["attention_scope_state"] = (
            "session_ambiguous" if len(ids) > 1 else "session_scoped"
        )
        scoped["attention_scope_reason"] = (
            "session_scoped_routes_require_session_identity"
        )
        scoped["route_attention_packet_ids"] = list(ids)
        updated[actor_id] = scoped
    return updated


def packet_attention_for_sync_status(
    review_state: dict[str, object],
    *,
    target_agent: str,
    agent_loop_decisions: list[dict[str, object]],
) -> dict[str, object]:
    attention = extract_reviewer_runtime_field(review_state, "packet_attention")
    if not target_agent:
        return attention

    rows = [
        row
        for row in agent_loop_decisions
        if str(row.get("actor_id") or "").strip() == target_agent
        and (
            str(row.get("attention_packet_id") or "").strip()
            or str(row.get("active_packet_id") or "").strip()
        )
    ]
    if not rows:
        return attention

    packet_ids = _decision_attention_packet_ids(rows)
    sessions = _decision_session_ids(rows)
    updated = dict(attention)
    updated["observation_actor_id"] = target_agent
    updated["pending_packet_count"] = _target_pending_packet_count(
        review_state=review_state,
        target_agent=target_agent,
        rows=rows,
    )
    updated["wake_required"] = any(bool(row.get("wake_required")) for row in rows)
    updated["pivot_required"] = any(bool(row.get("pivot_required")) for row in rows)
    latest_inbox_event_id = _latest_decision_inbox_event_id(rows)
    updated["latest_inbox_event_id"] = latest_inbox_event_id
    if len(packet_ids) == 1 and len(sessions) <= 1:
        selected = rows[0]
        updated["latest_attention_packet_id"] = packet_ids[0]
        updated["observation_session_id"] = str(
            selected.get("session_id") or ""
        ).strip()
        updated["scope_state"] = (
            "session_scoped"
            if str(selected.get("session_id") or "").strip()
            else "actor_scoped"
        )
        if updated["wake_required"]:
            updated["stale_reason"] = "wake_required"
        return updated

    updated["latest_attention_packet_id"] = ""
    updated["observation_session_id"] = ""
    updated["scope_state"] = "session_ambiguous"
    updated["stale_reason"] = "session_identity_ambiguous_with_pending_wake"
    updated["scoped_attention_packet_ids"] = list(packet_ids)
    updated["scoped_session_ids"] = list(sessions)
    updated["pivot_reasons"] = _merge_reasons(
        updated.get("pivot_reasons"),
        ("session_identity_ambiguous", "scoped_session_attention_pending"),
    )
    return updated


def inbox_observation_for_sync_status(
    review_state: dict[str, object],
    *,
    target_agent: str,
    agent_loop_decisions: list[dict[str, object]],
) -> dict[str, object]:
    observation = extract_reviewer_runtime_field(review_state, "inbox_observation")
    if not target_agent:
        return observation
    rows = [
        row
        for row in agent_loop_decisions
        if str(row.get("actor_id") or "").strip() == target_agent
    ]
    if not rows:
        return observation

    pending_count = _target_pending_packet_count(
        review_state=review_state,
        target_agent=target_agent,
        rows=rows,
    )
    event_id = _latest_decision_event_id(rows)
    observed_event_id = str(observation.get("last_inbox_observed_event_id") or "")
    sessions = _decision_session_ids(rows)
    updated = dict(observation)
    updated["actor_id"] = target_agent
    updated["session_id"] = sessions[0] if len(sessions) == 1 else ""
    updated["last_inbox_event_id"] = event_id
    updated["pending_packet_count"] = pending_count
    updated["pivot_required"] = bool(
        pending_count > 0 or (event_id and event_id != observed_event_id)
    )
    updated["pivot_reasons"] = _inbox_pivot_reasons(
        pending_count=pending_count,
        event_id=event_id,
        observed_event_id=observed_event_id,
        session_count=len(sessions),
    )
    if len(sessions) > 1:
        updated["scope_state"] = "session_ambiguous"
        updated["scoped_session_ids"] = list(sessions)
    elif sessions:
        updated["scope_state"] = "session_scoped"
    else:
        updated["scope_state"] = "actor_scoped"
    return updated


def extract_reviewer_runtime_field(
    review_state: object, field_name: str
) -> dict[str, object]:
    """Return one reviewer_runtime field as a plain dict when present."""
    if not isinstance(review_state, dict):
        return {}
    reviewer_runtime = review_state.get("reviewer_runtime")
    if not isinstance(reviewer_runtime, dict):
        return {}
    payload = reviewer_runtime.get(field_name)
    return dict(payload) if isinstance(payload, dict) else {}


def _target_pending_packet_count(
    *,
    review_state: dict[str, object],
    target_agent: str,
    rows: list[dict[str, object]],
) -> int:
    agents = (review_state.get("agent_sync") or {}).get("agents") if isinstance(
        review_state.get("agent_sync"), dict
    ) else {}
    agent_row = agents.get(target_agent) if isinstance(agents, dict) else {}
    pending = (
        agent_row.get("pending_packets_to_me")
        if isinstance(agent_row, dict)
        else None
    )
    if isinstance(pending, list):
        return len({str(packet_id) for packet_id in pending if str(packet_id)})
    return max((_coerce_int(row.get("pending_packet_count")) for row in rows), default=0)


def _latest_decision_event_id(rows: list[dict[str, object]]) -> str:
    ranked: list[tuple[int, str]] = []
    for row in rows:
        event_id = str(row.get("latest_inbox_event_id") or "").strip() or str(
            row.get("source_latest_event_id") or ""
        ).strip()
        if event_id:
            ranked.append((_event_id_rank(event_id), event_id))
    if not ranked:
        return ""
    ranked.sort(reverse=True)
    return ranked[0][1]


def _latest_decision_inbox_event_id(rows: list[dict[str, object]]) -> str:
    ranked: list[tuple[int, str]] = []
    for row in rows:
        event_id = str(row.get("latest_inbox_event_id") or "").strip()
        if event_id:
            ranked.append((_event_id_rank(event_id), event_id))
    if not ranked:
        return ""
    ranked.sort(reverse=True)
    return ranked[0][1]


def _decision_session_ids(rows: list[dict[str, object]]) -> tuple[str, ...]:
    sessions: list[str] = []
    for row in rows:
        session_id = str(row.get("session_id") or "").strip()
        if session_id and session_id not in sessions:
            sessions.append(session_id)
    return tuple(sessions)


def _inbox_pivot_reasons(
    *,
    pending_count: int,
    event_id: str,
    observed_event_id: str,
    session_count: int,
) -> list[str]:
    reasons: list[str] = []
    if event_id and event_id != observed_event_id:
        reasons.append("inbox_event_unobserved")
    if pending_count > 0:
        reasons.append("pending_packets_unconsumed")
    if session_count > 1:
        reasons.append("session_identity_ambiguous")
    return reasons


def _active_route_ids_by_actor(
    route_rows: list[dict[str, object]],
) -> dict[str, tuple[str, ...]]:
    grouped: dict[str, list[tuple[int, str]]] = {}
    for row in route_rows:
        actor_id = str(row.get("actor_id") or "").strip()
        packet_id = str(row.get("active_packet_id") or "").strip()
        if not actor_id or not packet_id:
            continue
        grouped.setdefault(actor_id, []).append(
            (_event_id_rank(str(row.get("source_event_id") or "")), packet_id)
        )
    resolved: dict[str, tuple[str, ...]] = {}
    for actor_id, rows in grouped.items():
        seen: set[str] = set()
        packet_ids: list[str] = []
        for _rank, packet_id in sorted(rows, reverse=True):
            if packet_id in seen:
                continue
            seen.add(packet_id)
            packet_ids.append(packet_id)
        resolved[actor_id] = tuple(packet_ids)
    return resolved


def _decision_attention_packet_ids(
    rows: list[dict[str, object]],
) -> tuple[str, ...]:
    ranked: list[tuple[int, str]] = []
    for row in rows:
        packet_id = str(row.get("attention_packet_id") or "").strip() or str(
            row.get("active_packet_id") or ""
        ).strip()
        if not packet_id:
            continue
        rank = max(
            _event_id_rank(str(row.get("latest_inbox_event_id") or "")),
            _event_id_rank(str(row.get("source_latest_event_id") or "")),
        )
        ranked.append((rank, packet_id))
    seen: set[str] = set()
    packet_ids: list[str] = []
    for _rank, packet_id in sorted(ranked, reverse=True):
        if packet_id in seen:
            continue
        seen.add(packet_id)
        packet_ids.append(packet_id)
    return tuple(packet_ids)


def _merge_reasons(existing: object, required: tuple[str, ...]) -> list[str]:
    reasons: list[str] = []
    for value in tuple(existing or ()) + required:
        text = str(value or "").strip()
        if text and text not in reasons:
            reasons.append(text)
    return reasons


__all__ = [
    "agent_loop_decisions_for_work_board",
    "apply_route_attention_scope_to_agents",
    "canonical_active_packet_ambiguity",
    "canonical_active_packets_for_sync_status",
    "extract_reviewer_runtime_field",
    "inbox_observation_for_sync_status",
    "packet_attention_for_sync_status",
]
