"""Packet-body checks for peer-awareness boundaries."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .session_route_scope import packet_matches_session_route
from .session_termination_body import packet_body_observed_by_route
from .session_termination_pending import (
    packet_blocks_task_complete,
    packet_is_active_anchor,
    packet_sort_key,
)


def blocking_body_packet(
    packets: Sequence[object] | object,
    *,
    actor: str,
    actor_role: str,
    session_id: str,
    target_ref: str,
) -> Mapping[str, object] | None:
    rows = _packet_rows(packets)
    candidates = [
        packet
        for packet in rows
        if _packet_blocks_agent_message_boundary(packet)
        and packet_matches_session_route(
            packet,
            session_id=session_id,
            actor=actor,
            actor_role=actor_role,
            target_ref=target_ref,
        )
        and not packet_body_observed_by_route(
            packet,
            actor=actor,
            actor_role=actor_role,
            session_id=session_id,
        )
    ]
    return sorted(candidates, key=packet_sort_key, reverse=True)[0] if candidates else None


def _packet_blocks_agent_message_boundary(packet: Mapping[str, object]) -> bool:
    kind = _text(packet.get("kind"))
    if kind in {"stop_anchor", "continuation_anchor"}:
        return packet_is_active_anchor(packet)
    return packet_blocks_task_complete(packet) and packet_is_active_anchor(packet)


def _packet_rows(packets: Sequence[object] | object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(packets, Sequence) or isinstance(packets, (str, bytes)):
        return ()
    return tuple(packet for packet in packets if isinstance(packet, Mapping))


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["blocking_body_packet"]
