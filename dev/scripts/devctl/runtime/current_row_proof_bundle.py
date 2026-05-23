"""Typed current-row proof bundle assembly."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from dev.scripts.checks.check_bootstrap import utc_timestamp

from .current_row_proof_collaboration import CollaborationProof
from .current_row_proof_config import (
    CONTRACT_ID,
    DEFAULT_CLOSURE_RECEIPTS_PATH,
    DEFAULT_COLLABORATION_EVIDENCE_PATHS,
    DEFAULT_DOGFOOD_OUTPUT_PATHS,
    DEFAULT_FEATURE_PROOF_DIR,
    DEFAULT_FINAL_GATE_PATHS,
    DEFAULT_GUARD_OUTPUT_PATHS,
    DEFAULT_INGESTION_RECEIPTS_PATH,
    DEFAULT_PLAN_INDEX_PATH,
    DEFAULT_PROJECTION_PATH,
    DEFAULT_ROW_ID,
    DEFAULT_SNAPSHOTS_PATH,
    REQUIRED_ACTOR_ROLE_SESSION_EVIDENCE,
    REQUIRED_DOGFOOD_COMMANDS,
    REQUIRED_GUARD_IDS,
    REQUIRED_RECEIPT_TYPES,
    REQUIRED_TEST_COMMANDS,
)
from .current_row_proof_evidence import ProofEvidence
from .current_row_proof_projection import (
    render_current_row_projection,
    typed_state_hash,
    validate_projection_sync,
)
from .current_row_proof_requirements import (
    execution_items,
    failure,
    failures_from_requirements,
    next_bounded_command,
    proof_requirements,
)
from .current_row_proof_utils import ProofUtils as U


def build_current_row_proof_bundle(
    *,
    row_id: str = DEFAULT_ROW_ID,
    plan_index_path: Path = DEFAULT_PLAN_INDEX_PATH,
    snapshots_path: Path = DEFAULT_SNAPSHOTS_PATH,
    ingestion_receipts_path: Path = DEFAULT_INGESTION_RECEIPTS_PATH,
    closure_receipts_path: Path = DEFAULT_CLOSURE_RECEIPTS_PATH,
    feature_proof_dir: Path = DEFAULT_FEATURE_PROOF_DIR,
    guard_output_paths: Sequence[Path] = DEFAULT_GUARD_OUTPUT_PATHS,
    dogfood_output_paths: Sequence[Path] = DEFAULT_DOGFOOD_OUTPUT_PATHS,
    collaboration_evidence_paths: Sequence[Path] = DEFAULT_COLLABORATION_EVIDENCE_PATHS,
    final_gate_paths: Sequence[Path] = DEFAULT_FINAL_GATE_PATHS,
) -> dict[str, object]:
    """Build the typed current-row proof bundle from durable state and outputs."""
    row_id = row_id.strip()
    plan_rows = tuple(U.iter_jsonish(plan_index_path))
    plan_row = ProofEvidence.find_plan_row(plan_rows, row_id)
    work_evidence_ids = tuple(U.strings(plan_row.get("work_evidence_ids"))) if plan_row else ()
    source_snapshot_id = U.last_prefixed(work_evidence_ids, "plan_source_snapshot:")
    ingestion_receipt_id = U.last_prefixed(work_evidence_ids, "plan_intent_receipt:")

    snapshot = ProofEvidence.find_source_snapshot(
        snapshots_path=snapshots_path,
        row_id=row_id,
        snapshot_id=source_snapshot_id,
    )
    ingestion_receipt = ProofEvidence.find_ingestion_receipt(
        ingestion_receipts_path=ingestion_receipts_path,
        row_id=row_id,
        receipt_id=ingestion_receipt_id,
        snapshot_id=str(snapshot.get("snapshot_id") or source_snapshot_id),
    )
    source_snapshot_id = source_snapshot_id or str(snapshot.get("snapshot_id") or "")
    ingestion_receipt_id = ingestion_receipt_id or str(ingestion_receipt.get("receipt_id") or "")

    guard_statuses = ProofEvidence.guard_statuses(guard_output_paths, row_id=row_id)
    dogfood_statuses = ProofEvidence.dogfood_statuses(dogfood_output_paths, row_id=row_id)
    final_gate_status = ProofEvidence.final_gate_status(final_gate_paths, row_id=row_id)
    feature_proof = ProofEvidence.feature_proof_status(feature_proof_dir, row_id=row_id)
    closure = ProofEvidence.closure_status(closure_receipts_path, row_id=row_id)
    collaboration = CollaborationProof.status(
        collaboration_evidence_paths,
        row_id=row_id,
        plan_rows=plan_rows,
        not_before_timestamp=U.last_updated_timestamp(snapshot, ingestion_receipt),
    )

    requirements = proof_requirements(
        plan_row=plan_row,
        snapshot=snapshot,
        ingestion_receipt=ingestion_receipt,
        guard_statuses=guard_statuses,
        dogfood_statuses=dogfood_statuses,
        final_gate_status=final_gate_status,
        feature_proof=feature_proof,
        closure=closure,
        collaboration=collaboration,
    )
    failures = failures_from_requirements(requirements)
    if final_gate_status["status"] == "passed" and feature_proof["status"] != "passed":
        failures.append(
            failure(
                "final_gate_allowed_without_feature_proof_receipt",
                "Final gate output claims closure before FeatureProofReceipt(proven_passed).",
                "Emit a proven FeatureProofReceipt with exact pytest node evidence before closure.",
                "FeatureProofReceipt",
            )
        )

    next_command = next_bounded_command(requirements, failures)
    report = {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "mode": "current_row_proof",
        "command": "check_current_row_proof_bundle",
        "timestamp": utc_timestamp(),
        "ok": not failures,
        "row_id": row_id,
        "source_snapshot_id": source_snapshot_id,
        "source_snapshot_hash": str(snapshot.get("body_hash") or snapshot.get("source_hash") or ""),
        "source_hash": U.source_hash(plan_row, snapshot, ingestion_receipt),
        "source_ref": str(snapshot.get("source_ref") or U.nested(plan_row, ("provenance", "source_file")) or ""),
        "ingestion_receipt_id": ingestion_receipt_id,
        "current_plan_row_status": str(plan_row.get("status") or "") if plan_row else "",
        "current_bounded_next_command": next_command,
        "next_bounded_command": next_command,
        "actor_role_session_state": collaboration["actor_role_session_state"],
        "active_packet_refs": collaboration["active_packet_refs"],
        "execution_items": execution_items(),
        "proof_requirements": requirements,
        "required_guard_ids": list(REQUIRED_GUARD_IDS),
        "required_test_commands": list(REQUIRED_TEST_COMMANDS),
        "required_dogfood_commands": list(REQUIRED_DOGFOOD_COMMANDS),
        "required_receipt_types": list(REQUIRED_RECEIPT_TYPES),
        "required_actor_role_session_evidence": list(REQUIRED_ACTOR_ROLE_SESSION_EVIDENCE),
        "guard_statuses": guard_statuses,
        "test_statuses": ProofEvidence.test_statuses(feature_proof),
        "dogfood_statuses": dogfood_statuses,
        "final_gate_status": final_gate_status,
        "feature_proof_receipt_status": feature_proof,
        "closure_receipt_status": closure,
        "collaboration_status": collaboration,
        "status": "complete" if not failures else "blocked",
        "failure_count": len(failures),
        "failures": failures,
        "last_updated_timestamp": U.last_updated_timestamp(
            plan_row,
            snapshot,
            ingestion_receipt,
            feature_proof,
            closure,
            final_gate_status,
            guard_statuses,
            dogfood_statuses,
            collaboration,
        ),
    }
    report["typed_state_hash"] = typed_state_hash(report)
    return report


__all__ = [
    "CONTRACT_ID",
    "DEFAULT_COLLABORATION_EVIDENCE_PATHS",
    "DEFAULT_CLOSURE_RECEIPTS_PATH",
    "DEFAULT_DOGFOOD_OUTPUT_PATHS",
    "DEFAULT_FEATURE_PROOF_DIR",
    "DEFAULT_FINAL_GATE_PATHS",
    "DEFAULT_GUARD_OUTPUT_PATHS",
    "DEFAULT_INGESTION_RECEIPTS_PATH",
    "DEFAULT_PLAN_INDEX_PATH",
    "DEFAULT_PROJECTION_PATH",
    "DEFAULT_ROW_ID",
    "DEFAULT_SNAPSHOTS_PATH",
    "REQUIRED_GUARD_IDS",
    "build_current_row_proof_bundle",
    "render_current_row_projection",
    "typed_state_hash",
    "validate_projection_sync",
]
