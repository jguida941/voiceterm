"""Typed packet-pressure contracts for ``/develop``."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

PACKET_BACKLOG_PRESSURE_CONTRACT_ID = "PacketBacklogPressure"
PACKET_INTENT_CLASSIFICATION_CONTRACT_ID = "PacketIntentClassification"
PACKET_ATTENTION_INGESTION_DECISION_CONTRACT_ID = "PacketAttentionIngestionDecision"
PACKET_INGEST_DECISION_CONTRACT_ID = "PacketIngestDecision"

DURABLE_PACKET_CLASSIFICATIONS = {
    "durable plan",
    "finding",
    "guard",
    "knowledge",
    "manual-review-required",
}
TERMINAL_PACKET_CLASSIFICATIONS = {"duplicate", "obsolete", "rejected"}


@dataclass(frozen=True, slots=True)
class PacketBacklogPressure:
    """Read-side packet pressure used by AgentAttentionLoop."""

    live_total: int
    actionable_total: int
    near_ttl_total: int
    expired_unresolved_total: int
    carry_forward_total: int
    durable_owner_gap_total: int
    per_kind: dict[str, int]
    per_role: dict[str, int]
    selected_packet_ids: tuple[str, ...]
    pressure_state: str
    soft_attention_budget: int
    hard_attention_budget: int
    near_ttl_minutes: int
    schema_version: int = 1
    contract_id: str = PACKET_BACKLOG_PRESSURE_CONTRACT_ID

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["selected_packet_ids"] = list(self.selected_packet_ids)
        return payload


@dataclass(frozen=True, slots=True)
class PacketIntentClassification:
    """One selected packet's durable-intent classification."""

    packet_id: str
    kind: str
    status: str
    to_role: str
    classification: str
    durable_owner: str = ""
    terminal_receipt: str = ""
    action_required: bool = False
    reason: str = ""
    target_ref: str = ""
    expires_at_utc: str = ""
    schema_version: int = 1
    contract_id: str = PACKET_INTENT_CLASSIFICATION_CONTRACT_ID

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PacketAttentionIngestionDecision:
    """Attention-loop decision for selected packet classifications."""

    decision: str
    reason_code: str
    required_action: str
    fail_closed: bool
    selected_packet_ids: tuple[str, ...]
    next_command: str = ""
    schema_version: int = 1
    contract_id: str = PACKET_ATTENTION_INGESTION_DECISION_CONTRACT_ID

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["selected_packet_ids"] = list(self.selected_packet_ids)
        return payload


@dataclass(frozen=True, slots=True)
class PacketIngestDecision:
    """Per-packet typed ingest/ack decision over a packet classification."""

    packet_id: str
    classification: str
    decision: str
    reason_code: str
    required_action: str
    next_command: str
    target_kind: str = ""
    target_ref: str = ""
    terminal_status: str = ""
    fail_closed: bool = False
    schema_version: int = 1
    contract_id: str = PACKET_INGEST_DECISION_CONTRACT_ID

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


__all__ = [
    "DURABLE_PACKET_CLASSIFICATIONS",
    "PACKET_ATTENTION_INGESTION_DECISION_CONTRACT_ID",
    "PACKET_BACKLOG_PRESSURE_CONTRACT_ID",
    "PACKET_INGEST_DECISION_CONTRACT_ID",
    "PACKET_INTENT_CLASSIFICATION_CONTRACT_ID",
    "PacketAttentionIngestionDecision",
    "PacketBacklogPressure",
    "PacketIngestDecision",
    "PacketIntentClassification",
    "TERMINAL_PACKET_CLASSIFICATIONS",
]
