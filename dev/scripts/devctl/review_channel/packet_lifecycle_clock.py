"""Packet lifecycle clock-expiry predicates."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone

from ..time_utils import parse_utc_timestamp as _parse_utc
from .packet_lifecycle_binding import has_creation_binding


def has_expired_durable_binding(packet: Mapping[str, object]) -> bool:
    return has_creation_binding(packet) and is_clock_expired(packet)


def is_clock_expired(packet: Mapping[str, object]) -> bool:
    expires_at = _parse_utc(str(packet.get("expires_at_utc") or "").strip())
    return expires_at is not None and expires_at <= datetime.now(timezone.utc)


__all__ = ["has_expired_durable_binding", "is_clock_expired"]
