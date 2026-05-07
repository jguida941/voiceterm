"""Bounded plan-intent ingestion for ``devctl develop``."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

from ...common import emit_output, write_output
from ...config import REPO_ROOT
from ...runtime.master_plan_contract import DEFAULT_MASTER_PLAN_STORE_REL, PlanRow
from ...runtime.master_plan_store import (
    read_plan_rows_jsonl,
    upsert_plan_row_jsonl,
    with_plan_revision,
)
from ...runtime.plan_intent_ingestion import (
    PLAN_INTENT_INGESTION_RECEIPT_STORE_REL,
    PlanIntentIngestionReceipt,
    append_plan_intent_ingestion_receipt,
    plan_intent_content_hash,
)
from ...runtime.plan_source_retention import PLAN_SOURCE_SNAPSHOT_STORE_REL
from ...time_utils import utc_timestamp
from .actions import resolve_action
from .plan_intake_receipts import (
    ReceiptBuildContext,
    ReceiptOutcome,
    build_receipt,
    receipt_status,
)
from .plan_intake_render import remediation_for_receipt, render_plan_intake_markdown
from .plan_intake_rows import rows_from_source
from .plan_intake_sources import source_from_args
from .plan_intake_source_snapshots import (
    rows_with_source_snapshot_refs,
    source_completeness_status,
    source_integrity_status,
    source_matched_anchor_count,
    source_missing_required_anchors,
    source_packet_expires_at,
    source_required_anchor_count,
    source_retention_status,
    write_source_snapshots,
)
from .plan_intake_support import text


def run_ingest_plan(args: Any) -> int:
    """Run the write-capable plan-intent ingestion action."""
    action = resolve_action(args, default="ingest-plan")
    receipt = ingest_plan_intent(args, repo_root=REPO_ROOT)
    payload = {
        "command": "develop",
        "action": action,
        "ok": receipt.status in {"accepted", "duplicate", "obsolete", "preview"},
        "receipt": receipt.to_dict(),
    }
    remediation = remediation_for_receipt(args, receipt)
    if remediation:
        payload["remediation"] = remediation
    output = json.dumps(payload, indent=2, sort_keys=True)
    if getattr(args, "format", "json") != "json":
        output = render_plan_intake_markdown(payload)
    return emit_output(
        output,
        output_path=getattr(args, "output", None),
        pipe_command=getattr(args, "pipe_command", None),
        pipe_args=getattr(args, "pipe_args", None),
        writer=write_output,
    )


def ingest_plan_intent(
    args: Any,
    *,
    repo_root: Path,
) -> PlanIntentIngestionReceipt:
    """Ingest one packet/file/body plan source into typed plan authority."""
    observed_at = utc_timestamp()
    source = source_from_args(args, repo_root=repo_root)
    source_hash = plan_intent_content_hash(source.body)
    store_path = repo_root / DEFAULT_MASTER_PLAN_STORE_REL
    receipt_path = repo_root / PLAN_INTENT_INGESTION_RECEIPT_STORE_REL
    source_snapshot_path = repo_root / PLAN_SOURCE_SNAPSHOT_STORE_REL
    context = ReceiptBuildContext(
        args=args,
        source=source,
        source_hash=source_hash,
        observed_at=observed_at,
        store_path=store_path,
    )

    outcome = _terminal_outcome(args, source_reason=source.reason)
    if outcome is not None:
        return _store_receipt(
            receipt_path,
            build_receipt(context, outcome),
            dry_run=bool(getattr(args, "dry_run", False)),
        )

    rows = rows_from_source(
        args,
        source=source,
        source_hash=source_hash,
        observed_at=observed_at,
    )
    if not rows:
        return _store_receipt(
            receipt_path,
            build_receipt(context, _missing_rows_outcome()),
            dry_run=bool(getattr(args, "dry_run", False)),
        )

    return _write_or_preview_rows(
        args,
        rows=rows,
        context=context,
        store_path=store_path,
        receipt_path=receipt_path,
        source_snapshot_path=source_snapshot_path,
    )


def _terminal_outcome(args: Any, *, source_reason: str) -> ReceiptOutcome | None:
    if source_reason:
        return ReceiptOutcome(
            status="rejected",
            reason=source_reason,
            target_kind="terminal_receipt",
            terminal_status="rejected",
        )
    terminal_status = text(getattr(args, "terminal_status", ""))
    if not terminal_status:
        return None
    return ReceiptOutcome(
        status=terminal_status,
        reason=text(getattr(args, "reason", ""))
        or "explicit_terminal_plan_intent_receipt",
        target_kind="terminal_receipt",
        terminal_status=terminal_status,
    )


def _missing_rows_outcome() -> ReceiptOutcome:
    return ReceiptOutcome(
        status="rejected",
        reason="missing_plan_row_or_checklist_authority",
        target_kind="terminal_receipt",
        terminal_status="rejected",
    )


def _write_or_preview_rows(
    args: Any,
    *,
    rows: tuple[PlanRow, ...],
    context: ReceiptBuildContext,
    store_path: Path,
    receipt_path: Path,
    source_snapshot_path: Path,
) -> PlanIntentIngestionReceipt:
    rows = _merge_rows_with_existing(
        args,
        rows=rows,
        existing_rows=read_plan_rows_jsonl(store_path),
    )
    if bool(getattr(args, "dry_run", False)):
        return build_receipt(
            context,
            ReceiptOutcome(
                status="preview",
                reason="dry_run_plan_rows_not_written",
                target_kind="plan_row",
                row_ids=tuple(row.row_id for row in rows),
                store_statuses=tuple("preview" for _row in rows),
                source_retention_status="preview",
                source_integrity_status="unknown",
                source_completeness_status="unknown",
                source_integrity_checked_at_utc=context.observed_at,
            ),
        )

    rows_with_snapshot_refs = rows_with_source_snapshot_refs(
        rows,
        source=context.source,
        source_hash=context.source_hash,
    )
    stored_rows, store_statuses = _upsert_rows(store_path, rows_with_snapshot_refs)
    snapshots = write_source_snapshots(
        source_snapshot_path,
        rows=stored_rows,
        context=context,
    )
    status, reason, terminal = receipt_status(store_statuses)
    receipt = build_receipt(
        context,
        ReceiptOutcome(
            status=status,
            reason=reason,
            target_kind="plan_row",
            row_ids=tuple(row.row_id for row in stored_rows),
            store_statuses=store_statuses,
            terminal_status=terminal,
                source_snapshot_ids=tuple(snapshot.snapshot_id for snapshot in snapshots),
                source_snapshot_path=str(source_snapshot_path),
                canonical_source_hash=(
                    snapshots[0].body_hash if snapshots else context.source_hash
                ),
                source_packet_expires_at_utc=source_packet_expires_at(context.source),
                source_retention_status=source_retention_status(snapshots),
                source_integrity_status=source_integrity_status(snapshots),
                source_completeness_status=source_completeness_status(snapshots),
                source_required_anchor_count=source_required_anchor_count(snapshots),
                source_matched_anchor_count=source_matched_anchor_count(snapshots),
                source_missing_required_anchors=source_missing_required_anchors(
                    snapshots
                ),
                source_integrity_checked_at_utc=context.observed_at,
            ),
        )
    return append_plan_intent_ingestion_receipt(receipt_path, receipt)


def _merge_rows_with_existing(
    args: Any,
    *,
    rows: tuple[PlanRow, ...],
    existing_rows: tuple[PlanRow, ...],
) -> tuple[PlanRow, ...]:
    existing_by_id = {row.row_id: row for row in existing_rows}
    return tuple(
        _merge_row_with_existing(args, row=row, existing=existing_by_id.get(row.row_id))
        for row in rows
    )


def _merge_row_with_existing(
    args: Any,
    *,
    row: PlanRow,
    existing: PlanRow | None,
) -> PlanRow:
    if existing is None:
        return row
    return replace(
        row,
        title=row.title if text(getattr(args, "title", "")) else existing.title,
        status=(
            row.status
            if _explicit_arg(args, "plan_status", default="queued")
            else existing.status
        ),
        sdlc_stage=(
            row.sdlc_stage
            if _explicit_arg(args, "sdlc_stage", default="spec")
            else existing.sdlc_stage
        ),
        target_ref=(
            row.target_ref
            if text(getattr(args, "target_ref", ""))
            else existing.target_ref
        ),
        sourced_from_packets=_merged_refs(
            existing.sourced_from_packets,
            row.sourced_from_packets,
        ),
        work_evidence_ids=_merged_refs(
            existing.work_evidence_ids,
            row.work_evidence_ids,
        ),
        anchor_refs=_merged_refs(existing.anchor_refs, row.anchor_refs),
        contradicts_packets=_merged_refs(
            existing.contradicts_packets,
            row.contradicts_packets,
        ),
    )


def _explicit_arg(args: Any, name: str, *, default: str = "") -> bool:
    value = text(getattr(args, name, ""))
    return bool(value and value != default)


def _merged_refs(
    existing: tuple[str, ...],
    incoming: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            str(value or "").strip()
            for value in (*existing, *incoming)
            if str(value or "").strip()
        )
    )


def _upsert_rows(
    store_path: Path,
    rows: tuple[PlanRow, ...],
) -> tuple[tuple[PlanRow, ...], tuple[str, ...]]:
    stored_rows: list[PlanRow] = []
    statuses: list[str] = []
    for row in rows:
        with_revision = with_plan_revision(row, read_plan_rows_jsonl(store_path))
        status, stored = upsert_plan_row_jsonl(store_path, with_revision)
        statuses.append(status)
        stored_rows.append(stored)
    return tuple(stored_rows), tuple(statuses)


def _store_receipt(
    path: Path,
    receipt: PlanIntentIngestionReceipt,
    *,
    dry_run: bool,
) -> PlanIntentIngestionReceipt:
    if dry_run:
        return receipt
    return append_plan_intent_ingestion_receipt(path, receipt)


__all__ = ["ingest_plan_intent", "run_ingest_plan"]
