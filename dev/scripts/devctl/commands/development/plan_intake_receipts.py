"""Receipt construction for plan-intent ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...runtime.plan_ingestion_phase0_models import (
    CommandManifestProof,
    GuardMaturityRecord,
    PlanCompositionDispositionEntry,
    ReceiptCoverageInventory,
    RepoStateFingerprint,
)
from ...runtime.plan_intent_ingestion import (
    PlanIntentIngestionReceipt,
    plan_intent_action_id,
    plan_intent_receipt_id,
)
from ...runtime.derived_state_invalidation import plan_ingestion_invalidation_payload
from ...runtime.correlation_spine import (
    causation_id_for_ref,
    correlation_id_for_ref,
    run_id_for_ref,
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
    composition_disposition_matrix: tuple[PlanCompositionDispositionEntry, ...] = ()
    command_manifest_proofs: tuple[CommandManifestProof, ...] = ()
    guard_maturity_records: tuple[GuardMaturityRecord, ...] = ()
    repo_state_fingerprint: RepoStateFingerprint | None = None
    receipt_coverage_inventory: ReceiptCoverageInventory | None = None
    schema_limit_warning: str = ""


@dataclass(frozen=True, slots=True)
class ReceiptBindingIds:
    """Deterministic ids shared by row, receipt, and snapshot bindings."""

    receipt_id: str
    action_id: str
    target_ref: str


def receipt_binding_ids(context: ReceiptBuildContext) -> ReceiptBindingIds:
    """Return deterministic receipt/action ids for one ingestion attempt."""
    target_ref = target_ref_from_source(context.args, context.source)
    return ReceiptBindingIds(
        receipt_id=plan_intent_receipt_id(
            source_kind=context.source.kind,
            source_ref=context.source.ref,
            source_hash=context.source_hash,
            recorded_at_utc=context.observed_at,
        ),
        action_id=plan_intent_action_id(
            source_kind=context.source.kind,
            source_ref=context.source.ref,
            source_hash=context.source_hash,
            target_ref=target_ref,
            recorded_at_utc=context.observed_at,
        ),
        target_ref=target_ref,
    )


def build_receipt(
    context: ReceiptBuildContext,
    outcome: ReceiptOutcome,
) -> PlanIntentIngestionReceipt:
    """Build a typed plan-intent ingestion receipt."""
    source = context.source
    packet = source.packet_payload
    binding_ids = receipt_binding_ids(context)
    dry_run = bool(getattr(context.args, "dry_run", False))
    derived_state_invalidation = plan_ingestion_invalidation_payload(
        source_ref=source.ref,
        packet_id=text(packet.get("packet_id")),
        receipt_id=binding_ids.receipt_id,
        action_id=binding_ids.action_id,
        row_ids=outcome.row_ids,
        target_ref=binding_ids.target_ref,
        status=outcome.status,
        store_statuses=outcome.store_statuses,
        invalidated=not dry_run,
    )
    return PlanIntentIngestionReceipt(
        receipt_id=binding_ids.receipt_id,
        action_id=binding_ids.action_id,
        source_kind=source.kind,
        source_ref=source.ref,
        status=outcome.status,
        reason=outcome.reason,
        target_kind=outcome.target_kind,
        target_ref=binding_ids.target_ref,
        correlation_id=correlation_id_for_ref("typed_action", binding_ids.action_id),
        causation_id=causation_id_for_ref(source.kind, source.ref),
        run_id=run_id_for_ref("plan_intent_ingestion", context.observed_at),
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
        composition_disposition_matrix=outcome.composition_disposition_matrix,
        command_manifest_proofs=outcome.command_manifest_proofs,
        guard_maturity_records=outcome.guard_maturity_records,
        repo_state_fingerprint=outcome.repo_state_fingerprint,
        receipt_coverage_inventory=outcome.receipt_coverage_inventory,
        schema_limit_warning=outcome.schema_limit_warning,
        derived_state_invalidated=not dry_run,
        derived_state_invalidation=derived_state_invalidation,
        recorded_at_utc=context.observed_at,
        dry_run=dry_run,
    )


def receipt_status(statuses: tuple[str, ...]) -> tuple[str, str, str]:
    """Return receipt status, reason, and optional terminal class."""
    if statuses and all(status == "already_present" for status in statuses):
        return "duplicate", "plan_rows_already_present", "duplicate"
    if any(status in {"inserted", "updated"} for status in statuses):
        return "accepted", "plan_rows_upserted", ""
    return "rejected", "plan_rows_not_written", "rejected"


__all__ = [
    "ReceiptBindingIds",
    "ReceiptBuildContext",
    "ReceiptOutcome",
    "build_receipt",
    "receipt_binding_ids",
    "receipt_status",
]
