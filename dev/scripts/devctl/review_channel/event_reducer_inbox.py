"""Inbox/history query helpers for reduced event-backed review state."""

from __future__ import annotations

from ..runtime.review_packet_inbox_liveness import is_expired_unresolved

from .packet_contract import packet_route_matches_scope
from .pending_packets import live_pending_packets, partition_live_packet_queue
from .timestamp_parse import parse_utc_value as _parse_utc


def filter_inbox_packets(
    review_state: dict[str, object],
    *,
    target: str | None = None,
    target_role: str | None = None,
    target_session_id: str | None = None,
    status: str | None = None,
    limit: int | None = None,
) -> list[dict[str, object]]:
    """Filter the reduced packet list into one target/status inbox view.

    When filtering by status=pending, expired packets are excluded so the
    inbox matches pending_total, per-agent counts, and derived_next_instruction.
    """
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return []
    filtered = []
    packet_iter = live_pending_packets(packets) if status == "pending" else (
        packet for packet in packets if isinstance(packet, dict)
    )
    for packet in packet_iter:
        if target and packet.get("to_agent") != target:
            continue
        if target_role or target_session_id:
            if not _packet_has_route_scope(packet):
                continue
            if not packet_route_matches_scope(
                packet,
                target_role=target_role,
                target_session_id=target_session_id,
            ):
                continue
        if status and not _packet_matches_inbox_status(packet, status):
            continue
        filtered.append(packet)
    if limit is not None and limit >= 0:
        return filtered[:limit]
    return filtered


def filter_history_packets(
    review_state: dict[str, object],
    *,
    target: str | None = None,
    packet_id: str | None = None,
    limit: int | None = None,
) -> list[dict[str, object]]:
    """Filter the reduced packet list into one packet-history view."""
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return []
    requested_packet_id = str(packet_id or "").strip()
    if requested_packet_id:
        packet = packet_by_id(review_state, requested_packet_id)
        if packet is None:
            return []
        if target and packet.get("to_agent") != target:
            return []
        return [packet]
    _, history_packets, _ = partition_live_packet_queue(
        packet for packet in packets if isinstance(packet, dict)
    )
    filtered = []
    for packet in history_packets:
        if not isinstance(packet, dict):
            continue
        if target and packet.get("to_agent") != target:
            continue
        filtered.append(packet)
    if limit is not None and limit >= 0:
        return filtered[:limit]
    return filtered


def filter_history_events(
    events: list[dict[str, object]],
    *,
    trace_id: str | None = None,
    packet_id: str | None = None,
    limit: int | None = None,
) -> list[dict[str, object]]:
    """Filter the append-only event log into one history view."""
    requested_packet_id = str(packet_id or "").strip()
    filtered = [
        event
        for event in events
        if not trace_id or event.get("trace_id") == trace_id
        if not requested_packet_id or event.get("packet_id") == requested_packet_id
    ]
    if limit is not None and limit >= 0:
        return filtered[-limit:]
    return filtered


def packet_by_id(
    review_state: dict[str, object],
    packet_id: str,
) -> dict[str, object] | None:
    """Look up one packet in the reduced state."""
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return None
    for packet in packets:
        if isinstance(packet, dict) and packet.get("packet_id") == packet_id:
            return packet
    return None


def _packet_matches_inbox_status(packet: dict[str, object], status: str) -> bool:
    if status == "expired":
        return is_expired_unresolved(packet)
    return packet.get("status") == status


def _packet_has_route_scope(packet: dict[str, object]) -> bool:
    return bool(packet.get("target_role") or packet.get("target_session_id"))
