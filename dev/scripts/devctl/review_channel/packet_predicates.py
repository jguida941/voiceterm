"""Shared predicates for packet actor/session routing."""

from __future__ import annotations

from collections.abc import Mapping


def packet_has_actor_route(packet: Mapping[str, object]) -> bool:
    """Return True when a packet names a role or exact session route."""
    return bool(
        str(packet.get("target_role") or "").strip()
        or str(packet.get("target_session_id") or "").strip()
    )
