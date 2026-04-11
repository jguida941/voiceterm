"""Validation-plan helpers for the governed VCS executor."""

from __future__ import annotations

import secrets
from collections.abc import Sequence

from ...runtime import ActionResult, TypedAction
from ...runtime.action_contracts import ActionOutcome
from ...runtime.remote_commit_pipeline_models import RemoteCommitPipelineContract
from ...runtime.validation_contracts import ValidationPlan, ValidationReceipt
from ...time_utils import utc_timestamp
from .governed_executor_field_access import string_value


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
        risk_addons=tuple(
            str(item).strip()
            for item in action.parameters.get("risk_addons", ()) or ()
            if str(item).strip()
        ),
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
    return ValidationReceipt(
        receipt_id=f"validation-receipt-{secrets.token_hex(6)}",
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
        emitted_at_utc=utc_timestamp(),
    )
