"""Route visibility helpers for actor-scoped packet attention."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.review_packet_inbox_actionable import attention_urgency
from ..runtime.session_termination_policy import SESSION_TERMINATION_PACKET_KINDS
from ..runtime.value_coercion import coerce_text as _text
from .agent_sync_models import ACTIVE_LIFECYCLE_STATES
from .packet_contract import packet_route_matches_scope
from .packet_loop_attention import packet_requires_runtime_attention
from .packet_terminal_lifecycle_states import TERMINAL_LIFECYCLE_STATES

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


def pending_packets_for_scope(
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
        if not packet_matches_attention_scope(packet, role=role, session=session):
            continue
        if pending_packet_visible_to_route(
            packet,
            actor=actor,
            role=role,
            session=session,
        ):
            rows.append(packet)
    if not rows and role in {"dashboard", "operator"}:
        rows.extend(
            pending_packets_for_ambiguous_actor_scope(
                packet_rows,
                actor=actor,
                session=session,
                observer_role=role,
            )
        )
    return tuple(rows)


def pending_packets_for_ambiguous_actor_scope(
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
        if pending_packet_visible_to_route(
            packet,
            actor=actor,
            role=observer_role,
            session=session,
        ):
            rows.append(packet)
    return tuple(rows)


def packet_matches_attention_scope(
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


def pending_packet_visible_to_route(
    packet: Mapping[str, object],
    *,
    actor: str,
    role: str,
    session: str,
) -> bool:
    if _text(packet.get("kind")) in SESSION_TERMINATION_PACKET_KINDS:
        return False
    lifecycle = _text(packet.get("lifecycle_current_state"))
    if lifecycle in TERMINAL_LIFECYCLE_STATES:
        return False
    if observer_legacy_action_request(packet, role=role):
        return False
    status = _text(packet.get("status"))
    if status not in {"", "pending"} or lifecycle not in _PENDING_LIFECYCLES:
        return False
    return packet_requires_runtime_attention(
        packet,
        actor=actor,
        role=role,
        session=session,
    )


def active_packet_visible_to_route(
    packet: Mapping[str, object],
    *,
    actor: str,
    role: str,
    session: str,
) -> bool:
    if not packet:
        return False
    if observer_legacy_action_request(packet, role=role):
        return False
    lifecycle = _text(packet.get("lifecycle_current_state"))
    if lifecycle not in ACTIVE_LIFECYCLE_STATES:
        return False
    status = _text(packet.get("status"))
    if status not in {"", "pending", "acked", "acknowledged", "in_progress"}:
        return False
    return packet_requires_runtime_attention(
        packet,
        actor=actor,
        role=role,
        session=session,
    )


def observer_legacy_action_request(
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
