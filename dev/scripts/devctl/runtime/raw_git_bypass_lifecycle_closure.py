"""Close raw-git governed exceptions with commit-anchor proof."""

from __future__ import annotations

from collections.abc import Mapping

from .governed_exception_lifecycle import GovernedExceptionLifecycle
from .governed_exception_receipts import ClosureProof, ResolutionReceipt
from .governed_transition_typechecker import (
    COMMIT_ANCHOR_CLOSURE_EVENT,
    GovernedTransitionCheck,
    GovernedTransitionInput,
    check_governed_exception_transition,
)
from .raw_git_bypass_receipts import (
    RAW_GIT_BYPASS_GUARD_ID,
    RawGitBypassReceipt,
)

RAW_GIT_COMMIT_ANCHOR_STATUS = "closed_via_commit_anchor"


def raw_git_receipt_ref(receipt_id: str) -> str:
    """Return the canonical evidence ref for a RawGitBypassReceipt."""
    normalized = receipt_id.strip()
    if not normalized:
        return ""
    if normalized.startswith("raw_git_bypass_receipt:"):
        return normalized
    return f"raw_git_bypass_receipt:{normalized}"


def raw_git_receipt_id_for_lifecycle(
    lifecycle: GovernedExceptionLifecycle,
) -> str:
    """Extract the RawGitBypassReceipt id linked to a governed exception row."""
    for ref in (
        lifecycle.planned_finding_ingest_ref,
        lifecycle.exception.planned_finding_ingest_ref if lifecycle.exception else "",
    ):
        normalized = ref.strip()
        if normalized.startswith("raw_git_bypass_receipt:"):
            return normalized.removeprefix("raw_git_bypass_receipt:")
    if lifecycle.exception and lifecycle.exception.receipt_id.startswith("exception:"):
        return lifecycle.exception.receipt_id.removeprefix("exception:")
    return ""


def is_open_raw_git_bypass_lifecycle(
    lifecycle: GovernedExceptionLifecycle,
) -> bool:
    """Return true for raw-git exception rows still awaiting typed closure."""
    return (
        lifecycle.status.strip() == "operator_approved"
        and lifecycle.exception is not None
        and lifecycle.exception.guard_id == RAW_GIT_BYPASS_GUARD_ID
        and lifecycle.closure_proof is None
    )


def close_raw_git_bypass_lifecycle(
    lifecycle: GovernedExceptionLifecycle,
    *,
    receipt: RawGitBypassReceipt | None = None,
    closed_at_utc: str,
    normal_command: str,
    evidence_index: Mapping[str, object] | None = None,
) -> tuple[GovernedExceptionLifecycle, GovernedTransitionCheck]:
    """Build and typecheck a closed raw-git lifecycle row."""
    if not is_open_raw_git_bypass_lifecycle(lifecycle):
        raise ValueError("not_open_raw_git_bypass_lifecycle")

    receipt_id = raw_git_receipt_id_for_lifecycle(lifecycle)
    commit_sha = _commit_anchor(lifecycle, receipt=receipt)
    if not commit_sha:
        raise ValueError("missing_commit_anchor")

    receipt_ref = raw_git_receipt_ref(receipt_id)
    validation_receipt_id = receipt_ref or f"commit:{commit_sha}"
    closure_proof_id = (
        f"closure-proof:{lifecycle.lifecycle_id}:raw-git-commit-anchor"
    )
    resolution_id = f"resolution:{lifecycle.lifecycle_id}:raw-git-commit-anchor"
    proof_artifacts = _proof_artifacts(
        commit_sha=commit_sha,
        receipt_ref=receipt_ref,
        lifecycle=lifecycle,
    )

    closure_proof = ClosureProof(
        closure_proof_id=closure_proof_id,
        exception_lifecycle_id=lifecycle.lifecycle_id,
        normal_command=normal_command,
        validation_receipt_id=validation_receipt_id,
        exception_used=True,
        remote_ref_verified=_remote_ref_verified(lifecycle, receipt=receipt),
        post_push_green=_post_push_green(lifecycle, receipt=receipt),
        proof_artifacts=proof_artifacts,
    )
    resolution = ResolutionReceipt(
        resolution_id=resolution_id,
        exception_lifecycle_id=lifecycle.lifecycle_id,
        finding_id=lifecycle.finding_id,
        status=RAW_GIT_COMMIT_ANCHOR_STATUS,
        root_cause_class="raw_git_bypass_commit_anchor",
        root_cause_summary=(
            "Raw git bypass debt closed by anchoring the exception lifecycle "
            f"to commit {commit_sha}."
        ),
        fixed_by_commit=commit_sha,
        validation_receipt_id=validation_receipt_id,
        closure_proof_id=closure_proof_id,
        exception_used=True,
        remote_ref_verified=_remote_ref_verified(lifecycle, receipt=receipt),
        post_push_green=_post_push_green(lifecycle, receipt=receipt),
        closed_at_utc=closed_at_utc,
        closure_reason="CommitAnchorClosureProof accepted by governed transition typechecker.",
    )

    closed = GovernedExceptionLifecycle(
        lifecycle_id=lifecycle.lifecycle_id,
        status=RAW_GIT_COMMIT_ANCHOR_STATUS,
        exception=lifecycle.exception,
        resolution=resolution,
        closure_proof=closure_proof,
        finding_id=lifecycle.finding_id,
        planned_finding_ingest_ref=lifecycle.planned_finding_ingest_ref,
        validation_plan_id=lifecycle.validation_plan_id,
        authority_evidence_refs=lifecycle.authority_evidence_refs,
        worktree_safety_evidence_refs=lifecycle.worktree_safety_evidence_refs,
        system_map_contract_ids=lifecycle.system_map_contract_ids,
        developer_loop_refs=lifecycle.developer_loop_refs,
        learning_refs=lifecycle.learning_refs,
        projection_refs=lifecycle.projection_refs,
        resolution_receipt_id=resolution_id,
        created_at_utc=lifecycle.created_at_utc,
        updated_at_utc=closed_at_utc,
    )
    evidence = (
        evidence_index
        if evidence_index is not None
        else _evidence_index(
            closure_proof=closure_proof,
            commit_sha=commit_sha,
        )
    )
    check = check_governed_exception_transition(
        GovernedTransitionInput(
            before=lifecycle,
            after=closed,
            event_kind=COMMIT_ANCHOR_CLOSURE_EVENT,
            evidence_index=evidence,
            closure_proof=closure_proof,
        )
    )
    return closed, check


