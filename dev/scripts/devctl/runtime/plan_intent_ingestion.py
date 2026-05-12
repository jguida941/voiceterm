"""Typed receipts for bounded plan-intent ingestion."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from .master_plan_contract import MASTER_PLAN_SCHEMA_VERSION
from .plan_ingestion_phase0_models import (
    CommandManifestProof,
    GuardMaturityRecord,
    PlanCompositionDispositionEntry,
    ReceiptCoverageInventory,
    RepoStateFingerprint,
)
from .state_store_authority import append_json_mapping
from .correlation_spine import (
    CAUSATION_REF_PREFIX,
    CORRELATION_REF_PREFIX,
    RUN_REF_PREFIX,
)

PLAN_INTENT_INGESTION_RECEIPT_CONTRACT_ID = "PlanIntentIngestionReceipt"
PLAN_INTENT_INGESTION_RECEIPT_STORE_REL = "dev/state/plan_ingestion_receipts.jsonl"
PLAN_INTENT_RECEIPT_REF_PREFIX = "plan_intent_receipt:"
TYPED_ACTION_REF_PREFIX = "typed_action:"
PLAN_INTENT_CORRELATION_REF_PREFIX = CORRELATION_REF_PREFIX
PLAN_INTENT_CAUSATION_REF_PREFIX = CAUSATION_REF_PREFIX
PLAN_INTENT_RUN_REF_PREFIX = RUN_REF_PREFIX


@dataclass(frozen=True, slots=True)
class PlanIntentIngestionReceipt:
    """Receipt proving a planning source reached typed authority or terminal state."""

    receipt_id: str
    action_id: str
    source_kind: str
    source_ref: str
    status: str
    reason: str
    target_kind: str
    target_ref: str
    correlation_id: str = ""
    causation_id: str = ""
    run_id: str = ""
    row_ids: tuple[str, ...] = ()
    store_statuses: tuple[str, ...] = ()
    terminal_status: str = ""
    packet_id: str = ""
    path: str = ""
    receipt_path: str = ""
    source_hash: str = ""
    source_snapshot_ids: tuple[str, ...] = ()
    source_snapshot_path: str = ""
    canonical_source_hash: str = ""
    source_packet_expires_at_utc: str = ""
    source_retention_status: str = ""
    source_integrity_status: str = ""
    source_completeness_status: str = ""
    source_required_anchor_count: int = 0
    source_matched_anchor_count: int = 0
    source_missing_required_anchors: tuple[str, ...] = ()
    source_integrity_checked_at_utc: str = ""
    composition_disposition_matrix: tuple[PlanCompositionDispositionEntry, ...] = ()
    command_manifest_proofs: tuple[CommandManifestProof, ...] = ()
    guard_maturity_records: tuple[GuardMaturityRecord, ...] = ()
    repo_state_fingerprint: RepoStateFingerprint | None = None
    receipt_coverage_inventory: ReceiptCoverageInventory | None = None
    schema_limit_warning: str = ""
    recorded_at_utc: str = ""
    dry_run: bool = False
    schema_version: int = MASTER_PLAN_SCHEMA_VERSION
    contract_id: str = PLAN_INTENT_INGESTION_RECEIPT_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["row_ids"] = list(self.row_ids)
        payload["store_statuses"] = list(self.store_statuses)
        payload["source_snapshot_ids"] = list(self.source_snapshot_ids)
        payload["source_missing_required_anchors"] = list(
            self.source_missing_required_anchors
        )
        payload["composition_disposition_matrix"] = [
            entry.to_dict() for entry in self.composition_disposition_matrix
        ]
        payload["command_manifest_proofs"] = [
            entry.to_dict() for entry in self.command_manifest_proofs
        ]
        payload["guard_maturity_records"] = [
            entry.to_dict() for entry in self.guard_maturity_records
        ]
        payload["repo_state_fingerprint"] = (
            self.repo_state_fingerprint.to_dict()
            if self.repo_state_fingerprint is not None
            else None
        )
        payload["receipt_coverage_inventory"] = (
            self.receipt_coverage_inventory.to_dict()
            if self.receipt_coverage_inventory is not None
            else None
        )
        return payload


def plan_intent_content_hash(value: str) -> str:
    """Return a stable content hash for one plan-intent source."""
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def plan_intent_receipt_id(
    *,
    source_kind: str,
    source_ref: str,
    source_hash: str,
    recorded_at_utc: str,
) -> str:
    """Return a bounded receipt id for one ingestion attempt."""
    raw = "\n".join((source_kind, source_ref, source_hash, recorded_at_utc))
    return "plan-ingest-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def plan_intent_action_id(
    *,
    source_kind: str,
    source_ref: str,
    source_hash: str,
    target_ref: str,
    recorded_at_utc: str,
) -> str:
    """Return a stable TypedAction id for one ingestion attempt."""
    raw = "\n".join(
        (
            source_kind,
            source_ref,
            source_hash,
            target_ref,
            recorded_at_utc,
        )
    )
    return "plan-intent-action-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def plan_intent_receipt_ref(receipt_id: str) -> str:
    """Return the canonical evidence ref for one plan-intent receipt."""
    return f"{PLAN_INTENT_RECEIPT_REF_PREFIX}{receipt_id}" if receipt_id else ""


def typed_action_ref(action_id: str) -> str:
    """Return the canonical evidence ref for one TypedAction id."""
    return f"{TYPED_ACTION_REF_PREFIX}{action_id}" if action_id else ""


def append_plan_intent_ingestion_receipt(
    path: Path,
    receipt: PlanIntentIngestionReceipt,
) -> PlanIntentIngestionReceipt:
    """Append one receipt to the durable plan-ingestion receipt store."""
    stored = replace(receipt, receipt_path=str(path))
    append_json_mapping(
        path,
        stored.to_dict(),
        store_id="plan_ingestion_receipts",
        correlation_id=stored.correlation_id,
        causation_id=stored.causation_id,
        run_id=stored.run_id,
    )
    return stored


def read_plan_intent_ingestion_receipts(
    path: Path,
) -> tuple[dict[str, object], ...]:
    """Read raw receipt rows from the JSONL receipt store."""
    if not path.exists():
        return ()
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return tuple(rows)


def terminal_packet_receipt_by_packet(
    receipts: tuple[dict[str, object], ...],
) -> dict[str, str]:
    """Return packet ids with terminal plan-intent receipts."""
    terminal: dict[str, str] = {}
    for receipt in receipts:
        packet_id = _packet_id_for_receipt(receipt)
        terminal_status = _terminal_status_for_receipt(receipt)
        if packet_id and terminal_status:
            terminal[packet_id] = terminal_status
    return terminal


def plan_row_id_by_packet_receipt(
    receipts: tuple[dict[str, object], ...],
) -> dict[str, str]:
    """Return packet ids whose accepted ingestion receipt names a plan row."""
    row_ids_by_packet: dict[str, str] = {}
    for receipt in receipts:
        packet_id = _packet_id_for_receipt(receipt)
        if not packet_id:
            continue
        if str(receipt.get("status") or "").strip() != "accepted":
            continue
        row_ids = receipt.get("row_ids")
        if not isinstance(row_ids, (list, tuple)) or not row_ids:
            continue
        row_id = str(row_ids[0] or "").strip()
        if row_id:
            row_ids_by_packet[packet_id] = row_id
    return row_ids_by_packet


def _packet_id_for_receipt(receipt: dict[str, object]) -> str:
    packet_id = str(receipt.get("packet_id") or "").strip()
    if packet_id:
        return packet_id
    source_ref = str(receipt.get("source_ref") or "").strip()
    prefix = "packet:"
    if source_ref.startswith(prefix):
        return source_ref[len(prefix) :].strip()
    return ""


def _terminal_status_for_receipt(receipt: dict[str, object]) -> str:
    status = str(receipt.get("terminal_status") or "").strip()
    if status:
        return status
    if str(receipt.get("target_kind") or "").strip() != "terminal_receipt":
        return ""
    status = str(receipt.get("status") or "").strip()
    if status in {"rejected", "duplicate", "obsolete"}:
        return status
    return ""


__all__ = [
    "PLAN_INTENT_RECEIPT_REF_PREFIX",
    "PLAN_INTENT_INGESTION_RECEIPT_CONTRACT_ID",
    "PLAN_INTENT_INGESTION_RECEIPT_STORE_REL",
    "PlanIntentIngestionReceipt",
    "TYPED_ACTION_REF_PREFIX",
    "append_plan_intent_ingestion_receipt",
    "plan_intent_action_id",
    "plan_intent_content_hash",
    "plan_intent_receipt_id",
    "plan_intent_receipt_ref",
    "plan_row_id_by_packet_receipt",
    "read_plan_intent_ingestion_receipts",
    "terminal_packet_receipt_by_packet",
    "typed_action_ref",
]
