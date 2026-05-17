"""Runtime-lifecycle predicate for review-channel packets."""

from __future__ import annotations

from collections.abc import Mapping

from .packet_transport_expiry import (
    packet_has_explicit_transport_expiry,
    packet_kind_allows_optional_transport_expiry,
    packet_kind_uses_default_transport_expiry,
)


def packet_requires_runtime_lifecycle(packet: Mapping[str, object]) -> bool:
    """Return True when packet expiry represents live runtime handoff state."""
    kind = str(packet.get("kind") or "").strip()
    if packet_kind_uses_default_transport_expiry(kind):
        return True
    if packet_kind_allows_optional_transport_expiry(kind):
        return packet_has_explicit_transport_expiry(packet)
    return False
