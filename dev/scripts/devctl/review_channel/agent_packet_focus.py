"""Shared packet-focus projection for one actor scope."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ..runtime.review_packet_inbox_actionable import attention_urgency
from ..runtime.value_coercion import coerce_mapping as _mapping
from ..runtime.value_coercion import coerce_text as _text
from .active_packet_authority import current_active_packet_for_agent
from .event_models import event_id_rank as _event_id_rank
from .agent_sync_models import ACTIVE_LIFECYCLE_STATES
from .packet_contract import normalize_packet_route_role


_FOCUSABLE_LIFECYCLE_STATES = ACTIVE_LIFECYCLE_STATES | frozenset(
    {
        "delivery_pending",
        "execution_pending",
        "apply_pending_after_execution",
        "acknowledged",
        "pending",
        "in_progress",
        "task_started",
        "task_progress",
        "task_produced",
        "task_blocked",
        "operator_routed",
    }
)


@dataclass(frozen=True, slots=True)
class AgentPacketFocus:
    """Read model for active, attention, and executing packet focus."""

    contract_id: str = "AgentPacketFocus"
    schema_version: int = 1
    active_packet_id: str = ""
    attention_packet_id: str = ""
    executing_packet_id: str = ""
    legacy_unscoped_packet_id: str = ""
    active_packet: Mapping[str, object] = field(default_factory=dict)
    attention_packet: Mapping[str, object] = field(default_factory=dict)
    executing_packet: Mapping[str, object] = field(default_factory=dict)
    source_contracts: tuple[str, ...] = (
        "ActivePacketAuthority",
        "AgentWorkBoardProjection",
        "PacketAttention",
    )


def packet_focus_for_agent(
    review_state: Mapping[str, object],
    *,
    actor: str,
    role: str,
    session: str,
    attention: Mapping[str, object],
) -> AgentPacketFocus:
    """Return the typed packet focus for one actor/role/session scope."""
    active = current_active_packet_for_agent(
        review_state,
        actor,
        target_role=role,
        target_session_id=session,
    )
    if not _packet_id_is_focusable(review_state, active):
        active = ""
    work_row = _work_board_row_for_scope(
        review_state,
        actor=actor,
        role=role,
        session=session,
        active_packet_id=active,
    )
    selected_attention_id = _text(attention.get("latest_attention_packet_id"))
    body_open_attention_id = (
        _text(attention.get("body_open_packet_id"))
        if attention.get("body_open_required")
        else ""
    )
    default_attention_id = (
        _text(work_row.get("attention_packet_id"))
        or active
        or selected_attention_id
    )
    explicit_work_board_attention = _text(work_row.get("attention_packet_id"))
    selected_preempts_default = _attention_packet_preempts(
        review_state,
        selected_attention_id,
        default_attention_id,
    )
    attention_id = body_open_attention_id or (
        selected_attention_id
        if selected_preempts_default
        else explicit_work_board_attention or default_attention_id
    )
    executing = _text(work_row.get("executing_packet_id"))
    if not _packet_id_is_focusable(review_state, attention_id):
        attention_id = ""
    if not _packet_id_is_focusable(review_state, executing):
        executing = ""
    active_packet = packet_by_id(review_state, active)
    legacy_unscoped = ""
    if _role_is_observer(role) and active and not _text(active_packet.get("target_role")):
        legacy_unscoped = active
        active = ""
        attention_id = ""
        executing = ""
        active_packet = {}
    return AgentPacketFocus(
        active_packet_id=active,
        attention_packet_id=attention_id,
        executing_packet_id=executing,
        legacy_unscoped_packet_id=legacy_unscoped,
        active_packet=active_packet,
        attention_packet=packet_by_id(review_state, attention_id),
        executing_packet=packet_by_id(review_state, executing),
    )


def packet_by_id(
    review_state: Mapping[str, object],
    packet_id: str,
) -> Mapping[str, object]:
    packets = review_state.get("packets")
    if not packet_id or not isinstance(packets, (list, tuple)):
        return {}
    for packet in packets:
        if isinstance(packet, Mapping) and _text(packet.get("packet_id")) == packet_id:
            return packet
    return {}


def _packet_id_is_focusable(
    review_state: Mapping[str, object],
    packet_id: str,
) -> bool:
    if not packet_id:
        return False
    if not isinstance(review_state.get("packets"), (list, tuple)):
        return True
    return _packet_is_focusable(packet_by_id(review_state, packet_id))


def _packet_is_focusable(packet: Mapping[str, object]) -> bool:
    if not packet:
        return False
    lifecycle = _text(packet.get("lifecycle_current_state"))
    if lifecycle not in _FOCUSABLE_LIFECYCLE_STATES:
        return False
    status = _text(packet.get("status"))
    return status in {"", "pending", "acked", "acknowledged", "in_progress"}


def _attention_packet_preempts(
    review_state: Mapping[str, object],
    candidate_id: str,
    current_id: str,
) -> bool:
    if not candidate_id or candidate_id == current_id:
        return False
    candidate = packet_by_id(review_state, candidate_id)
    if not _packet_is_focusable(candidate):
        return False
    current = packet_by_id(review_state, current_id)
    if not _packet_is_focusable(current):
        return True
    return _attention_priority_key(candidate) > _attention_priority_key(current)


def _attention_priority_key(packet: Mapping[str, object]) -> tuple[int, int, int, int]:
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
        _event_id_rank(_text(packet.get("latest_event_id"))),
        kind_rank.get(_text(packet.get("kind")).lower(), 0),
    )


def _work_board_row_for_scope(
    review_state: Mapping[str, object],
    *,
    actor: str,
    role: str,
    session: str,
    active_packet_id: str,
) -> Mapping[str, object]:
    rows = _mapping(review_state.get("agent_work_board")).get("rows")
    if not isinstance(rows, list):
        return {}
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if _text(row.get("actor_id")) != actor:
            continue
        if role and normalize_packet_route_role(row.get("role")) != role:
            continue
        if session and _text(row.get("session_id")) != session:
            continue
        row_packets = {
            _text(row.get("active_packet_id")),
            _text(row.get("attention_packet_id")),
            _text(row.get("executing_packet_id")),
        }
        if active_packet_id and active_packet_id not in row_packets:
            continue
        return row
    return {}


def _role_is_observer(role: str) -> bool:
    return role in {"dashboard", "observer", "operator"}


__all__ = [
    "AgentPacketFocus",
    "packet_by_id",
    "packet_focus_for_agent",
]
