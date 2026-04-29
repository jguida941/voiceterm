"""Packet liveness helpers for the typed packet inbox."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone


def is_live_pending(packet: Mapping[str, object]) -> bool:
    """Return True when a packet is still pending and not expired."""
    if _packet_status(packet) != "pending":
        return False
    if is_failed_action_request(packet):
        return False
    if _normalized_text(packet.get("apply_pending_after_execution_at_utc")):
        return False
    expires_at = _parse_utc(packet.get("expires_at_utc"))
    if expires_at is None:
        return True
    return expires_at > datetime.now(timezone.utc)


def is_live_control_packet(packet: Mapping[str, object]) -> bool:
    """Return True when a packet should still drive current instruction state."""
    return is_live_pending(packet) or is_active_acked_action_request(packet)


def is_failed_action_request(packet: Mapping[str, object]) -> bool:
    """Return True when an action_request has terminal execution failure evidence."""
    return (
        _packet_kind(packet) == "action_request"
        and bool(_normalized_text(packet.get("execution_failed_at_utc")))
    )


def is_active_acked_action_request(packet: Mapping[str, object]) -> bool:
    """Return True for acknowledged action requests not yet resolved by apply."""
    if _packet_status(packet) != "acked":
        return False
    if _packet_kind(packet) != "action_request":
        return False
    if is_failed_action_request(packet):
        return False
    if _normalized_text(packet.get("apply_pending_after_execution_at_utc")):
        return False
    expires_at = _parse_utc(packet.get("expires_at_utc"))
    return expires_at is None or expires_at > datetime.now(timezone.utc)


def is_expired_unresolved(packet: Mapping[str, object]) -> bool:
    """Return True when a packet is expired but unresolved."""
    status = _packet_status(packet)
    if status == "expired":
        return True
    if status != "pending":
        return False
    expires_at = _parse_utc(packet.get("expires_at_utc"))
    return expires_at is not None and expires_at <= datetime.now(timezone.utc)


def _packet_status(packet: Mapping[str, object]) -> str:
    return _normalized_text(packet.get("status"))


def _packet_kind(packet: Mapping[str, object]) -> str:
    return _normalized_text(packet.get("kind"))


def _normalized_text(value: object) -> str:
    return str(value or "").strip()


def _parse_utc(value: object):
    text = _normalized_text(value)
    if not text:
        return None
    try:
        stamp = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        return stamp.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc)
