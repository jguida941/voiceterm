"""Receipt construction for plan-intent ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...runtime.plan_intent_ingestion import (
    PlanIntentIngestionReceipt,
    plan_intent_receipt_id,
)
from .plan_intake_sources import PlanIntentSource
from .plan_intake_support import target_ref_from_source, text


@dataclass(frozen=True, slots=True)
class ReceiptBuildContext:
    """Stable inputs shared by every receipt outcome."""

    args: Any
    source: PlanIntentSource
    source_hash: str
    observed_at: str
    store_path: Path


@dataclass(frozen=True, slots=True)
class ReceiptOutcome:
    """One receipt outcome before common provenance fields are added."""

    status: str
    reason: str
    target_kind: str
    row_ids: tuple[str, ...] = ()
    store_statuses: tuple[str, ...] = ()
    terminal_status: str = ""


def build_receipt(
    context: ReceiptBuildContext,
    outcome: ReceiptOutcome,
) -> PlanIntentIngestionReceipt:
    """Build a typed plan-intent ingestion receipt."""
    source = context.source
    packet = source.packet_payload
    receipt_id = plan_intent_receipt_id(
        source_kind=source.kind,
        source_ref=source.ref,
        source_hash=context.source_hash,
        recorded_at_utc=context.observed_at,
    )
    return PlanIntentIngestionReceipt(
        receipt_id=receipt_id,
        source_kind=source.kind,
        source_ref=source.ref,
        status=outcome.status,
        reason=outcome.reason,
        target_kind=outcome.target_kind,
        target_ref=target_ref_from_source(context.args, source),
        row_ids=outcome.row_ids,
        store_statuses=outcome.store_statuses,
        terminal_status=outcome.terminal_status,
        packet_id=text(packet.get("packet_id")),
        path=str(context.store_path),
        source_hash=context.source_hash,
        recorded_at_utc=context.observed_at,
        dry_run=bool(getattr(context.args, "dry_run", False)),
    )


def receipt_status(statuses: tuple[str, ...]) -> tuple[str, str, str]:
    """Return receipt status, reason, and optional terminal class."""
    if statuses and all(status == "already_present" for status in statuses):
        return "duplicate", "plan_rows_already_present", "duplicate"
    if any(status in {"inserted", "updated"} for status in statuses):
        return "accepted", "plan_rows_upserted", ""
    return "rejected", "plan_rows_not_written", "rejected"


__all__ = ["ReceiptBuildContext", "ReceiptOutcome", "build_receipt", "receipt_status"]
