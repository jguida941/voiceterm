"""Validation-plan helpers for the governed VCS executor."""

from __future__ import annotations

import secrets
from collections.abc import Sequence
from typing import cast

from ...runtime import ActionResult, TypedAction
from ...runtime.action_contracts import ActionOutcome
from ...runtime.correlation_spine import correlation_context_for_ref
from ...runtime.remote_commit_pipeline_models import RemoteCommitPipelineContract
from ...runtime.receipt_state_gate import require_receipt_state
from ...runtime.validation_contracts import ValidationPlan, ValidationReceipt
from ...time_utils import utc_timestamp
from .governed_executor_field_access import string_value

VALIDATION_PRE_STATE = "validation_pending"
VALIDATION_PASSED_STATE = "validation_passed"
VALIDATION_FAILED_STATE = "validation_failed"


class ValidationReceiptStateRequired(ValueError):
    """Raised when a validation receipt does not reach its expected state."""


def build_validation_plan(
    *,
    action: TypedAction,
    staged: Sequence[str],
    tree_hash: str,
) -> ValidationPlan:
    """Bind the selected validation policy to one staged tree."""
    push_requested = bool(action.parameters.get("push_requested"))
    guard_profile = string_value(action.parameters.get("guard_profile"))
    return ValidationPlan(
        plan_id=f"validation-plan-{secrets.token_hex(6)}",
        bundle_id=guard_profile,
        staged_tree_hash=tree_hash,
        selected_paths=tuple(staged),
        risk_addons=_risk_addons(action.parameters.get("risk_addons")),
        proof_level=string_value(action.parameters.get("proof_level"))
        or ("publish_ready" if push_requested else "checkpoint_ready"),
        checkpoint_required=True,
        push_requested=push_requested,
        work_intake_ref=string_value(action.parameters.get("work_intake_ref")),
    )


def build_validation_receipt(
    *,
    pipeline: RemoteCommitPipelineContract,
    guard_result: ActionResult,
    guard_action_id: str,
) -> ValidationReceipt:
    """Project one guard result into the typed validation receipt contract."""
    validation_plan = pipeline.intent.validation_plan
    bundle_id = (
        validation_plan.bundle_id
        if validation_plan is not None
        else pipeline.intent.guard_profile
    )
    plan_id = validation_plan.plan_id if validation_plan is not None else ""
    staged_tree_hash = (
        validation_plan.staged_tree_hash
        if validation_plan is not None
        else pipeline.intent.staged_tree_hash
    )
    passed = guard_result.ok and guard_result.status == ActionOutcome.PASS
    post_state = VALIDATION_PASSED_STATE if passed else VALIDATION_FAILED_STATE
    receipt_id = f"validation-receipt-{secrets.token_hex(6)}"
    context = correlation_context_for_ref(
        "validation_receipt",
        receipt_id,
        causation_kind="typed_action",
        causation_ref_value=guard_action_id,
        run_kind="validation_plan",
        run_ref_value=plan_id or staged_tree_hash,
    )
    receipt = ValidationReceipt(
        receipt_id=receipt_id,
        plan_id=plan_id,
        bundle_id=bundle_id,
        staged_tree_hash=staged_tree_hash,
        action_id=guard_action_id,
        status=guard_result.status,
        reason=guard_result.reason,
        findings_count=guard_result.findings_count,
        warnings=tuple(guard_result.warnings),
        checkpoint_sufficient=passed,
        push_sufficient=passed and pipeline.intent.push_requested,
        pre_state=VALIDATION_PRE_STATE,
        post_state=post_state,
        pre_state_snapshot=f"staged_tree:{staged_tree_hash}",
        post_state_snapshot=(
            f"guard_action:{guard_action_id}:"
            f"{guard_result.status}:{guard_result.findings_count}"
        ),
        emitted_at_utc=utc_timestamp(),
        correlation_id=context.correlation_id,
        causation_id=context.causation_id,
        run_id=context.run_id,
    )
    validated: ValidationReceipt = require_receipt_state(
        receipt,
        state_getter=lambda item: item.post_state,
        required_state=post_state,
        error_factory=lambda: ValidationReceiptStateRequired(
            "validation receipt did not reach the expected post_state"
        ),
    )
    return validated


def _risk_addons(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    items = cast(list[object] | tuple[object, ...], value)
    return tuple(text for item in items if (text := str(item).strip()))
