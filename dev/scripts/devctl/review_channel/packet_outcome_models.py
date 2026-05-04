"""Typed packet outcome model contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum


class PacketOutcome(str, Enum):
    """Terminal outcome assigned to packet-history rows."""

    DELIVERED_VIA_COMMIT = "delivered_via_commit"
    SUPERSEDED_BY = "superseded_by"
    PROMOTED_TO_FINDING = "promoted_to_finding"
    WITHDRAWN_BY_REVIEWER = "withdrawn_by_reviewer"
    EXPIRED_UNRECOVERABLE = "expired_unrecoverable"
    ARCHIVED = "archived"
    LOST = "lost"


@dataclass(frozen=True, slots=True)
class PacketOutcomeRecord:
    """One typed outcome for a packet-history row."""

    packet_id: str
    outcome: PacketOutcome
    evidence_ref: str
    recorded_at_utc: str
    reason: str
    status: str
    expires_at_utc: str
    source_event_id: str = ""
    superseding_packet_id: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["outcome"] = self.outcome.value
        return payload


__all__ = [
    "PacketOutcome",
    "PacketOutcomeRecord",
]
