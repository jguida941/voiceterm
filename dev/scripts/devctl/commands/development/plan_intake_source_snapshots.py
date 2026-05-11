"""PlanSourceSnapshot write helpers for plan-intent ingestion."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ...runtime.master_plan_contract import PlanRow
from ...runtime.plan_intent_ingestion import plan_intent_receipt_ref, typed_action_ref
from ...runtime.plan_source_retention import (
    PlanSourceSnapshot,
    build_plan_source_snapshot,
    plan_source_snapshot_id,
    upsert_plan_source_snapshots,
)
from .plan_intake_phase0 import Phase0IntakeMetadata
from .plan_intake_receipts import ReceiptBuildContext
from .plan_intake_support import text


def rows_with_source_snapshot_refs(
    rows: tuple[PlanRow, ...],
    *,
    source,
    source_hash: str,
    receipt_id: str,
    action_id: str,
) -> tuple[PlanRow, ...]:
    """Link rows to the durable source snapshot that will be written."""
    next_rows: list[PlanRow] = []
    for row in rows:
        snapshot_id = plan_source_snapshot_id(
            plan_row_id=row.row_id,
            source_kind=source.kind,
            source_ref=source.ref,
            source_hash=source_hash,
        )
        evidence = list(row.work_evidence_ids)
        ref = f"plan_source_snapshot:{snapshot_id}"
        if ref not in evidence:
            evidence.append(ref)
        receipt_ref = plan_intent_receipt_ref(receipt_id)
        if receipt_ref and receipt_ref not in evidence:
            evidence.append(receipt_ref)
        action_ref = typed_action_ref(action_id)
        if action_ref and action_ref not in evidence:
            evidence.append(action_ref)
        next_rows.append(replace(row, work_evidence_ids=tuple(evidence)))
    return tuple(next_rows)


def write_source_snapshots(
    path: Path,
    *,
    rows: tuple[PlanRow, ...],
    context: ReceiptBuildContext,
    receipt_id: str,
    action_id: str,
    phase0_metadata: Phase0IntakeMetadata | None = None,
) -> tuple[PlanSourceSnapshot, ...]:
    """Write durable source snapshots for stored PlanRows."""
    source = context.source
    packet_id = text(source.packet_payload.get("packet_id"))
    packet_expires_at = source_packet_expires_at(source)
    snapshots: list[PlanSourceSnapshot] = []
    for row in rows:
        disposition = (
            phase0_metadata.entry_for_row(row.row_id) if phase0_metadata is not None else None
        )
        snapshot = build_plan_source_snapshot(
            plan_row_id=row.row_id,
            source_kind=source.kind,
            source_ref=source.ref,
            source_hash=context.source_hash,
            source_text=source.body,
            captured_at_utc=context.observed_at,
            receipt_id=receipt_id,
            action_id=action_id,
            source_packet_id=packet_id,
            packet_expires_at_utc=packet_expires_at,
            composition_disposition=(
                disposition.disposition if disposition is not None else ""
            ),
            owning_mp_family=(
                disposition.owning_mp_family if disposition is not None else ""
            ),
            existing_owner_row_refs=(
                disposition.existing_owner_row_refs if disposition is not None else ()
            ),
            packet_binding_refs=(
                disposition.packet_binding_refs if disposition is not None else ()
            ),
            why_not_duplicate=(
                disposition.why_not_duplicate if disposition is not None else ""
            ),
            phase_allowed_to_block=(
                disposition.phase_allowed_to_block if disposition is not None else ""
            ),
            phase_allowed_to_mutate=(
                disposition.phase_allowed_to_mutate if disposition is not None else ""
            ),
            schema_limit_warning=(
                phase0_metadata.schema_limit_warning if phase0_metadata is not None else ""
            ),
        )
        snapshots.append(snapshot)
    return upsert_plan_source_snapshots(path, tuple(snapshots))


def source_packet_expires_at(source) -> str:
    return text(source.packet_payload.get("expires_at_utc"))


def source_retention_status(snapshots: tuple[PlanSourceSnapshot, ...]) -> str:
    if not snapshots:
        return "missing"
    statuses = {snapshot.retention_status for snapshot in snapshots}
    if "protected" in statuses:
        return "protected"
    if statuses == {"snapshotted"}:
        return "snapshotted"
    return sorted(statuses)[0] if statuses else "unknown"


def source_integrity_status(snapshots: tuple[PlanSourceSnapshot, ...]) -> str:
    if not snapshots:
        return "dangling"
    statuses = {snapshot.source_integrity_status for snapshot in snapshots}
    if statuses == {"ok"}:
        return "ok"
    if "dangling" in statuses:
        return "dangling"
    return sorted(statuses)[0] if statuses else "unknown"


def source_completeness_status(snapshots: tuple[PlanSourceSnapshot, ...]) -> str:
    if not snapshots:
        return "dangling"
    statuses = {snapshot.source_completeness_status for snapshot in snapshots}
    if statuses == {"full_plan_retained"}:
        return "full_plan_retained"
    if statuses == {"not_required"}:
        return "not_required"
    if "missing_required_anchors" in statuses:
        return "missing_required_anchors"
    return sorted(statuses)[0] if statuses else "unknown"


def source_required_anchor_count(snapshots: tuple[PlanSourceSnapshot, ...]) -> int:
    return max((snapshot.required_anchor_count for snapshot in snapshots), default=0)


def source_matched_anchor_count(snapshots: tuple[PlanSourceSnapshot, ...]) -> int:
    return max((snapshot.matched_anchor_count for snapshot in snapshots), default=0)


def source_missing_required_anchors(
    snapshots: tuple[PlanSourceSnapshot, ...],
) -> tuple[str, ...]:
    missing: list[str] = []
    for snapshot in snapshots:
        missing.extend(snapshot.missing_required_anchors)
    return tuple(dict.fromkeys(missing))


__all__ = [
    "rows_with_source_snapshot_refs",
    "source_completeness_status",
    "source_integrity_status",
    "source_matched_anchor_count",
    "source_missing_required_anchors",
    "source_packet_expires_at",
    "source_required_anchor_count",
    "source_retention_status",
    "write_source_snapshots",
]
