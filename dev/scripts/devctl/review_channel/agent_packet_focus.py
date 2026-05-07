"""Shared packet-focus projection for one actor scope."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ..runtime.value_coercion import coerce_mapping as _mapping
from ..runtime.value_coercion import coerce_text as _text
from .active_packet_authority import current_active_packet_for_agent
from .agent_sync_models import ACTIVE_LIFECYCLE_STATES
from .packet_contract import normalize_packet_route_role


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
    attention_id = (
        _text(work_row.get("attention_packet_id"))
        or active
        or _text(attention.get("latest_attention_packet_id"))
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
    if lifecycle not in ACTIVE_LIFECYCLE_STATES:
        return False
    status = _text(packet.get("status"))
    return status in {"", "pending", "acked", "acknowledged", "in_progress"}


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
