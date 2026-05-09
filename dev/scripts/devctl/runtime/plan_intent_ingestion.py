"""Typed receipts for bounded plan-intent ingestion."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from .master_plan_contract import MASTER_PLAN_SCHEMA_VERSION

PLAN_INTENT_INGESTION_RECEIPT_CONTRACT_ID = "PlanIntentIngestionReceipt"
PLAN_INTENT_INGESTION_RECEIPT_STORE_REL = "dev/state/plan_ingestion_receipts.jsonl"


@dataclass(frozen=True, slots=True)
class PlanIntentIngestionReceipt:
    """Receipt proving a planning source reached typed authority or terminal state."""

    receipt_id: str
    source_kind: str
    source_ref: str
    status: str
    reason: str
    target_kind: str
    target_ref: str
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


def append_plan_intent_ingestion_receipt(
    path: Path,
    receipt: PlanIntentIngestionReceipt,
) -> PlanIntentIngestionReceipt:
    """Append one receipt to the durable plan-ingestion receipt store."""
    path.parent.mkdir(parents=True, exist_ok=True)
    stored = replace(receipt, receipt_path=str(path))
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(stored.to_dict(), sort_keys=True) + "\n")
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
    "PLAN_INTENT_INGESTION_RECEIPT_CONTRACT_ID",
    "PLAN_INTENT_INGESTION_RECEIPT_STORE_REL",
    "PlanIntentIngestionReceipt",
    "append_plan_intent_ingestion_receipt",
    "plan_intent_content_hash",
    "plan_intent_receipt_id",
    "plan_row_id_by_packet_receipt",
    "read_plan_intent_ingestion_receipts",
    "terminal_packet_receipt_by_packet",
]
