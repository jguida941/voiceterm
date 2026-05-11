"""Actor-scoped packet attention projection for agent-loop consumers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ..runtime.reviewer_runtime_models import (
    PacketAttentionState,
    build_packet_attention_state,
)
from ..runtime.review_packet_inbox_actionable import attention_urgency
from ..runtime.session_termination_policy import SESSION_TERMINATION_PACKET_KINDS
from ..runtime.value_coercion import coerce_mapping as _mapping
from ..runtime.value_coercion import coerce_text as _text
from .active_packet_authority import current_active_packet_for_agent
from .agent_packet_focus import packet_by_id
from .agent_sync_readers import (
    agent_sync_pending_packet_count_from_row,
    agent_sync_row_for_actor,
)
from .agent_sync_models import (
    ACTIVE_LIFECYCLE_STATES,
    TERMINAL_NON_SUCCESS_STATES,
    TERMINAL_SUCCESS_STATES,
)
from .event_models import event_id_rank
from .packet_contract import normalize_packet_route_role, packet_route_matches_scope


_TERMINAL_LIFECYCLE_STATES = (
    TERMINAL_NON_SUCCESS_STATES | TERMINAL_SUCCESS_STATES
)
_PENDING_LIFECYCLES = frozenset(
    {
        "",
        "pending",
        "delivery_pending",
        "execution_pending",
        "acknowledged",
        "in_progress",
        "apply_pending_after_execution",
        "task_started",
        "task_progress",
        "task_produced",
        "task_blocked",
        "operator_routed",
    }
)


@dataclass(frozen=True, slots=True)
class _AttentionBuildInput:
    actor: str
    session: str
    attention_packet: Mapping[str, object]
    pending_packets: tuple[Mapping[str, object], ...]
    fallback: Mapping[str, object]
    agent_sync: Mapping[str, object]
    packet_rows_authoritative: bool


def packet_attention_for_agent(
    review_state: Mapping[str, object],
    *,
    actor: str,
    role: str = "",
    session: str = "",
    fallback_attention: Mapping[str, object] | None = None,
) -> PacketAttentionState:
    """Return packet-attention state scoped to one requested actor."""
    actor_id = _text(actor)
    role_id = normalize_packet_route_role(role)
    session_id = _text(session)
    fallback = _matching_fallback_attention(
        fallback_attention,
        actor=actor_id,
        session=session_id,
    )
    if not actor_id:
        return _fallback_attention(session_id=session_id, fallback=fallback)

    packet_rows = _packet_rows(review_state)
    packet_rows_authoritative = isinstance(review_state.get("packets"), (list, tuple))
    pending_packets = _pending_packets_for_scope(
        packet_rows,
        actor=actor_id,
        role=role_id,
        session=session_id,
    )
    active_packet = _active_packet_for_scope(
        review_state,
        actor=actor_id,
        role=role_id,
        session=session_id,
    )
    if not _active_packet_visible_to_role(active_packet, role=role_id):
        active_packet = {}
    attention_packet = _best_attention_packet(
        active_packet=active_packet,
        pending_packets=pending_packets,
    )
    return _build_attention(
        _AttentionBuildInput(
            actor=actor_id,
            session=session_id,
            attention_packet=attention_packet,
            pending_packets=pending_packets,
            fallback=fallback,
            agent_sync=agent_sync_row_for_actor(review_state, actor_id),
            packet_rows_authoritative=packet_rows_authoritative,
        )
    )


def _fallback_attention(
    *,
    session_id: str,
    fallback: Mapping[str, object],
) -> PacketAttentionState:
    return build_packet_attention_state(
        observation_actor_id="",
        observation_session_id=session_id,
        latest_inbox_event_id=_text(fallback.get("latest_inbox_event_id")),
        latest_attention_packet_id=_text(fallback.get("latest_attention_packet_id")),
        latest_attention_changed_at_utc=_text(
            fallback.get("latest_attention_changed_at_utc")
        ),
        last_observed_event_id=_text(fallback.get("last_observed_event_id")),
        last_observed_at_utc=_text(fallback.get("last_observed_at_utc")),
        pending_packet_count=int(fallback.get("pending_packet_count") or 0),
        superseded_packet_id=_text(fallback.get("superseded_packet_id")),
    )


def _active_packet_for_scope(
    review_state: Mapping[str, object],
    *,
    actor: str,
    role: str,
    session: str,
) -> Mapping[str, object]:
    packet_id = current_active_packet_for_agent(
        review_state,
        actor,
        target_role=role,
        target_session_id=session,
    )
    return packet_by_id(review_state, packet_id)


def _build_attention(context: _AttentionBuildInput) -> PacketAttentionState:
    fallback = context.fallback
    attention_packet = context.attention_packet
    agent_sync = context.agent_sync
    last_observed = (
        _text(fallback.get("last_observed_event_id"))
        or _text(agent_sync.get("last_consumed_event_id_lower_bound"))
    )
    if context.packet_rows_authoritative:
        latest_event_id = _text(attention_packet.get("latest_event_id"))
        latest_attention_packet_id = _text(attention_packet.get("packet_id"))
        pending_packet_count = len(context.pending_packets)
        fallback_attention_changed_at = ""
        superseded_packet_id = ""
    else:
        latest_event_id = _latest_event_id(
            _text(attention_packet.get("latest_event_id")),
            _text(fallback.get("latest_inbox_event_id")),
        )
        latest_attention_packet_id = _text(attention_packet.get("packet_id")) or _text(
            fallback.get("latest_attention_packet_id")
        )
        pending_packet_count = len(
            context.pending_packets
        ) or agent_sync_pending_packet_count_from_row(agent_sync)
        fallback_attention_changed_at = _text(
            fallback.get("latest_attention_changed_at_utc")
        )
        superseded_packet_id = _text(fallback.get("superseded_packet_id"))
    return build_packet_attention_state(
        observation_actor_id=context.actor,
        observation_session_id=context.session,
        latest_inbox_event_id=latest_event_id,
        latest_attention_packet_id=latest_attention_packet_id,
        latest_attention_changed_at_utc=(
            _text(attention_packet.get("posted_at"))
            or _text(attention_packet.get("latest_event_at_utc"))
            or fallback_attention_changed_at
        ),
        last_observed_event_id=last_observed,
        last_observed_at_utc=_text(fallback.get("last_observed_at_utc")),
        pending_packet_count=pending_packet_count,
        superseded_packet_id=superseded_packet_id,
    )


def _packet_rows(review_state: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    packets = review_state.get("packets")
    if not isinstance(packets, (list, tuple)):
        return ()
    return tuple(packet for packet in packets if isinstance(packet, Mapping))


def _pending_packets_for_scope(
    packet_rows: tuple[Mapping[str, object], ...],
    *,
    actor: str,
    role: str,
    session: str,
) -> tuple[Mapping[str, object], ...]:
    rows: list[Mapping[str, object]] = []
    for packet in packet_rows:
        if _text(packet.get("to_agent")) != actor:
            continue
        if not _packet_matches_attention_scope(
            packet,
            role=role,
            session=session,
        ):
            continue
        if _pending_packet_visible_to_role(packet, role=role):
            rows.append(packet)
    if not rows and role in {"dashboard", "operator"}:
        rows.extend(
            _pending_packets_for_ambiguous_actor_scope(
                packet_rows,
                actor=actor,
                session=session,
                observer_role=role,
            )
        )
    return tuple(rows)


def _pending_packets_for_ambiguous_actor_scope(
    packet_rows: tuple[Mapping[str, object], ...],
    *,
    actor: str,
    session: str,
    observer_role: str,
) -> tuple[Mapping[str, object], ...]:
    rows: list[Mapping[str, object]] = []
    for packet in packet_rows:
        if _text(packet.get("to_agent")) != actor:
            continue
        packet_session = _text(packet.get("target_session_id"))
        if packet_session and session and packet_session != session:
            continue
        if not (_text(packet.get("target_role")) or packet_session):
            continue
        if _pending_packet_visible_to_role(packet, role=observer_role):
            rows.append(packet)
    return tuple(rows)


def _packet_matches_attention_scope(
    packet: Mapping[str, object],
    *,
    role: str,
    session: str,
) -> bool:
    if packet_route_matches_scope(
        packet,
        target_role=role,
        target_session_id=session,
    ):
        return True
    if attention_urgency(packet) not in {"urgent", "blocking"}:
        return False
    packet_session = _text(packet.get("target_session_id"))
    return bool(packet_session and session and packet_session == session)


def _pending_packet_visible_to_role(
    packet: Mapping[str, object],
    *,
    role: str,
) -> bool:
    if _text(packet.get("kind")) in SESSION_TERMINATION_PACKET_KINDS:
        return False
    lifecycle = _text(packet.get("lifecycle_current_state"))
    if lifecycle in _TERMINAL_LIFECYCLE_STATES:
        return False
    if _observer_legacy_action_request(packet, role=role):
        return False
    status = _text(packet.get("status"))
    return status in {"", "pending"} and lifecycle in _PENDING_LIFECYCLES


def _active_packet_visible_to_role(
    packet: Mapping[str, object],
    *,
    role: str,
) -> bool:
    if not packet:
        return False
    if _observer_legacy_action_request(packet, role=role):
        return False
    lifecycle = _text(packet.get("lifecycle_current_state"))
    if lifecycle not in ACTIVE_LIFECYCLE_STATES:
        return False
    status = _text(packet.get("status"))
    return status in {"", "pending", "acked", "acknowledged", "in_progress"}


def _best_attention_packet(
    *,
    active_packet: Mapping[str, object],
    pending_packets: tuple[Mapping[str, object], ...],
) -> Mapping[str, object]:
    candidates: list[tuple[tuple[int, int, int, int, int], Mapping[str, object]]] = []
    if active_packet:
        candidates.append(
            (
                _attention_priority_key(active_packet, source_rank=1, index=-1),
                active_packet,
            )
        )
    candidates.extend(
        (_attention_priority_key(packet, source_rank=0, index=index), packet)
        for index, packet in enumerate(pending_packets)
    )
    if not candidates:
        return {}
    candidates.sort(reverse=True, key=lambda row: row[0])
    return candidates[0][1]


def _attention_priority_key(
    packet: Mapping[str, object],
    *,
    source_rank: int,
    index: int,
) -> tuple[int, int, int, int, int]:
    urgency_rank = {"blocking": 5, "urgent": 4, "ambient": 0}
    command_lane_rank = {
        "action_request": 3,
        "instruction": 3,
        "approval_request": 3,
    }
    kind_rank = {
        "review_failed": 2,
        "finding": 2,
        "decision": 2,
        "task_progress": 1,
    }
    return (
        urgency_rank.get(attention_urgency(packet), 0),
        command_lane_rank.get(_text(packet.get("kind")).lower(), 0),
        event_id_rank(_text(packet.get("latest_event_id"))),
        kind_rank.get(_text(packet.get("kind")).lower(), 0) + source_rank,
        index,
    )


def _latest_event_id(*values: str) -> str:
    best = ""
    best_rank = -1
    for value in values:
        text = _text(value)
        rank = event_id_rank(text)
        if text and rank >= best_rank:
            best = text
            best_rank = rank
    return best


def _observer_legacy_action_request(
    packet: Mapping[str, object],
    *,
    role: str,
) -> bool:
    if role not in {"dashboard", "operator"}:
        return False
    if _text(packet.get("kind")) != "action_request":
        return False
    return not (
        _text(packet.get("target_role"))
        or _text(packet.get("target_session_id"))
    )


def _matching_fallback_attention(
    fallback_attention: Mapping[str, object] | None,
    *,
    actor: str,
    session: str,
) -> Mapping[str, object]:
    fallback = fallback_attention if isinstance(fallback_attention, Mapping) else {}
    observed_actor = _text(fallback.get("observation_actor_id"))
    observed_session = _text(fallback.get("observation_session_id"))
    if observed_actor and actor and observed_actor != actor:
        return {}
    if observed_session and session and observed_session != session:
        return {}
    if actor and not observed_actor:
        return {}
    return fallback


__all__ = ["packet_attention_for_agent"]