def _commit_anchor(
    lifecycle: GovernedExceptionLifecycle,
    *,
    receipt: RawGitBypassReceipt | None,
) -> str:
    if lifecycle.exception and lifecycle.exception.head:
        return lifecycle.exception.head
    if receipt is None:
        return ""
    if receipt.commit_sha:
        return receipt.commit_sha
    if receipt.push_range:
        return receipt.push_range[1]
    return ""


def _proof_artifacts(
    *,
    commit_sha: str,
    receipt_ref: str,
    lifecycle: GovernedExceptionLifecycle,
) -> tuple[str, ...]:
    refs = [
        f"commit:{commit_sha}",
        receipt_ref,
        lifecycle.planned_finding_ingest_ref,
    ]
    refs.extend(lifecycle.authority_evidence_refs)
    refs.extend(lifecycle.worktree_safety_evidence_refs)
    return tuple(dict.fromkeys(ref for ref in refs if ref))


def _evidence_index(
    *,
    closure_proof: ClosureProof,
    commit_sha: str,
) -> dict[str, object]:
    refs = tuple(
        dict.fromkeys(
            (
                closure_proof.validation_receipt_id,
                *closure_proof.proof_artifacts,
                f"commit:{commit_sha}",
                commit_sha,
            )
        )
    )
    return {
        "refs": refs,
        "commit_shas": (commit_sha,),
        **{ref: {"kind": "raw_git_commit_anchor"} for ref in refs},
    }


def _remote_ref_verified(
    lifecycle: GovernedExceptionLifecycle,
    *,
    receipt: RawGitBypassReceipt | None,
) -> bool:
    if lifecycle.exception and lifecycle.exception.remote_ref_verified:
        return True
    return bool(receipt and receipt.push_range)


def _post_push_green(
    lifecycle: GovernedExceptionLifecycle,
    *,
    receipt: RawGitBypassReceipt | None,
) -> bool:
    if lifecycle.exception and lifecycle.exception.post_push_proof_ref:
        return True
    return bool(receipt and receipt.push_range)


__all__ = [
    "RAW_GIT_COMMIT_ANCHOR_STATUS",
    "close_raw_git_bypass_lifecycle",
    "is_open_raw_git_bypass_lifecycle",
    "raw_git_receipt_id_for_lifecycle",
    "raw_git_receipt_ref",
]
