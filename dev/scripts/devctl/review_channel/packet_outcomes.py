"""Typed packet outcome ledger helpers for review-channel history."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
import re

from .packet_lifecycle import project_packet_lifecycle


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


@dataclass(frozen=True, slots=True)
class PacketOutcomeLedger:
    """Read-side snapshot of packet outcomes for a bounded history view."""

    generated_at_utc: str
    source: str
    records: tuple[PacketOutcomeRecord, ...]
    schema_version: int = 1
    contract_id: str = "PacketOutcomeLedger"

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "contract_id": self.contract_id,
            "generated_at_utc": self.generated_at_utc,
        }
        payload["source"] = self.source
        payload["record_count"] = len(self.records)
        payload["outcome_counts"] = _outcome_counts(self.records)
        payload["records"] = [record.to_dict() for record in self.records]
        return payload


_COMMIT_SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b", re.IGNORECASE)


def build_packet_outcome_ledger(
    *,
    packets: Iterable[Mapping[str, object]],
    events: Iterable[Mapping[str, object]],
    generated_at_utc: str,
    source: str,
) -> PacketOutcomeLedger:
    """Classify the packet-history rows shown by a read surface."""
    event_rows = [event for event in events if isinstance(event, Mapping)]
    records = tuple(
        _record_for_packet(packet, event_rows, generated_at_utc)
        for packet in packets
        if isinstance(packet, Mapping) and _packet_needs_outcome(packet)
    )
    return PacketOutcomeLedger(
        generated_at_utc=generated_at_utc,
        source=source,
        records=records,
    )


def attach_packet_outcomes(
    packets: Iterable[Mapping[str, object]],
    ledger: PacketOutcomeLedger,
) -> list[dict[str, object]]:
    """Attach ledger records to packet rows without mutating source rows."""
    by_packet_id = {
        record.packet_id: record.to_dict()
        for record in ledger.records
        if record.packet_id
    }
    enriched: list[dict[str, object]] = []
    for packet in packets:
        row = dict(packet)
        outcome = by_packet_id.get(str(row.get("packet_id") or "").strip())
        if outcome is not None:
            row["packet_outcome"] = outcome
            if outcome.get("outcome") == PacketOutcome.ARCHIVED.value:
                row = project_packet_lifecycle(row, stale_pending=True)
        enriched.append(row)
    return enriched


def _record_for_packet(
    packet: Mapping[str, object],
    events: list[Mapping[str, object]],
    generated_at_utc: str,
) -> PacketOutcomeRecord:
    packet_id = _text(packet.get("packet_id"))
    status = _text(packet.get("status"))
    expires_at = _text(packet.get("expires_at_utc"))
    posted_at = _parse_utc(_text(packet.get("posted_at")))
    evidence = _find_later_evidence(packet_id, posted_at, events)
    if evidence is not None:
        return _record_from_evidence(packet, evidence, generated_at_utc)
    explicit_expiry = _find_expiry_event(packet_id, events)
    if explicit_expiry is not None:
        return PacketOutcomeRecord(
            packet_id=packet_id,
            outcome=PacketOutcome.ARCHIVED,
            evidence_ref=f"event:{_text(explicit_expiry.get('event_id'))}",
            recorded_at_utc=generated_at_utc,
            reason="explicit packet_expired event archived the packet without later resolution evidence",
            status=status,
            expires_at_utc=expires_at,
            source_event_id=_text(explicit_expiry.get("event_id")),
        )
    return PacketOutcomeRecord(
        packet_id=packet_id,
        outcome=PacketOutcome.ARCHIVED,
        evidence_ref="archive_classification:clock_expired_without_disposition",
        recorded_at_utc=generated_at_utc,
        reason="pending packet TTL elapsed and the lifecycle reducer archived it for audit",
        status=status,
        expires_at_utc=expires_at,
    )


def _record_from_evidence(
    packet: Mapping[str, object],
    evidence: Mapping[str, object],
    generated_at_utc: str,
) -> PacketOutcomeRecord:
    packet_id = _text(packet.get("packet_id"))
    event_id = _text(evidence.get("event_id"))
    evidence_text = _event_search_text(evidence).lower()
    outcome = _classify_evidence(evidence, evidence_text)
    superseding_packet_id = ""
    if outcome == PacketOutcome.SUPERSEDED_BY:
        superseding_packet_id = _text(evidence.get("packet_id"))
    return PacketOutcomeRecord(
        packet_id=packet_id,
        outcome=outcome,
        evidence_ref=_evidence_ref(evidence, outcome),
        recorded_at_utc=generated_at_utc,
        reason=_outcome_reason(outcome),
        status=_text(packet.get("status")),
        expires_at_utc=_text(packet.get("expires_at_utc")),
        source_event_id=event_id,
        superseding_packet_id=superseding_packet_id,
    )


def _packet_needs_outcome(packet: Mapping[str, object]) -> bool:
    status = _text(packet.get("status"))
    if status == "expired":
        return True
    if status != "pending":
        return False
    expires_at = _parse_utc(_text(packet.get("expires_at_utc")))
    return expires_at is not None and expires_at <= datetime.now(timezone.utc)


def _find_later_evidence(
    packet_id: str,
    posted_at: datetime | None,
    events: list[Mapping[str, object]],
) -> Mapping[str, object] | None:
    if not packet_id:
        return None
    for event in events:
        if _text(event.get("packet_id")) == packet_id:
            continue
        event_time = _parse_utc(_text(event.get("timestamp_utc")))
        if posted_at is not None and event_time is not None and event_time <= posted_at:
            continue
        if packet_id in _event_search_text(event):
            return event
    return None


def _find_expiry_event(
    packet_id: str,
    events: list[Mapping[str, object]],
) -> Mapping[str, object] | None:
    for event in events:
        if _text(event.get("packet_id")) != packet_id:
            continue
        if _text(event.get("event_type")) == "packet_expired":
            return event
    return None


def _classify_evidence(
    event: Mapping[str, object],
    evidence_text: str,
) -> PacketOutcome:
    kind = _text(event.get("kind"))
    if "supersed" in evidence_text:
        return PacketOutcome.SUPERSEDED_BY
    if kind == "finding" or "promoted to finding" in evidence_text:
        return PacketOutcome.PROMOTED_TO_FINDING
    if "withdraw" in evidence_text or "dismiss" in evidence_text:
        return PacketOutcome.WITHDRAWN_BY_REVIEWER
    if (
        kind == "system_notice"
        or "commit" in evidence_text
        or "landed" in evidence_text
        or "delivered" in evidence_text
        or _COMMIT_SHA_RE.search(evidence_text)
    ):
        return PacketOutcome.DELIVERED_VIA_COMMIT
    return PacketOutcome.EXPIRED_UNRECOVERABLE


def _evidence_ref(
    event: Mapping[str, object],
    outcome: PacketOutcome,
) -> str:
    attestation_ref = _attestation_evidence_ref(event)
    if attestation_ref:
        return attestation_ref
    event_id = _text(event.get("event_id"))
    if outcome == PacketOutcome.SUPERSEDED_BY:
        superseding_packet_id = _text(event.get("packet_id"))
        if superseding_packet_id:
            return f"packet:{superseding_packet_id}"
    if outcome == PacketOutcome.DELIVERED_VIA_COMMIT:
        sha = _COMMIT_SHA_RE.search(_event_search_text(event))
        if sha is not None:
            return f"commit:{sha.group(0)}"
    return f"event:{event_id}" if event_id else "event:unknown"


def _attestation_evidence_ref(event: Mapping[str, object]) -> str:
    metadata = event.get("metadata")
    if not isinstance(metadata, Mapping):
        return ""
    attestation = metadata.get("guard_attestation")
    if not isinstance(attestation, Mapping):
        return ""
    packet_id = _text(attestation.get("packet_id"))
    event_id = _text(event.get("event_id"))
    if packet_id and event_id:
        return f"packet_attestation:{packet_id}@{event_id}"
    if packet_id:
        return f"packet_attestation:{packet_id}"
    return ""


def _outcome_reason(outcome: PacketOutcome) -> str:
    if outcome == PacketOutcome.DELIVERED_VIA_COMMIT:
        return "later review-channel evidence names the packet in delivered or commit context"
    if outcome == PacketOutcome.SUPERSEDED_BY:
        return "later packet explicitly supersedes this packet"
    if outcome == PacketOutcome.PROMOTED_TO_FINDING:
        return "later finding evidence names this packet as promoted review work"
    if outcome == PacketOutcome.WITHDRAWN_BY_REVIEWER:
        return "later reviewer evidence names this packet as withdrawn or dismissed"
    if outcome == PacketOutcome.EXPIRED_UNRECOVERABLE:
        return "later evidence names the packet but does not prove a stronger terminal state"
    if outcome == PacketOutcome.ARCHIVED:
        return "packet was archived with a typed disposition instead of remaining unresolved"
    return "no later typed evidence resolves the expired packet"


def _event_search_text(event: Mapping[str, object]) -> str:
    values: list[str] = []
    for key in (
        "packet_id",
        "kind",
        "summary",
        "body",
        "requested_action",
        "target_ref",
        "target_revision",
        "guard_results_summary",
        "full_guard_bundle_evidence",
    ):
        values.append(_text(event.get(key)))
    for key in ("evidence_refs", "guidance_refs", "anchor_refs"):
        raw_values = event.get(key)
        if isinstance(raw_values, list):
            values.extend(_text(value) for value in raw_values)
    return "\n".join(value for value in values if value)


def _outcome_counts(records: tuple[PacketOutcomeRecord, ...]) -> dict[str, int]:
    counts = {outcome.value: 0 for outcome in PacketOutcome}
    for record in records:
        counts[record.outcome.value] += 1
    return counts


def _parse_utc(value: str) -> datetime | None:
    if not value:
        return None
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        return stamp.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc)


def _text(value: object) -> str:
    return str(value or "").strip()
