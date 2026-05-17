"""Pending review-packet resolution helpers for the control plane."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def resolve_pending_packets(review_state: dict[str, Any] | None) -> int:
    """Count live pending action_request packets from review state."""
    if review_state is None:
        return 0
    packets = review_state.get("packets", [])
    if not isinstance(packets, list):
        return 0
    return sum(
        1
        for packet in packets
        if _is_live_pending_action_request(packet, packets)
    )


def _is_live_pending_action_request(
    packet: object,
    packets: list[dict[str, Any]],
) -> bool:
    if not isinstance(packet, dict):
        return False
    if _packet_text(packet.get("kind")) != "action_request":
        return False
    return _is_live_pending_packet(packet, packets)


def _is_live_pending_packet(
    packet: object,
    packets: list[dict[str, Any]],
) -> bool:
    if not isinstance(packet, dict):
        return False
    status = _packet_text(packet.get("status"))
    if status != "pending":
        return False
    if _is_resolved_commit_approval_request(packet, packets):
        return False
    expires_at = _parse_utc_stamp(packet.get("expires_at_utc"))
    if expires_at is not None and expires_at <= datetime.now(timezone.utc):
        return False
    return True


def _is_resolved_commit_approval_request(
    packet: dict[str, Any],
    packets: list[dict[str, Any]],
) -> bool:
    if _packet_text(packet.get("kind")) != "commit_approval":
        return False
    if not bool(packet.get("approval_required")):
        return False
    key = _packet_resolution_key(packet)
    if not any(key):
        return False
    for other in packets:
        if not isinstance(other, dict):
            continue
        if _packet_text(other.get("status")) != "applied":
            continue
        if bool(other.get("approval_required")):
            continue
        if _packet_text(other.get("kind")) != "commit_approval":
            continue
        if _packet_resolution_key(other) == key:
            return True
    return False


def _packet_resolution_key(packet: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        _packet_text(packet.get("trace_id")),
        _packet_text(packet.get("kind")),
        _packet_text(packet.get("target_ref")),
        _packet_text(packet.get("pipeline_generation")),
    )


def _packet_text(value: object) -> str:
    return str(value or "").strip()


def _parse_utc_stamp(value: object) -> datetime | None:
    text = _packet_text(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
