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
    recorded_at_utc: str = ""
    dry_run: bool = False
    schema_version: int = MASTER_PLAN_SCHEMA_VERSION
    contract_id: str = PLAN_INTENT_INGESTION_RECEIPT_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["row_ids"] = list(self.row_ids)
        payload["store_statuses"] = list(self.store_statuses)
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


__all__ = [
    "PLAN_INTENT_INGESTION_RECEIPT_CONTRACT_ID",
    "PLAN_INTENT_INGESTION_RECEIPT_STORE_REL",
    "PlanIntentIngestionReceipt",
    "append_plan_intent_ingestion_receipt",
    "plan_intent_content_hash",
    "plan_intent_receipt_id",
    "read_plan_intent_ingestion_receipts",
]
