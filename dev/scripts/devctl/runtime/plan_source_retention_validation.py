"""Validation helpers for retained plan source snapshots."""

from __future__ import annotations

from collections.abc import Mapping

from .master_plan_contract import PlanRow
from .plan_source_retention_anchors import (
    REQUIRED_FULL_PLAN_ANCHORS_BY_ROW_ID,
    missing_required_plan_source_anchors,
)
from .plan_source_retention_models import (
    PlanSourceSnapshot,
    plan_source_body_hash,
)
from .value_coercion import coerce_string, coerce_string_items

ACCEPTED_PLAN_SOURCE_RECEIPT_STATUSES = frozenset({"accepted"})


def validate_plan_row_source_retention(
    row: PlanRow,
    snapshots: tuple[PlanSourceSnapshot, ...],
) -> tuple[str, ...]:
    """Return validation errors for packet-sourced PlanRow source retention."""
    errors: list[str] = []
    snapshot_ids = _snapshot_ids_from_row(row)
    if not row.sourced_from_packets and not snapshot_ids:
        return ()
    matching = _matching_snapshots(row, snapshots, snapshot_ids=snapshot_ids)
    if not matching:
        return ("missing_plan_source_snapshot",)
    packet_ids = set(row.sourced_from_packets)
    if packet_ids and not any(
        snapshot.source_packet_id in packet_ids for snapshot in matching
    ):
        errors.append("plan_source_snapshot_packet_mismatch")
    valid_reconstructable = tuple(
        snapshot for snapshot in matching if _snapshot_reconstructable(row, snapshot)
    )
    if not valid_reconstructable:
        errors.append("plan_source_snapshot_not_reconstructable")
    errors.extend(_missing_full_plan_anchor_errors(row.row_id, matching))
    return tuple(errors)


