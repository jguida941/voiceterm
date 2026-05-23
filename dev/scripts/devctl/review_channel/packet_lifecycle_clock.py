"""Packet lifecycle clock-expiry predicates."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone

from ..runtime.packet_transport_expiry import packet_uses_transport_expiry
from ..time_utils import parse_utc_timestamp as _parse_utc
from .packet_lifecycle_binding import has_creation_binding

_RUNTIME_AUTHORITY_PACKET_KINDS = {
    "action_request",
    "approval_request",
    "commit_approval",
}


def has_expired_durable_binding(packet: Mapping[str, object]) -> bool:
    if _packet_kind(packet) in _RUNTIME_AUTHORITY_PACKET_KINDS:
        return False
    return has_creation_binding(packet) and _expires_at_or_before_now(packet)


def is_clock_expired(packet: Mapping[str, object]) -> bool:
    if not packet_uses_transport_expiry(packet):
        return False
    return _expires_at_or_before_now(packet)


def _expires_at_or_before_now(packet: Mapping[str, object]) -> bool:
    expires_at = _parse_utc(str(packet.get("expires_at_utc") or "").strip())
    return expires_at is not None and expires_at <= datetime.now(timezone.utc)


def _packet_kind(packet: Mapping[str, object]) -> str:
    return str(packet.get("kind") or "").strip()


__all__ = ["has_expired_durable_binding", "is_clock_expired"]
