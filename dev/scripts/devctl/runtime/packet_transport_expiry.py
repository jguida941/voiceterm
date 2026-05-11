"""Transport-expiry policy for review-channel packets.

Review packets carry two different things: runtime handoff authority and
durable content. Runtime handoff can expire. Durable content must be ingested,
dismissed, superseded, or otherwise given typed ownership; clock expiry is not a
content disposition.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone

from ..time_utils import parse_utc_timestamp
from .collaboration_packet_kinds import COLLABORATION_LIFECYCLE_PACKET_KINDS

ALWAYS_TRANSPORT_EXPIRING_PACKET_KINDS = frozenset(
    {
        "action_request",
        "approval_request",
        "commit_approval",
        "continuation_anchor",
        "stop_anchor",
    }
)
CONDITIONAL_TRANSPORT_EXPIRING_PACKET_KINDS = frozenset({"decision"})
DURABLE_INTENT_PACKET_KINDS = frozenset(
    {
        "finding",
        "plan_gap_review",
        "plan_patch_review",
        "plan_ready_gate",
        "draft",
    }
)
NON_TRANSPORT_EXPIRING_PACKET_KINDS = frozenset(
    {
        *DURABLE_INTENT_PACKET_KINDS,
        *COLLABORATION_LIFECYCLE_PACKET_KINDS,
        "instruction",
        "question",
        "system_notice",
    }
)


def packet_uses_transport_expiry(packet: Mapping[str, object]) -> bool:
    """Return True when a packet's ``expires_at_utc`` is runtime authority."""
    kind = _text(_packet_value(packet, "kind"))
    if kind in ALWAYS_TRANSPORT_EXPIRING_PACKET_KINDS:
        return True
    if kind in CONDITIONAL_TRANSPORT_EXPIRING_PACKET_KINDS:
        return not packet_carries_durable_intent(packet)
    if kind in NON_TRANSPORT_EXPIRING_PACKET_KINDS:
        return False
    return False


def packet_carries_durable_intent(packet: Mapping[str, object]) -> bool:
    """Return True when packet content must resolve through typed ownership."""
    kind = _text(_packet_value(packet, "kind"))
    if kind in DURABLE_INTENT_PACKET_KINDS:
        return True
    if _text(_packet_value(packet, "target_kind")) == "plan":
        return True
    if _text(_packet_value(packet, "target_ref")):
        return True
    if _text(_packet_value(packet, "intake_ref")):
        return True
    if _rows(_packet_value(packet, "anchor_refs")):
        return True
    return _has_plan_proposal(_packet_value(packet, "plan_proposal"))


def packet_transport_expires_at(packet: Mapping[str, object]) -> datetime | None:
    """Return the runtime transport expiry timestamp for one packet, if any."""
    if not packet_uses_transport_expiry(packet):
        return None
    return parse_utc_timestamp(_packet_value(packet, "expires_at_utc"))


def packet_transport_expired(
    packet: Mapping[str, object],
    *,
    now: datetime | None = None,
) -> bool:
    """Return True when a runtime-transport packet is past its TTL."""
    expires_at = packet_transport_expires_at(packet)
    if expires_at is None:
        return False
    observed_now = now or datetime.now(timezone.utc)
    if observed_now.tzinfo is None:
        observed_now = observed_now.replace(tzinfo=timezone.utc)
    return expires_at <= observed_now.astimezone(timezone.utc)


def _has_plan_proposal(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(bool(_text(item)) for item in value.values())
    return bool(value and _text(value))


def _rows(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(_text(item) for item in value if _text(item))


def _packet_value(packet: Mapping[str, object], field_name: str) -> object:
    return packet.get(field_name)


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "ALWAYS_TRANSPORT_EXPIRING_PACKET_KINDS",
    "CONDITIONAL_TRANSPORT_EXPIRING_PACKET_KINDS",
    "DURABLE_INTENT_PACKET_KINDS",
    "NON_TRANSPORT_EXPIRING_PACKET_KINDS",
    "packet_carries_durable_intent",
    "packet_transport_expired",
    "packet_transport_expires_at",
    "packet_uses_transport_expiry",
]