def validate_current_plan_source_retention(
    row: PlanRow,
    snapshots: tuple[PlanSourceSnapshot, ...],
    receipts: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    """Validate the latest accepted ingestion receipt points at full source."""
    errors = list(validate_plan_row_source_retention(row, snapshots))
    if row.row_id not in REQUIRED_FULL_PLAN_ANCHORS_BY_ROW_ID:
        return tuple(errors)

    receipt = latest_accepted_plan_source_receipt(row.row_id, receipts)
    if receipt is None:
        errors.append("missing_latest_accepted_plan_ingestion_receipt")
        return tuple(dict.fromkeys(errors))

    current_snapshots, current_errors = _current_receipt_snapshots(
        row,
        snapshots,
        receipt,
    )
    errors.extend(current_errors)
    if not current_snapshots:
        return tuple(dict.fromkeys(errors))

    if not any(
        _snapshot_reconstructable(row, snapshot) for snapshot in current_snapshots
    ):
        errors.append("current_plan_source_snapshot_not_reconstructable")
    errors.extend(
        error.replace("missing_full_plan_anchor:", "current_missing_full_plan_anchor:")
        for error in _missing_full_plan_anchor_errors(row.row_id, current_snapshots)
    )
    errors.extend(_current_receipt_metadata_errors(receipt, current_snapshots))
    return tuple(dict.fromkeys(errors))


def latest_accepted_plan_source_receipt(
    row_id: str,
    receipts: tuple[Mapping[str, object], ...],
) -> Mapping[str, object] | None:
    """Return the latest accepted ingestion receipt for one PlanRow id."""
    latest: tuple[str, int, Mapping[str, object]] | None = None
    for index, receipt in enumerate(receipts):
        if (
            coerce_string(receipt.get("status"))
            not in ACCEPTED_PLAN_SOURCE_RECEIPT_STATUSES
        ):
            continue
        if row_id not in coerce_string_items(receipt.get("row_ids")):
            continue
        recorded_at = coerce_string(receipt.get("recorded_at_utc"))
        candidate = (recorded_at, index, receipt)
        if latest is None or candidate[:2] > latest[:2]:
            latest = candidate
    return latest[2] if latest is not None else None


def _matching_snapshots(
    row: PlanRow,
    snapshots: tuple[PlanSourceSnapshot, ...],
    *,
    snapshot_ids: set[str],
) -> tuple[PlanSourceSnapshot, ...]:
    if snapshot_ids:
        return tuple(
            snapshot
            for snapshot in snapshots
            if snapshot.plan_row_id == row.row_id and snapshot.snapshot_id in snapshot_ids
        )
    return tuple(snapshot for snapshot in snapshots if snapshot.plan_row_id == row.row_id)


def _current_receipt_snapshots(
    row: PlanRow,
    snapshots: tuple[PlanSourceSnapshot, ...],
    receipt: Mapping[str, object],
) -> tuple[tuple[PlanSourceSnapshot, ...], tuple[str, ...]]:
    snapshot_ids = coerce_string_items(receipt.get("source_snapshot_ids"))
    if not snapshot_ids:
        return (), ("latest_receipt_missing_source_snapshot",)

    by_id = {snapshot.snapshot_id: snapshot for snapshot in snapshots}
    current: list[PlanSourceSnapshot] = []
    errors: list[str] = []
    evidence_ids = _snapshot_ids_from_row(row)
    for snapshot_id in snapshot_ids:
        snapshot = by_id.get(snapshot_id)
        if snapshot is None:
            errors.append(f"latest_receipt_source_snapshot_missing:{snapshot_id}")
            continue
        if snapshot.plan_row_id != row.row_id:
            continue
        current.append(snapshot)
        if snapshot_id not in evidence_ids:
            errors.append(f"plan_row_missing_latest_source_snapshot_ref:{snapshot_id}")
    if not current:
        errors.append("latest_receipt_source_snapshot_row_mismatch")
    return tuple(current), tuple(errors)


def _current_receipt_metadata_errors(
    receipt: Mapping[str, object],
    snapshots: tuple[PlanSourceSnapshot, ...],
) -> tuple[str, ...]:
    errors: list[str] = []
    receipt_hash = coerce_string(receipt.get("canonical_source_hash"))
    if receipt_hash and not any(
        snapshot.body_hash == receipt_hash for snapshot in snapshots
    ):
        errors.append("latest_receipt_canonical_source_hash_mismatch")
    completeness = coerce_string(receipt.get("source_completeness_status"))
    if completeness and completeness != "full_plan_retained":
        errors.append("latest_receipt_source_completeness_not_full_plan")
    return tuple(errors)


def _snapshot_reconstructable(row: PlanRow, snapshot: PlanSourceSnapshot) -> bool:
    if snapshot.retention_status not in {"protected", "snapshotted"}:
        return False
    if snapshot.source_integrity_status not in {"ok", "packet_expired_snapshot_ok"}:
        return False
    if not snapshot.source_text:
        return False
    if snapshot.body_hash != plan_source_body_hash(snapshot.source_text):
        return False
    if row.content_hash and snapshot.source_hash != row.content_hash:
        return False
    if missing_required_plan_source_anchors(row.row_id, snapshot.source_text):
        return False
    return True


def _missing_full_plan_anchor_errors(
    row_id: str,
    snapshots: tuple[PlanSourceSnapshot, ...],
) -> tuple[str, ...]:
    missing: list[str] = []
    for snapshot in snapshots:
        if snapshot.source_completeness_status == "full_plan_retained":
            continue
        anchors = (
            snapshot.missing_required_anchors
            or missing_required_plan_source_anchors(
                row_id,
                snapshot.source_text,
            )
        )
        for anchor in anchors:
            missing.append(f"missing_full_plan_anchor:{anchor}")
    return tuple(dict.fromkeys(missing))


def _snapshot_ids_from_row(row: PlanRow) -> set[str]:
    prefix = "plan_source_snapshot:"
    return {
        item[len(prefix) :]
        for item in row.work_evidence_ids
        if item.startswith(prefix) and item[len(prefix) :]
    }


__all__ = [
    "ACCEPTED_PLAN_SOURCE_RECEIPT_STATUSES",
    "latest_accepted_plan_source_receipt",
    "validate_current_plan_source_retention",
    "validate_plan_row_source_retention",
]
