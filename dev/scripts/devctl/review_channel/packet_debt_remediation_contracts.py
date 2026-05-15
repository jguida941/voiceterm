"""Typed contracts for packet carry-forward debt remediation."""

from __future__ import annotations

from dataclasses import asdict, dataclass

PACKET_DURABLE_INGESTION_CONTRACT_ID = "PacketDurableIngestionReceipt"
DECIDED_PACKET_DEBT_DETECTOR_CONTRACT_ID = "DecidedPacketDebtDetector"
PACKET_BATCH_TRIAGE_CONTRACT_ID = "PacketBatchTriage"
PACKET_BATCH_TRIAGE_ROW_CONTRACT_ID = "PacketBatchTriageRow"
PACKET_DEBT_REMEDIATION_CONTRACT_ID = "PacketDebtRemediationReport"
PACKET_DEBT_REMEDIATION_ROW_CONTRACT_ID = "PacketDebtRemediationRow"
PACKET_DEBT_REMEDIATION_SCHEMA_VERSION = 1
PACKET_DURABLE_INGESTION_EVENT_TYPES = frozenset(
    {
        "packet_durable_ingestion_recorded",
        "packet_durable_ingestion_failed",
    }
)


@dataclass(frozen=True, slots=True)
class PacketDurableIngestionReceipt:
    """Receipt proving one transport packet was merged into durable state."""

    packet_id: str
    status: str
    reason: str
    target_kind: str
    target_ref: str
    binding_target_kind: str = ""
    binding_target: str = ""
    path: str = ""
    projection_path: str = ""
    event_id: str = ""
    recorded_at_utc: str = ""
    contract_id: str = PACKET_DURABLE_INGESTION_CONTRACT_ID
    schema_version: int = PACKET_DEBT_REMEDIATION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PacketDebtRemediationRow:
    """One carry-forward packet mapped to a deterministic remediation route."""

    packet_id: str
    reason: str
    kind: str
    status: str
    lifecycle_state: str
    cluster_id: str
    recommended_action: str
    target_ref: str = ""
    summary: str = ""
    receipt: PacketDurableIngestionReceipt | None = None
    contract_id: str = PACKET_DEBT_REMEDIATION_ROW_CONTRACT_ID
    schema_version: int = PACKET_DEBT_REMEDIATION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["receipt"] = self.receipt.to_dict() if self.receipt else None
        return payload


@dataclass(frozen=True, slots=True)
class DecidedPacketDebtDetector:
    """Detector summary for ACKed packets that still lack durable ownership."""

    reason: str
    total_count: int
    sample_packet_ids: tuple[str, ...]
    kind_counts: dict[str, int]
    status_counts: dict[str, int]
    contract_id: str = DECIDED_PACKET_DEBT_DETECTOR_CONTRACT_ID
    schema_version: int = PACKET_DEBT_REMEDIATION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["sample_packet_ids"] = list(self.sample_packet_ids)
        return payload


@dataclass(frozen=True, slots=True)
class PacketBatchTriageRow:
    """One packet-debt cluster sharing reason, target, and next action."""

    cluster_id: str
    reason: str
    recommended_action: str
    target_ref: str
    packet_count: int
    sample_packet_ids: tuple[str, ...]
    kind_counts: dict[str, int]
    status_counts: dict[str, int]
    contract_id: str = PACKET_BATCH_TRIAGE_ROW_CONTRACT_ID
    schema_version: int = PACKET_DEBT_REMEDIATION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["sample_packet_ids"] = list(self.sample_packet_ids)
        return payload


@dataclass(frozen=True, slots=True)
class PacketBatchTriage:
    """Bounded cluster summary for packet debt classes."""

    rows: tuple[PacketBatchTriageRow, ...]
    total_cluster_count: int
    largest_batch_size: int = 0
    contract_id: str = PACKET_BATCH_TRIAGE_CONTRACT_ID
    schema_version: int = PACKET_DEBT_REMEDIATION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["rows"] = [row.to_dict() for row in self.rows]
        return payload


