"""Packet post-expiry stamping for review-channel events."""

from __future__ import annotations

from collections.abc import MutableMapping

from ..runtime.packet_transport_expiry import (
    TRANSPORT_EXPIRY_EXPLICIT_METADATA_KEY,
    packet_kind_allows_optional_transport_expiry,
    packet_kind_default_ttl_minutes,
    packet_uses_transport_expiry,
)
from .event_store import DEFAULT_PACKET_TTL_MINUTES, future_utc_timestamp
from .packet_contract import PacketPostRequest


def apply_post_transport_expiry(
    *,
    request: PacketPostRequest,
    event: MutableMapping[str, object],
    metadata: MutableMapping[str, object],
) -> None:
    expiry_minutes = _post_transport_expiry_minutes(request=request, event=event)
    if expiry_minutes is None:
        return
    event["expires_at_utc"] = future_utc_timestamp(minutes=expiry_minutes)
    if packet_kind_allows_optional_transport_expiry(event.get("kind")):
        metadata[TRANSPORT_EXPIRY_EXPLICIT_METADATA_KEY] = True


def _post_transport_expiry_minutes(
    *,
    request: PacketPostRequest,
    event: MutableMapping[str, object],
) -> int | None:
    requested = _positive_int(request.expires_in_minutes)
    if packet_kind_allows_optional_transport_expiry(event.get("kind")):
        return requested
    if packet_uses_transport_expiry(event):
        return (
            requested
            or packet_kind_default_ttl_minutes(event.get("kind"))
            or DEFAULT_PACKET_TTL_MINUTES
        )
    return None


def _positive_int(value: object) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


__all__ = ["apply_post_transport_expiry"]
