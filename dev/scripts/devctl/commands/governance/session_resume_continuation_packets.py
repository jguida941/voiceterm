"""Packet-position helpers for session-resume continuation state."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...runtime.review_state_models import PacketInboxState, ReviewState


def last_seen_packet_id(
    *,
    packet_inbox: "PacketInboxState | None",
    agent_id: str,
) -> str:
    if packet_inbox is None:
        return ""
    record = packet_inbox.for_agent(agent_id)
    if record is None:
        return ""
    return (
        record.current_instruction_packet_id
        or record.latest_finding_packet_id
        or next(iter(record.pending_actionable_packet_ids), "")
        or next(iter(record.expired_unresolved_packet_ids), "")
    )


def last_acknowledged_packet_id(
    *,
    typed_review_state: "ReviewState | None",
    agent_id: str,
) -> str:
    if typed_review_state is None:
        return ""
    agent_key = str(agent_id or "").strip().lower()
    latest_sort_key = ""
    latest_packet_id = ""
    for packet in getattr(typed_review_state, "packets", ()) or ():
        packet_id = str(getattr(packet, "packet_id", "") or "").strip()
        if not packet_id:
            continue
        ack_key = _packet_ack_sort_key(packet, agent_key=agent_key)
        if ack_key and ack_key >= latest_sort_key:
            latest_sort_key = ack_key
            latest_packet_id = packet_id
    return latest_packet_id


def _packet_ack_sort_key(packet: object, *, agent_key: str) -> str:
    acked_by = str(getattr(packet, "acked_by", "") or "").strip().lower()
    if agent_key and acked_by == agent_key:
        return str(getattr(packet, "acked_at_utc", "") or "").strip() or " "
    latest = ""
    for event in getattr(packet, "acknowledged_events", ()) or ():
        if not isinstance(event, dict):
            continue
        by_agent = str(event.get("by_agent") or event.get("actor") or "").lower()
        if agent_key and by_agent != agent_key:
            continue
        timestamp = str(event.get("timestamp_utc") or "").strip() or " "
        if timestamp >= latest:
            latest = timestamp
    return latest


__all__ = ["last_acknowledged_packet_id", "last_seen_packet_id"]
