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
        source_snapshot_ids=outcome.source_snapshot_ids,
        source_snapshot_path=outcome.source_snapshot_path,
        canonical_source_hash=outcome.canonical_source_hash,
        source_packet_expires_at_utc=outcome.source_packet_expires_at_utc,
        source_retention_status=outcome.source_retention_status,
        source_integrity_status=outcome.source_integrity_status,
        source_completeness_status=outcome.source_completeness_status,
        source_required_anchor_count=outcome.source_required_anchor_count,
        source_matched_anchor_count=outcome.source_matched_anchor_count,
        source_missing_required_anchors=outcome.source_missing_required_anchors,
        source_integrity_checked_at_utc=outcome.source_integrity_checked_at_utc,
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
