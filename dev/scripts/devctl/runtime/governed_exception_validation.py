"""Fail-closed validators for governed-exception contracts."""

from __future__ import annotations

from .governed_exception_lifecycle import GovernedExceptionLifecycle
from .governed_exception_policy import ExceptionPolicy
from .governed_exception_receipts import ExceptionReceipt

MUTATION_ACTION_KINDS = frozenset(
    {
        "vcs.stage",
        "vcs.commit",
        "vcs.push",
        "vcs.recover",
        "runtime.mutate",
    }
)

GENERIC_REASON_TEXT = frozenset(
    {
        "bypass",
        "needed",
        "temporary",
        "temp",
        "fix later",
        "later",
        "test",
        "testing",
        "n/a",
        "na",
        "none",
        "unknown",
    }
)

OPEN_LIFECYCLE_STATUSES = frozenset(
    {
        "blocked",
        "classified",
        "bounded_auto_repair_attempted",
        "exception_requested",
        "exception_policy_checked",
        "operator_approved",
        "receipt_written_pending",
        "exception_executed",
        "result_verified",
        "finding_opened_or_refreshed",
        "remediation_packet_created",
        "startup_context_projected",
        "assigned_to_agent_or_slice",
        "fix_attempted",
        "validation_plan_rerun",
        "resolution_receipt_written",
        "closure_proof_verified",
        "guard_promotion_or_waiver_recorded",
        "open",
        "reopened",
        "escalated",
    }
)

CLOSED_LIFECYCLE_STATUSES = frozenset(
    {"closed", "closed_via_commit_anchor", "closed_via_bypass_expiry", "resolved"}
)


def validate_exception_receipt(
    receipt: ExceptionReceipt,
    *,
    current_head: str = "",
    policy: ExceptionPolicy | None = None,
) -> tuple[str, ...]:
    """Return fail-closed validation errors for one exception receipt."""
    effective_policy = policy or ExceptionPolicy()
    errors: list[str] = []
    if not receipt.receipt_id:
        errors.append("missing_receipt_id")
    if not receipt.action_kind:
        errors.append("missing_action_kind")
    if not receipt.phase:
        errors.append("missing_phase")
    if not receipt.guard_id:
        errors.append("missing_guard_id")
    if not _specific_reason(receipt.operator_reason):
        errors.append("missing_or_generic_reason")
    if not receipt.head:
        errors.append("missing_head")
    if current_head and receipt.head and receipt.head != current_head:
        errors.append("stale_head")
    allowed = set(effective_policy.allowed_exception_classes)
    forbidden = set(effective_policy.forbidden_exception_classes)
    if not receipt.exception_class:
        errors.append("missing_exception_class")
    elif receipt.exception_class in forbidden:
        errors.append("forbidden_exception_class")
    elif receipt.exception_class not in allowed:
        errors.append("unknown_exception_class")
    if not (receipt.finding_id or receipt.planned_finding_ingest_ref):
        errors.append("missing_finding_or_planned_finding_ingest")
    if _is_mutation_action(receipt.action_kind):
        if not receipt.authority_evidence_refs:
            errors.append("missing_authority_evidence")
        if not receipt.worktree_safety_evidence_refs:
            errors.append("missing_worktree_or_orphan_evidence")
    if _is_successful_push_without_remote_proof(receipt):
        errors.append("push_success_without_remote_ref_or_post_push_proof")
    return tuple(errors)


def validate_governed_exception_lifecycle(
    lifecycle: GovernedExceptionLifecycle,
    *,
    current_head: str = "",
    policy: ExceptionPolicy | None = None,
) -> tuple[str, ...]:
    """Return validation errors for one governed exception lifecycle."""
    errors: list[str] = []
    if not lifecycle.lifecycle_id:
        errors.append("missing_lifecycle_id")
    status = lifecycle.status or "open"
    if status not in OPEN_LIFECYCLE_STATUSES | CLOSED_LIFECYCLE_STATUSES:
        errors.append("unknown_lifecycle_status")
    if lifecycle.exception is None:
        errors.append("missing_exception_receipt")
    else:
        errors.extend(
            f"exception.{error}"
            for error in validate_exception_receipt(
                lifecycle.exception,
                current_head=current_head,
                policy=policy,
            )
        )
    if status in CLOSED_LIFECYCLE_STATUSES:
        if lifecycle.resolution is None:
            errors.append("closed_lifecycle_without_resolution")
        if lifecycle.closure_proof is None:
            errors.append("closed_lifecycle_without_closure_proof")
    return tuple(errors)


def pending_lifecycle_status(status: str) -> bool:
    """Return whether a lifecycle should appear in read-only pending views."""
    normalized = (status or "open").strip()
    return normalized not in CLOSED_LIFECYCLE_STATUSES


def _specific_reason(reason: str) -> bool:
    normalized = " ".join(reason.strip().lower().split())
    if not normalized or normalized in GENERIC_REASON_TEXT:
        return False
    if len(normalized) < 20:
        return False
    return any(char.isalpha() for char in normalized)


def _is_mutation_action(action_kind: str) -> bool:
    normalized = action_kind.strip()
    return normalized in MUTATION_ACTION_KINDS or normalized.startswith("vcs.")


def _is_successful_push_without_remote_proof(receipt: ExceptionReceipt) -> bool:
    if receipt.action_kind != "vcs.push":
        return False
    if receipt.execution_status not in {"success", "succeeded", "ok"}:
        return False
    return not (receipt.remote_ref_verified and receipt.post_push_proof_ref)


__all__ = [
    "CLOSED_LIFECYCLE_STATUSES",
    "GENERIC_REASON_TEXT",
    "MUTATION_ACTION_KINDS",
    "OPEN_LIFECYCLE_STATUSES",
    "pending_lifecycle_status",
    "validate_exception_receipt",
    "validate_governed_exception_lifecycle",
]