@dataclass(frozen=True, slots=True)
class PacketDebtRemediationReport:
    """Bounded report used by /develop and probes to drain packet debt."""

    generated_at_utc: str
    source_review_state_path: str
    write_enabled: bool
    rows: tuple[PacketDebtRemediationRow, ...]
    total_debt_count: int = 0
    decided_packet_debt: DecidedPacketDebtDetector | None = None
    batch_triage: PacketBatchTriage | None = None
    contract_id: str = PACKET_DEBT_REMEDIATION_CONTRACT_ID
    schema_version: int = PACKET_DEBT_REMEDIATION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        row_payloads = [row.to_dict() for row in self.rows]
        total_debt_count = self.total_debt_count or len(row_payloads)
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "contract_id": self.contract_id,
            "generated_at_utc": self.generated_at_utc,
            "source_review_state_path": self.source_review_state_path,
            "write_enabled": self.write_enabled,
        }
        payload["debt_count"] = len(row_payloads)
        payload["total_debt_count"] = total_debt_count
        payload["omitted_debt_count"] = max(total_debt_count - len(row_payloads), 0)
        payload["action_counts"] = _counts(row.recommended_action for row in self.rows)
        payload["receipt_counts"] = _counts(
            row.receipt.status for row in self.rows if row.receipt is not None
        )
        payload["decided_packet_debt"] = (
            self.decided_packet_debt.to_dict()
            if self.decided_packet_debt
            else None
        )
        payload["batch_triage"] = self.batch_triage.to_dict() if self.batch_triage else None
        payload["rows"] = row_payloads
        return payload


def durable_ingestion_event(
    *,
    packet: dict[str, object],
    receipt: PacketDurableIngestionReceipt,
    event_type: str,
    timestamp_utc: str,
) -> dict[str, object]:
    """Return one event-log row for a durable ingestion receipt."""
    event: dict[str, object] = {
        "schema_version": PACKET_DEBT_REMEDIATION_SCHEMA_VERSION,
        "event_type": event_type,
        "source": "review_channel",
        "event_id": "",
        "session_id": packet.get("session_id"),
    }
    event.update(
        {
            "project_id": packet.get("project_id"),
            "packet_id": packet.get("packet_id"),
            "trace_id": packet.get("trace_id"),
            "timestamp_utc": timestamp_utc,
            "plan_id": packet.get("plan_id"),
        }
    )
    event.update(
        {
            "controller_run_id": packet.get("controller_run_id"),
            "from_agent": packet.get("from_agent"),
            "to_agent": packet.get("to_agent"),
            "kind": packet.get("kind"),
            "summary": packet.get("summary"),
        }
    )
    event.update(
        {
            "status": packet.get("status"),
            "packet_durable_ingestion": receipt.to_dict(),
            "durable_binding": receipt.to_dict(),
            "metadata": {"actor": "system", "reason": receipt.reason},
        }
    )
    return event


def receipt_from_binding(
    *,
    binding: dict[str, object],
    target_kind: str,
    target_ref: str,
) -> PacketDurableIngestionReceipt:
    """Convert a plan-row binding result into a durable-ingestion receipt."""
    return PacketDurableIngestionReceipt(
        packet_id=str(binding.get("packet_id") or "").strip(),
        status=str(binding.get("status") or "").strip(),
        reason=str(binding.get("reason") or "").strip(),
        target_kind=target_kind,
        target_ref=target_ref,
        binding_target_kind=str(binding.get("binding_target_kind") or "").strip(),
        binding_target=str(binding.get("binding_target") or "").strip(),
        path=str(binding.get("path") or "").strip(),
        projection_path=str(binding.get("projection_path") or "").strip(),
    )


def _counts(values) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value or "").strip() or "unknown"
        counts[key] = counts.get(key, 0) + 1
    return counts


__all__ = [
    "DECIDED_PACKET_DEBT_DETECTOR_CONTRACT_ID",
    "PACKET_BATCH_TRIAGE_CONTRACT_ID",
    "PACKET_BATCH_TRIAGE_ROW_CONTRACT_ID",
    "PACKET_DEBT_REMEDIATION_CONTRACT_ID",
    "PACKET_DEBT_REMEDIATION_ROW_CONTRACT_ID",
    "PACKET_DEBT_REMEDIATION_SCHEMA_VERSION",
    "PACKET_DURABLE_INGESTION_CONTRACT_ID",
    "PACKET_DURABLE_INGESTION_EVENT_TYPES",
    "DecidedPacketDebtDetector",
    "PacketBatchTriage",
    "PacketBatchTriageRow",
    "PacketDebtRemediationReport",
    "PacketDebtRemediationRow",
    "PacketDurableIngestionReceipt",
    "durable_ingestion_event",
    "receipt_from_binding",
]
