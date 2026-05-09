"""Packet liveness helpers for the typed packet inbox."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone

from .packet_transport_expiry import (
    packet_transport_expired,
    packet_transport_expires_at,
    packet_uses_transport_expiry,
)

_UNRESOLVED_EXPIRED_ARCHIVE_CLASSIFICATIONS = {
    "clock_expired_without_disposition",
}


def is_live_pending(packet: Mapping[str, object]) -> bool:
    """Return True when a packet is still pending and not expired."""
    if _packet_status(packet) != "pending":
        return False
    if _is_resolved_lifecycle(packet):
        return False
    if is_failed_action_request(packet):
        return False
    if _normalized_text(packet.get("apply_pending_after_execution_at_utc")):
        return False
    if not packet_uses_transport_expiry(packet):
        return True
    expires_at = packet_transport_expires_at(packet)
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
    expires_at = packet_transport_expires_at(packet)
    return expires_at is None or expires_at > datetime.now(timezone.utc)


def is_expired_unresolved(packet: Mapping[str, object]) -> bool:
    """Return True when a packet is expired but unresolved."""
    if not packet_uses_transport_expiry(packet):
        return False
    if _has_unresolved_expired_archive_classification(packet):
        return True
    return is_expired_unresolved_attention(packet)


def is_expired_unresolved_attention(packet: Mapping[str, object]) -> bool:
    """Return True when an expired packet should still drive inbox attention."""
    if _is_resolved_lifecycle(packet):
        return False
    if not packet_uses_transport_expiry(packet):
        return False
    status = _packet_status(packet)
    if status == "expired":
        return True
    if status != "pending":
        return False
    return packet_transport_expired(packet)


def _packet_status(packet: Mapping[str, object]) -> str:
    return _normalized_text(packet.get("status"))


def _packet_kind(packet: Mapping[str, object]) -> str:
    return _normalized_text(packet.get("kind"))


def _is_resolved_lifecycle(packet: Mapping[str, object]) -> bool:
    lifecycle = _normalized_text(packet.get("lifecycle_current_state"))
    if lifecycle in {"applied", "dismissed", "archived"}:
        return True
    disposition = packet.get("disposition")
    if not isinstance(disposition, Mapping):
        return False
    return _normalized_text(disposition.get("sink")) in {
        "applied",
        "dismissed",
        "archived",
    }


def _has_unresolved_expired_archive_classification(packet: Mapping[str, object]) -> bool:
    disposition = packet.get("disposition")
    if not isinstance(disposition, Mapping):
        return False
    classification = _normalized_text(disposition.get("archive_classification"))
    if not classification:
        resolution_anchor = _normalized_text(disposition.get("resolution_anchor"))
        prefix = "archive_classification:"
        if resolution_anchor.startswith(prefix):
            classification = resolution_anchor[len(prefix) :]
    return classification in _UNRESOLVED_EXPIRED_ARCHIVE_CLASSIFICATIONS


def _normalized_text(value: object) -> str:
    return str(value or "").strip()
