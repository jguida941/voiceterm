"""Evaluation and expiry reducers for governed bypass lifecycles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .bypass_activation_result import (
    BypassActivated,
    BypassActivationResult,
    BypassDenied,
    bypass_activation_lifecycle,
    bypass_activation_result,
)
from .bypass_lifecycle_models import (
    BYPASS_EXCEPTION_CLASS,
    BYPASS_GUARD_ID,
    BypassAuthorityScope,
    BypassEvaluation,
    BypassEvaluationDecision,
    BypassExpiry,
    BypassExpirySource,
    BypassLifecycle,
    BypassLifecycleState,
    BypassReceipt,
    BypassRequest,
)
from .bypass_lifecycle_registry import DEFAULT_BYPASS_REGISTRY
from .correlation_spine import correlation_context_for_ref
from .governed_exception_receipts import ExceptionReceipt
from .governed_transitions import governed_transition

if TYPE_CHECKING:
    from .governed_exception_lifecycle import (
        GovernedExceptionLifecycle as GovernedExceptionRecord,
    )

_ACTION_KIND_BY_SCOPE = {
    BypassAuthorityScope.AGENT_SPAWN_ONLY: "runtime.spawn",
    BypassAuthorityScope.EDIT_ONLY: "runtime.mutate",
    BypassAuthorityScope.EDIT_AND_COMMIT: "vcs.commit",
    BypassAuthorityScope.EDIT_COMMIT_AND_PUSH: "vcs.push",
}


@dataclass(frozen=True, slots=True)
class BypassEvaluationInput:
    operator_signature: str
    ai_approval_evidence: str
    evaluated_at_utc: str
    evaluator_actor_id: str = "system"
    expires_at_utc: str = ""
    policy_evidence_refs: tuple[str, ...] = ()


@governed_transition(
    transition_id="bypass.grant_lifetime_bypass",
    requires=("BypassReceipt:issued",),
    produces=("GovernedExceptionLifecycle:operator_approved",),
    emits=("ExceptionReceipt", "GovernedExceptionLifecycle"),
    graph_path=("BypassReceipt", "ExceptionReceipt", "GovernedExceptionLifecycle"),
)
def grant_lifetime_bypass(receipt: BypassReceipt) -> "GovernedExceptionRecord":
    """Grant bypass authority through the governed exception lifecycle."""
    from .governed_exception_lifecycle import GovernedExceptionLifecycle

    authority_refs = (
        f"bypass_receipt:{receipt.receipt_id}",
        f"operator:{receipt.granted_by_operator_actor_id}",
        receipt.ai_approval_evidence,
    )
    worktree_refs = (f"requested_authority_scope:{receipt.requested_authority_scope}",)
    exception_receipt_id = f"exception:{receipt.receipt_id}"
    exception_context = correlation_context_for_ref(
        "exception_receipt",
        exception_receipt_id,
        causation_kind="bypass_receipt",
        causation_ref_value=receipt.receipt_id,
        run_kind="validation_plan",
        run_ref_value="MP377-LIFETIME-BYPASS-MODE-S1",
    )
    exception = ExceptionReceipt(
        receipt_id=exception_receipt_id,
        action_kind=_ACTION_KIND_BY_SCOPE[receipt.requested_authority_scope],
        phase="operator_bypass_authorization",
        guard_id=BYPASS_GUARD_ID,
        exception_class=BYPASS_EXCEPTION_CLASS,
        operator_reason=receipt.reason,
        head=f"bypass:{receipt.receipt_id}",
        scope=receipt.requested_authority_scope,
        planned_finding_ingest_ref=f"bypass_receipt:{receipt.receipt_id}",
        authority_evidence_refs=authority_refs,
        worktree_safety_evidence_refs=worktree_refs,
        validation_plan_id="MP377-LIFETIME-BYPASS-MODE-S1",
        execution_status="operator_approved",
        expires_at_utc=receipt.expires_at_utc,
        created_at_utc=receipt.granted_at_utc,
        correlation_id=exception_context.correlation_id,
        causation_id=exception_context.causation_id,
        run_id=exception_context.run_id,
    )
    lifecycle = GovernedExceptionLifecycle(
        lifecycle_id=f"gel:bypass:{receipt.receipt_id}",
        status="operator_approved",
        exception=exception,
        planned_finding_ingest_ref=f"bypass_receipt:{receipt.receipt_id}",
        validation_plan_id="MP377-LIFETIME-BYPASS-MODE-S1",
        authority_evidence_refs=authority_refs,
        worktree_safety_evidence_refs=worktree_refs,
        system_map_contract_ids=("GovernedExceptionLifecycle", "BypassReceipt"),
        developer_loop_refs=(receipt.ai_approval_evidence,),
        created_at_utc=receipt.granted_at_utc,
        updated_at_utc=receipt.granted_at_utc,
    )
    DEFAULT_BYPASS_REGISTRY.register_receipt(receipt)
    return lifecycle


@governed_transition(
    transition_id="bypass.evaluate_request",
    requires=("BypassRequest:bypass_requested",),
    produces=("BypassLifecycle:bypass_active", "BypassLifecycle:bypass_denied"),
    emits=(
        "BypassEvaluation",
        "BypassReceipt",
        "GovernedExceptionLifecycle",
        "BypassLifecycle",
    ),
    graph_path=(
        "BypassRequest",
        "BypassEvaluation",
        "BypassReceipt",
        "GovernedExceptionLifecycle",
        "BypassLifecycle",
    ),
)
def evaluate_bypass_request(
    request: BypassRequest,
    evidence: BypassEvaluationInput,
) -> BypassLifecycle:
    """Evaluate a typed bypass request and issue a governed receipt when approved."""
    authority_evidence_refs = _authority_evidence_refs(request=request, evidence=evidence)
    denial_reason = _bypass_request_denial_reason(request=request, evidence=evidence)
    if denial_reason:
        evaluation = BypassEvaluation(
            evaluation_id=f"bypass-eval:{request.request_id}",
            request_id=request.request_id,
            decision=BypassEvaluationDecision.DENIED,
            evaluated_at_utc=evidence.evaluated_at_utc,
            evaluator_actor_id=evidence.evaluator_actor_id,
            reason=denial_reason,
            authority_evidence_refs=authority_evidence_refs,
            policy_evidence_refs=evidence.policy_evidence_refs,
        )
        return BypassLifecycle(
            lifecycle_id=f"bypass:{request.request_id}",
            state=BypassLifecycleState.DENIED,
            request=request,
            evaluation=evaluation,
        )

    receipt = BypassReceipt(
        receipt_id=f"bypass:{request.request_id}",
        reason=request.reason,
        operator_signature=evidence.operator_signature,
        ai_approval_evidence=evidence.ai_approval_evidence,
        requested_authority_scope=request.scope,
        granted_at_utc=evidence.evaluated_at_utc,
        granted_by_operator_actor_id=request.actor,
        expires_at_utc=evidence.expires_at_utc,
    )
    governed_exception = grant_lifetime_bypass(receipt)
    evaluation = BypassEvaluation(
        evaluation_id=f"bypass-eval:{request.request_id}",
        request_id=request.request_id,
        decision=BypassEvaluationDecision.APPROVED,
        evaluated_at_utc=evidence.evaluated_at_utc,
        evaluator_actor_id=evidence.evaluator_actor_id,
        reason="operator_approved_bypass_request",
        approved_scope=request.scope,
        governed_exception_lifecycle_id=governed_exception.lifecycle_id,
        authority_evidence_refs=authority_evidence_refs,
        policy_evidence_refs=(
            "ProjectGovernance",
            "repo-pack-policy",
            "GovernedExceptionLifecycle",
            *evidence.policy_evidence_refs,
        ),
    )
    lifecycle = BypassLifecycle(
        lifecycle_id=governed_exception.lifecycle_id,
        state=BypassLifecycleState.ACTIVE,
        request=request,
        evaluation=evaluation,
        receipt=receipt,
        governed_exception=governed_exception,
        activation_evidence_refs=(
            f"bypass_request:{request.request_id}",
            f"bypass_receipt:{receipt.receipt_id}",
            governed_exception.lifecycle_id,
        ),
    )
    DEFAULT_BYPASS_REGISTRY.register_lifecycle(lifecycle)
    return lifecycle


def evaluate_bypass_activation(
    request: BypassRequest,
    evidence: BypassEvaluationInput,
) -> BypassActivationResult:
    """Evaluate a bypass request as an explicit activated/denied sum type."""
    return bypass_activation_result(evaluate_bypass_request(request, evidence))


@governed_transition(
    transition_id="bypass.expire_lifecycle",
    requires=("BypassLifecycle:bypass_active",),
    produces=("BypassLifecycle:bypass_expired", "BypassLifecycle:bypass_revoked"),
    emits=("BypassExpiry", "BypassLifecycle"),
    graph_path=("BypassLifecycle", "BypassExpiry", "BypassLifecycle"),
)
def expire_bypass_lifecycle(
    lifecycle: BypassLifecycle,
    *,
    expired_at_utc: str,
    reason: str,
    source: BypassExpirySource,
    evidence_refs: tuple[str, ...] = (),
) -> BypassLifecycle:
    """Return a lifecycle with a typed expiry/revoke event attached."""
    receipt_id = lifecycle.receipt.receipt_id if lifecycle.receipt else ""
    expiry = BypassExpiry(
        expiry_id=f"bypass-expiry:{receipt_id or lifecycle.lifecycle_id}",
        receipt_id=receipt_id,
        expired_at_utc=expired_at_utc,
        source=source,
        reason=reason,
        evidence_refs=evidence_refs,
    )
    state = (
        BypassLifecycleState.REVOKED
        if source is BypassExpirySource.OPERATOR_REVOKE
        else BypassLifecycleState.EXPIRED
    )
    receipt = _revoked_receipt(
        lifecycle.receipt,
        expired_at_utc=expired_at_utc,
        reason=reason,
        source=source,
    )
    updated = BypassLifecycle(
        lifecycle_id=lifecycle.lifecycle_id,
        state=state,
        request=lifecycle.request,
        evaluation=lifecycle.evaluation,
        receipt=receipt,
        governed_exception=lifecycle.governed_exception,
        expiry=expiry,
        activation_evidence_refs=lifecycle.activation_evidence_refs,
    )
    DEFAULT_BYPASS_REGISTRY.register_lifecycle(updated)
    return updated


def _revoked_receipt(
    receipt: BypassReceipt | None,
    *,
    expired_at_utc: str,
    reason: str,
    source: BypassExpirySource,
) -> BypassReceipt | None:
    if receipt is None or source is not BypassExpirySource.OPERATOR_REVOKE:
        return receipt
    revoked = BypassReceipt(
        receipt_id=receipt.receipt_id,
        reason=receipt.reason,
        operator_signature=receipt.operator_signature,
        ai_approval_evidence=receipt.ai_approval_evidence,
        requested_authority_scope=receipt.requested_authority_scope,
        granted_at_utc=receipt.granted_at_utc,
        granted_by_operator_actor_id=receipt.granted_by_operator_actor_id,
        expires_at_utc=receipt.expires_at_utc,
        revoked_at_utc=expired_at_utc,
        revoked_reason=reason,
    )
    DEFAULT_BYPASS_REGISTRY.register_receipt(revoked)
    return revoked


def _authority_evidence_refs(
    *,
    request: BypassRequest,
    evidence: BypassEvaluationInput,
) -> tuple[str, ...]:
    refs = [
        f"bypass_request:{request.request_id}",
        f"operator:{evidence.operator_signature}",
        evidence.ai_approval_evidence,
        *request.evidence_refs,
    ]
    return tuple(ref for ref in refs if ref)


def _bypass_request_denial_reason(
    *,
    request: BypassRequest,
    evidence: BypassEvaluationInput,
) -> str:
    if not request.request_id:
        return "request_id_required"
    if not request.reason:
        return "reason_required"
    if not request.actor:
        return "actor_required"
    if not evidence.operator_signature:
        return "operator_signature_required"
    if not evidence.ai_approval_evidence:
        return "ai_approval_evidence_required"
    return ""


__all__ = [
    "BypassActivated",
    "BypassActivationResult",
    "BypassDenied",
    "BypassEvaluationInput",
    "bypass_activation_lifecycle",
    "bypass_activation_result",
    "evaluate_bypass_request",
    "evaluate_bypass_activation",
    "expire_bypass_lifecycle",
    "grant_lifetime_bypass",
]
