"""Pending packet selectors for session termination policy."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .packet_transport_expiry import packet_transport_expired
from .session_route_scope import packet_matches_session_route

TASK_COMPLETE_BLOCKING_PACKET_KINDS = frozenset(
    {
        "action_request",
        "approval_request",
        "instruction",
    }
)


def active_pending_review_packet(
    packets: Sequence[Mapping[str, object]],
    *,
    session_id: str,
    actor: str,
    actor_role: str,
    target_ref: str,
) -> Mapping[str, object] | None:
    candidates = [
        packet
        for packet in packets
        if packet_blocks_task_complete(packet)
        and packet_is_active_anchor(packet)
        and packet_matches_session_route(
            packet,
            session_id=session_id,
            actor=actor,
            actor_role=actor_role,
            target_ref=target_ref,
        )
    ]
    return sorted(candidates, key=packet_sort_key, reverse=True)[0] if candidates else None


def packet_blocks_task_complete(packet: Mapping[str, object]) -> bool:
    kind = _text(packet.get("kind"))
    return kind.startswith("review_") or kind in TASK_COMPLETE_BLOCKING_PACKET_KINDS


def packet_is_active_anchor(packet: Mapping[str, object]) -> bool:
    if packet_transport_expired(packet):
        return False
    status = _text(packet.get("status"))
    lifecycle = _text(packet.get("lifecycle_current_state"))
    if status in {"applied", "archived", "dismissed", "expired"}:
        return False
    return lifecycle not in {"applied", "archived", "dismissed", "expired"}


def packet_sort_key(packet: Mapping[str, object]) -> tuple[str, str, str]:
    return (
        _text(packet.get("posted_at")),
        _text(packet.get("latest_event_id")),
        _text(packet.get("packet_id")),
    )


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()
