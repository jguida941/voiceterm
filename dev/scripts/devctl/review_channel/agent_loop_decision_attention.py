"""Attention disambiguation helpers for agent-loop decision projections."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.value_coercion import (
    coerce_mapping as _mapping,
    coerce_text as _text,
)


def apply_scoped_attention_to_ambiguous_packet_attention(
    review_state: Mapping[str, object],
) -> dict[str, object]:
    """Make global ambiguous packet attention reflect scoped wake pressure."""
    runtime = _mapping(review_state.get("reviewer_runtime"))
    attention = _mapping(runtime.get("packet_attention"))
    if _text(attention.get("observation_actor_id")):
        return dict(review_state)
    wake_rows = [
        row
        for row in _decision_rows(review_state)
        if bool(row.get("wake_required")) or _int(row.get("pending_packet_count")) > 0
    ]
    if not wake_rows:
        return dict(review_state)

    selected = _latest_decision_row(wake_rows)
    queue = _mapping(review_state.get("queue"))
    pending_count = _int(queue.get("pending_total")) or sum(
        _int(row.get("pending_packet_count")) for row in wake_rows
    )
    updated_attention = dict(attention)
    updated_attention["latest_inbox_event_id"] = (
        _text(updated_attention.get("latest_inbox_event_id"))
        or _text(selected.get("latest_inbox_event_id"))
        or _text(selected.get("source_latest_event_id"))
    )
    updated_attention["latest_attention_packet_id"] = (
        _text(updated_attention.get("latest_attention_packet_id"))
        or _text(selected.get("attention_packet_id"))
        or _text(selected.get("active_packet_id"))
    )
    updated_attention["pending_packet_count"] = pending_count
    updated_attention["pivot_required"] = True
    updated_attention["wake_required"] = True
    updated_attention["stale_reason"] = "actor_identity_ambiguous_with_pending_wake"
    updated_attention["pivot_reasons"] = _merge_reasons(
        attention.get("pivot_reasons"),
        ("actor_identity_ambiguous", "scoped_agent_attention_pending"),
    )

    updated_runtime = dict(runtime)
    updated_runtime["packet_attention"] = updated_attention
    updated = dict(review_state)
    updated["reviewer_runtime"] = updated_runtime
    return updated


def apply_agent_sync_session_attention_disambiguation(
    review_state: Mapping[str, object],
) -> dict[str, object]:
    """Fail closed when an agent-level sync row hides session-level focus."""
    sync = _mapping(review_state.get("agent_sync"))
    agents = _mapping(sync.get("agents"))
    if not agents:
        return dict(review_state)

    decision_ids = _decision_packet_ids_by_actor(review_state)
    if not decision_ids:
        return dict(review_state)

    changed = False
    updated_agents: dict[str, object] = dict(agents)
    for actor_id, packet_ids in decision_ids.items():
        agent_row = agents.get(actor_id)
        if not isinstance(agent_row, Mapping):
            continue
        aggregate_attention = _text(agent_row.get("attention_packet_id"))
        if not _agent_attention_is_ambiguous(
            aggregate_attention=aggregate_attention,
            scoped_packet_ids=packet_ids,
        ):
            continue

        row = dict(agent_row)
        row["attention_packet_id"] = ""
        row["attention_scope_state"] = (
            "session_ambiguous" if len(packet_ids) > 1 else "session_scoped"
        )
        row["attention_scope_reason"] = (
            "session_scoped_routes_require_session_identity"
        )
        row["route_attention_packet_ids"] = list(packet_ids)
        updated_agents[actor_id] = row
        changed = True

    if not changed:
        return dict(review_state)

    updated_sync = dict(sync)
    updated_sync["agents"] = updated_agents
    updated = dict(review_state)
    updated["agent_sync"] = updated_sync
    return updated


def _decision_rows(
    review_state: Mapping[str, object],
) -> list[Mapping[str, object]]:
    rows = review_state.get("agent_loop_decisions")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, Mapping)]


def _decision_packet_ids_by_actor(
    review_state: Mapping[str, object],
) -> dict[str, tuple[str, ...]]:
    grouped: dict[str, list[tuple[int, str]]] = {}
    for row in _decision_rows(review_state):
        actor_id = _text(row.get("actor_id"))
        packet_id = _text(row.get("attention_packet_id")) or _text(
            row.get("active_packet_id")
        )
        if not actor_id or not packet_id:
            continue
        rank = max(
            _event_id_rank(_text(row.get("latest_inbox_event_id"))),
            _event_id_rank(_text(row.get("source_latest_event_id"))),
        )
        grouped.setdefault(actor_id, []).append((rank, packet_id))

    resolved: dict[str, tuple[str, ...]] = {}
    for actor_id, rows in grouped.items():
        seen: set[str] = set()
        packet_ids: list[str] = []
        for _rank, packet_id in sorted(rows, reverse=True):
            if packet_id in seen:
                continue
            seen.add(packet_id)
            packet_ids.append(packet_id)
        if packet_ids:
            resolved[actor_id] = tuple(packet_ids)
    return resolved


def _agent_attention_is_ambiguous(
    *,
    aggregate_attention: str,
    scoped_packet_ids: tuple[str, ...],
) -> bool:
    if not scoped_packet_ids:
        return False
    if len(scoped_packet_ids) > 1:
        return bool(aggregate_attention)
    return bool(aggregate_attention and aggregate_attention not in scoped_packet_ids)


def _latest_decision_row(
    rows: list[Mapping[str, object]],
) -> Mapping[str, object]:
    return max(
        rows,
        key=lambda row: (
            _event_id_rank(_text(row.get("latest_inbox_event_id"))),
            _event_id_rank(_text(row.get("source_latest_event_id"))),
            _text(row.get("attention_packet_id")) or _text(row.get("active_packet_id")),
        ),
    )


def _merge_reasons(existing: object, required: tuple[str, ...]) -> list[str]:
    reasons: list[str] = []
    for value in tuple(existing or ()) + required:
        text = _text(value)
        if text and text not in reasons:
            reasons.append(text)
    return reasons


def _event_id_rank(event_id: str) -> int:
    from .event_models import event_id_rank

    return event_id_rank(event_id)


def _int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        return int(_text(value))
    except ValueError:
        return 0
