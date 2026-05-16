"""Per-kind TTL evidence for long-lived review-channel packets."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from functools import partial
from typing import TypeAlias

from .collaboration_packet_kinds import TASK_PRODUCED_PACKET_KIND
from .packet_transport_expiry import (
    PACKET_KIND_TTL_SECONDS,
    packet_kind_default_ttl_seconds,
    packet_transport_expired,
    packet_transport_expires_at,
)
from .peer_heartbeat import (
    _format_utc,
    _latest_by_event_id,
    _packet_resolved,
    _packet_rows,
    _parse_utc,
)
from .value_coercion import coerce_string as _text

SCHEMA_VERSION = 1
PACKET_KIND_TTL_CONTRACT_ID = "PacketKindTtl"
TASK_PRODUCED_TTL_EVIDENCE_CONTRACT_ID = "TaskProducedTtlEvidence"
QUESTION_TTL_EVIDENCE_CONTRACT_ID = "QuestionTtlEvidence"
DECISION_TTL_EVIDENCE_CONTRACT_ID = "DecisionTtlEvidence"
FINDING_TTL_EVIDENCE_CONTRACT_ID = "FindingTtlEvidence"


@dataclass(frozen=True, slots=True)
class PacketKindTtl:
    contract_id: str = PACKET_KIND_TTL_CONTRACT_ID
    schema_version: int = SCHEMA_VERSION
    packet_kind: str = ""
    packet_id: str = ""
    observed_at_utc: str = ""
    expires_at_utc: str = ""
    ttl_seconds: int = 0
    status: str = "missing"
    expired: bool = False
    resolved: bool = False
    summary: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PacketKindTtlEvidence(PacketKindTtl):
    def __post_init__(self) -> None:
        if self.ttl_seconds <= 0 and self.packet_kind:
            object.__setattr__(
                self,
                "ttl_seconds",
                packet_kind_default_ttl_seconds(self.packet_kind),
            )


@dataclass(frozen=True, slots=True)
class TaskProducedTtlEvidence(PacketKindTtlEvidence):
    contract_id: str = TASK_PRODUCED_TTL_EVIDENCE_CONTRACT_ID
    packet_kind: str = TASK_PRODUCED_PACKET_KIND


@dataclass(frozen=True, slots=True)
class QuestionTtlEvidence(PacketKindTtlEvidence):
    contract_id: str = QUESTION_TTL_EVIDENCE_CONTRACT_ID
    packet_kind: str = "question"


@dataclass(frozen=True, slots=True)
class DecisionTtlEvidence(PacketKindTtlEvidence):
    contract_id: str = DECISION_TTL_EVIDENCE_CONTRACT_ID
    packet_kind: str = "decision"


@dataclass(frozen=True, slots=True)
class FindingTtlEvidence(PacketKindTtlEvidence):
    contract_id: str = FINDING_TTL_EVIDENCE_CONTRACT_ID
    packet_kind: str = "finding"


PacketKindTtlEvidenceType: TypeAlias = type[PacketKindTtlEvidence]

_EVIDENCE_TYPES: dict[str, PacketKindTtlEvidenceType] = {
    TASK_PRODUCED_PACKET_KIND: TaskProducedTtlEvidence,
    "question": QuestionTtlEvidence,
    "decision": DecisionTtlEvidence,
    "finding": FindingTtlEvidence,
}


def resolve_packet_kind_ttl(
    review_state: Mapping[str, object],
    *,
    kind: str,
    now_utc: str = "",
) -> PacketKindTtlEvidence:
    """Resolve TTL status for the latest unresolved packet of one kind."""
    packet_kind = _text(kind)
    evidence_type = _EVIDENCE_TYPES.get(packet_kind, PacketKindTtlEvidence)
    ttl_seconds = packet_kind_default_ttl_seconds(packet_kind)
    base = {
        "packet_kind": packet_kind,
        "ttl_seconds": ttl_seconds,
    }
    if not packet_kind or ttl_seconds <= 0:
        return evidence_type(
            **base,
            status="unsupported_kind",
            expired=False,
            resolved=False,
            summary="packet kind has no configured TTL",
        )

    packet = _latest_packet_by_kind(review_state, kind=packet_kind)
    if not packet:
        return evidence_type(
            **base,
            status="missing",
            expired=False,
            resolved=False,
            summary=f"no unresolved {packet_kind} packet found",
        )

    expires_at = packet_transport_expires_at(packet)
    expired = packet_transport_expired(packet, now=_parse_utc(now_utc))
    status = "expired" if expired else "alive"
    packet_id = _text(packet.get("packet_id"))
    return evidence_type(
        **base,
        packet_id=packet_id,
        observed_at_utc=_observed_at(packet),
        expires_at_utc=_format_utc(expires_at) if expires_at is not None else "",
        status=status,
        expired=expired,
        resolved=False,
        summary=f"{packet_kind} packet {packet_id or '(unknown)'} is {status}",
    )


resolve_task_produced_ttl = partial(
    resolve_packet_kind_ttl,
    kind=TASK_PRODUCED_PACKET_KIND,
)
resolve_question_ttl = partial(resolve_packet_kind_ttl, kind="question")
resolve_decision_ttl = partial(resolve_packet_kind_ttl, kind="decision")
resolve_finding_ttl = partial(resolve_packet_kind_ttl, kind="finding")


def _latest_packet_by_kind(
    review_state: Mapping[str, object],
    *,
    kind: str,
) -> Mapping[str, object]:
    candidates = [
        packet
        for packet in _packet_rows(review_state)
        if _text(packet.get("kind")) == kind and not _packet_resolved(packet)
    ]
    return _latest_by_event_id(candidates)


def _observed_at(packet: Mapping[str, object]) -> str:
    return _text(packet.get("posted_at")) or _text(packet.get("timestamp_utc"))


__all__ = [
    "DECISION_TTL_EVIDENCE_CONTRACT_ID",
    "FINDING_TTL_EVIDENCE_CONTRACT_ID",
    "PACKET_KIND_TTL_CONTRACT_ID",
    "QUESTION_TTL_EVIDENCE_CONTRACT_ID",
    "TASK_PRODUCED_TTL_EVIDENCE_CONTRACT_ID",
    "DecisionTtlEvidence",
    "FindingTtlEvidence",
    "PacketKindTtl",
    "PacketKindTtlEvidence",
    "QuestionTtlEvidence",
    "TaskProducedTtlEvidence",
    "resolve_decision_ttl",
    "resolve_finding_ttl",
    "resolve_packet_kind_ttl",
    "resolve_question_ttl",
    "resolve_task_produced_ttl",
]
