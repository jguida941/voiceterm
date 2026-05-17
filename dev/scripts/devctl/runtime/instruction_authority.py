"""Typed instruction-authority decisions and transition receipts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

from .master_plan_contract import IngestionProvenance
from .master_plan_parse import ingestion_provenance_from_mapping
from .value_coercion import coerce_mapping, coerce_string, coerce_string_items

INSTRUCTION_PRIORITY_DECISION_CONTRACT_ID = "InstructionPriorityDecision"
INSTRUCTION_TRANSITION_RECEIPT_CONTRACT_ID = "InstructionTransitionReceipt"
INSTRUCTION_AUTHORITY_SCHEMA_VERSION = 1
DEFAULT_INSTRUCTION_TRANSITIONS_REL = (
    "dev/reports/governance/instruction_transitions.jsonl"
)


@dataclass(frozen=True, slots=True)
class InstructionPriorityDecision:
    """Typed explanation of why one instruction source won."""

    selected_instruction_id: str
    selected_source_kind: str
    rule_id: str
    rejected_alternatives: tuple[str, ...] = ()
    rejection_reasons: tuple[str, ...] = ()
    decided_at_utc: str = ""
    schema_version: int = INSTRUCTION_AUTHORITY_SCHEMA_VERSION
    contract_id: str = INSTRUCTION_PRIORITY_DECISION_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["rejected_alternatives"] = list(self.rejected_alternatives)
        payload["rejection_reasons"] = list(self.rejection_reasons)
        return payload


@dataclass(frozen=True, slots=True)
class InstructionTransitionReceipt:
    """Typed audit row for an active-instruction authority change."""

    receipt_id: str
    closed_instruction_id: str
    close_reason: str
    new_instruction_id: str
    new_instruction_provenance: IngestionProvenance | None
    decided_via_rule: str
    transitioned_at_utc: str
    typed_evidence: dict[str, object] | None = None
    schema_version: int = INSTRUCTION_AUTHORITY_SCHEMA_VERSION
    contract_id: str = INSTRUCTION_TRANSITION_RECEIPT_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["new_instruction_provenance"] = (
            self.new_instruction_provenance.to_dict()
            if self.new_instruction_provenance is not None
            else None
        )
        return payload


def instruction_priority_decision_from_mapping(
    value: object,
) -> InstructionPriorityDecision:
    payload = coerce_mapping(value)
    return InstructionPriorityDecision(
        selected_instruction_id=coerce_string(payload.get("selected_instruction_id")),
        selected_source_kind=coerce_string(payload.get("selected_source_kind")),
        rule_id=coerce_string(payload.get("rule_id")),
        rejected_alternatives=coerce_string_items(payload.get("rejected_alternatives")),
        rejection_reasons=coerce_string_items(payload.get("rejection_reasons")),
        decided_at_utc=coerce_string(payload.get("decided_at_utc")),
    )


def instruction_transition_receipt_from_mapping(
    value: object,
) -> InstructionTransitionReceipt:
    payload = coerce_mapping(value)
    provenance_payload = payload.get("new_instruction_provenance")
    provenance = (
        ingestion_provenance_from_mapping(coerce_mapping(provenance_payload))
        if isinstance(provenance_payload, Mapping)
        else None
    )
    typed_evidence = coerce_mapping(payload.get("typed_evidence")) or None
    return InstructionTransitionReceipt(
        receipt_id=coerce_string(payload.get("receipt_id")),
        closed_instruction_id=coerce_string(payload.get("closed_instruction_id")),
        close_reason=coerce_string(payload.get("close_reason")),
        new_instruction_id=coerce_string(payload.get("new_instruction_id")),
        new_instruction_provenance=provenance,
        decided_via_rule=coerce_string(payload.get("decided_via_rule")),
        transitioned_at_utc=coerce_string(payload.get("transitioned_at_utc")),
        typed_evidence=dict(typed_evidence) if typed_evidence is not None else None,
    )


def packet_instruction_provenance(
    packet: Mapping[str, object],
    *,
    event_log_rel: str,
) -> IngestionProvenance:
    """Build provenance for instruction authority selected from a packet row."""
    packet_hash = "sha256:" + hashlib.sha256(
        json.dumps(dict(packet), sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    return IngestionProvenance(
        source_file=event_log_rel,
        source_line=0,
        source_kind="ReviewPacketEvent",
        source_hash=packet_hash,
        observed_at_utc=str(packet.get("posted_at") or packet.get("timestamp_utc") or ""),
        section_authority="review_packet",
    )


def append_instruction_transition_receipt(
    path: Path,
    receipt: InstructionTransitionReceipt,
) -> bool:
    """Append a receipt if its deterministic id is not already present."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            payload = coerce_mapping(_loads(line))
            if coerce_string(payload.get("receipt_id")) == receipt.receipt_id:
                return False
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(receipt.to_dict(), sort_keys=True) + "\n")
    return True


def deterministic_receipt_id(
    *,
    closed_instruction_id: str,
    close_reason: str,
    new_instruction_id: str,
    decided_via_rule: str,
    new_instruction_hash: str,
) -> str:
    digest = hashlib.sha256()
    for item in (
        closed_instruction_id,
        close_reason,
        new_instruction_id,
        decided_via_rule,
        new_instruction_hash,
    ):
        digest.update(item.encode("utf-8"))
        digest.update(b"\0")
    return f"instr_receipt_{digest.hexdigest()[:16]}"


def _loads(line: str) -> object:
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return {}


__all__ = [
    "DEFAULT_INSTRUCTION_TRANSITIONS_REL",
    "INSTRUCTION_AUTHORITY_SCHEMA_VERSION",
    "INSTRUCTION_PRIORITY_DECISION_CONTRACT_ID",
    "INSTRUCTION_TRANSITION_RECEIPT_CONTRACT_ID",
    "InstructionPriorityDecision",
    "InstructionTransitionReceipt",
    "append_instruction_transition_receipt",
    "deterministic_receipt_id",
    "instruction_priority_decision_from_mapping",
    "instruction_transition_receipt_from_mapping",
    "packet_instruction_provenance",
]
