"""Governed-exception closure helpers for bypass lifecycle expiry."""

from __future__ import annotations

from dataclasses import dataclass

from .bypass_lifecycle_models import (
    BypassExpiry,
    BypassExpirySource,
    BypassLifecycleState,
)
from .governed_exception_lifecycle import GovernedExceptionLifecycle
from .governed_exception_receipts import ClosureProof, ResolutionReceipt


@dataclass(frozen=True, slots=True)
class BypassExceptionClosureInput:
    expiry: BypassExpiry
    state: BypassLifecycleState
    expired_at_utc: str
    reason: str
    source: BypassExpirySource
    evidence_refs: tuple[str, ...]


def closed_governed_exception_for_bypass_expiry(
    governed_exception: GovernedExceptionLifecycle | None,
    closure: BypassExceptionClosureInput,
) -> GovernedExceptionLifecycle | None:
    """Return a closed exception lifecycle for a terminal bypass transition."""
    if governed_exception is None:
        return None

    closure_proof_id = f"closure-proof:{governed_exception.lifecycle_id}:bypass-expiry"
    resolution_id = f"resolution:{governed_exception.lifecycle_id}:bypass-expiry"

    closure_proof = ClosureProof(
        closure_proof_id=closure_proof_id,
        exception_lifecycle_id=governed_exception.lifecycle_id,
        normal_command="python3 dev/scripts/devctl.py bypass expire",
        validation_receipt_id=closure.expiry.expiry_id,
        exception_used=True,
        proof_artifacts=_proof_artifacts(
            closure.expiry,
            evidence_refs=closure.evidence_refs,
        ),
    )

    resolution = ResolutionReceipt(
        resolution_id=resolution_id,
        exception_lifecycle_id=governed_exception.lifecycle_id,
        finding_id=governed_exception.finding_id,
        status="closed",
        root_cause_class=f"bypass_lifecycle_{closure.source.value}",
        root_cause_summary=closure.reason,
        validation_receipt_id=closure.expiry.expiry_id,
        closure_proof_id=closure_proof_id,
        exception_used=True,
        closed_at_utc=closure.expired_at_utc,
        closure_reason=f"BypassLifecycle moved to {closure.state.value}.",
    )

    return GovernedExceptionLifecycle(
        lifecycle_id=governed_exception.lifecycle_id,
        status="closed",
        exception=governed_exception.exception,
        resolution=resolution,
        closure_proof=closure_proof,
        finding_id=governed_exception.finding_id,
        planned_finding_ingest_ref=governed_exception.planned_finding_ingest_ref,
        validation_plan_id=governed_exception.validation_plan_id,
        authority_evidence_refs=governed_exception.authority_evidence_refs,
        worktree_safety_evidence_refs=governed_exception.worktree_safety_evidence_refs,
        system_map_contract_ids=governed_exception.system_map_contract_ids,
        developer_loop_refs=governed_exception.developer_loop_refs,
        learning_refs=governed_exception.learning_refs,
        projection_refs=governed_exception.projection_refs,
        resolution_receipt_id=resolution_id,
        created_at_utc=governed_exception.created_at_utc,
        updated_at_utc=closure.expired_at_utc,
    )


def _proof_artifacts(
    expiry: BypassExpiry,
    *,
    evidence_refs: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(
        ref
        for ref in dict.fromkeys(
            (
                f"bypass_expiry:{expiry.expiry_id}",
                f"bypass_receipt:{expiry.receipt_id}" if expiry.receipt_id else "",
                *evidence_refs,
            )
        )
        if ref
    )


__all__ = [
    "BypassExceptionClosureInput",
    "closed_governed_exception_for_bypass_expiry",
]
