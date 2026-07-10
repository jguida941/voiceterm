"""Result construction for governed push recovery-loop repair."""

from __future__ import annotations

from dataclasses import asdict

from ...runtime import ActionResult
from ...runtime.agent_session_outcome import AgentSessionOutcomeState
from ...runtime.action_contracts import (
    ACTION_RESULT_CONTRACT_ID,
    ACTION_RESULT_SCHEMA_VERSION,
    ActionOutcome,
)
from .governed_executor_recovery_actions import (
    RECOVERY_LOOP_REPAIR_ACTION_ID,
    build_recovery_loop_repair_action,
)
from .push_recovery_loop_payload import compact_startup_payload, field_value
from .push_recovery_loop_state import set_state_attr
from .push_recovery_loop_types import (
    RecoveryContext,
    RecoveryProgress,
    RecoveryResultStatus,
)

PRE_VALIDATION_RECOVERY_LOOP_REPAIR = "pre_validation_recovery_loop_repair"


def complete_recovery_result(
    context: RecoveryContext,
    progress: RecoveryProgress,
    reason: str,
) -> dict[str, object]:
    return record_recovery_result(
        context,
        RecoveryResultStatus(
            status="completed",
            ok=True,
            reason=reason,
            retryable=False,
        ),
        progress=progress,
    )


def block_recovery_result(
    context: RecoveryContext,
    progress: RecoveryProgress,
    reason: str,
    *,
    retryable: bool,
) -> dict[str, object]:
    message = (
        "Pre-validation recovery loop repair could not clear startup-context "
        f"blockers: {reason}."
    )
    errors = getattr(context.state, "errors", [])
    if message not in errors:
        errors.append(message)

    return record_recovery_result(
        context,
        RecoveryResultStatus(
            status="blocked",
            ok=False,
            reason=reason,
            retryable=retryable,
        ),
        progress=progress,
    )


def record_recovery_result(
    context: RecoveryContext,
    outcome: RecoveryResultStatus,
    *,
    progress: RecoveryProgress | None = None,
    agent_session_outcome: AgentSessionOutcomeState | None = None,
) -> dict[str, object]:
    result = phase_result(
        context,
        outcome,
        progress=progress,
        agent_session_outcome=agent_session_outcome,
    )
    set_state_attr(context.state, "pre_validation_recovery_loop_repair", result)
    return result


def phase_result(
    context: RecoveryContext,
    outcome: RecoveryResultStatus,
    *,
    progress: RecoveryProgress | None,
    agent_session_outcome: AgentSessionOutcomeState | None = None,
) -> dict[str, object]:
    typed_action = build_recovery_loop_repair_action(
        repo_pack_id=context.policy.repo_pack_id,
        branch=getattr(context.state, "branch", ""),
        remote=getattr(context.state, "remote", ""),
        max_steps=context.max_steps,
        time_budget_seconds=context.time_budget_seconds,
    )
    latest_payload = progress.latest_payload if progress else {}
    artifact_paths = artifact_paths_from_payload(latest_payload)
    action_result = action_result_for_outcome(
        outcome,
        artifact_paths=artifact_paths,
    )
    result: dict[str, object] = {}
    result["phase"] = PRE_VALIDATION_RECOVERY_LOOP_REPAIR
    result["allowed"] = True
    result["status"] = outcome.status
    result["ok"] = outcome.ok
    result["reason"] = outcome.reason
    result["retryable"] = outcome.retryable
    result["max_steps"] = context.max_steps
    result["time_budget_seconds"] = context.time_budget_seconds
    result["typed_action"] = asdict(typed_action)
    result["action_result"] = action_result.to_dict()

    if progress and progress.steps:
        result["steps"] = progress.steps
        result["step_count"] = len(progress.steps)

    if latest_payload:
        result["latest_startup_context"] = compact_startup_payload(latest_payload)

    if agent_session_outcome is not None:
        result["agent_session_outcome"] = asdict(agent_session_outcome)

    if artifact_paths:
        result["artifact_paths"] = artifact_paths

    return result


def action_result_for_outcome(
    outcome: RecoveryResultStatus,
    *,
    artifact_paths: tuple[str, ...],
) -> ActionResult:
    return ActionResult(
        schema_version=ACTION_RESULT_SCHEMA_VERSION,
        contract_id=ACTION_RESULT_CONTRACT_ID,
        action_id=RECOVERY_LOOP_REPAIR_ACTION_ID,
        ok=outcome.ok,
        status=ActionOutcome.PASS if outcome.ok else ActionOutcome.FAIL,
        reason=outcome.reason,
        retryable=outcome.retryable,
        operator_guidance=(
            "Startup recovery completed; governed push may continue."
            if outcome.ok
            else "Review the bounded recovery phase and rerun governed push after the typed blocker clears."
        ),
        artifact_paths=artifact_paths,
    )


def artifact_paths_from_payload(payload: dict[str, object]) -> tuple[str, ...]:
    startup_receipt = payload.get("startup_receipt")
    if isinstance(startup_receipt, dict):
        path = field_value(startup_receipt, "path")
        return (path,) if path else ()

    receipt_path = field_value(payload, "startup_receipt_path")
    return (receipt_path,) if receipt_path else ()


__all__ = [
    "PRE_VALIDATION_RECOVERY_LOOP_REPAIR",
    "block_recovery_result",
    "complete_recovery_result",
    "record_recovery_result",
]
