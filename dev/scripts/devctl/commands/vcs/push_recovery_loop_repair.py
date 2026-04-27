"""Bounded review-loop recovery phase for governed push pre-validation."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from ...common import run_cmd
from ...config import REPO_ROOT
from ...runtime import ActionResult
from ...runtime.action_contracts import (
    ACTION_RESULT_CONTRACT_ID,
    ACTION_RESULT_SCHEMA_VERSION,
    ActionOutcome,
)
from .governed_executor_recovery_actions import (
    RECOVERY_LOOP_REPAIR_ACTION_ID,
    build_recovery_loop_repair_action,
)
from .push_recovery_loop_commands import (
    bounded_recovery_command,
    is_push_execute_command,
    run_bounded_command,
    run_startup_context_summary,
)
from .push_recovery_loop_payload import (
    compact_startup_payload,
    compact_step,
    field_value,
    payload_allows_bounded_recovery,
    returncode,
    startup_context_payload_from_step,
    startup_context_step_needs_recovery,
    step_record,
    startup_next_command,
)

PRE_VALIDATION_RECOVERY_LOOP_REPAIR = "pre_validation_recovery_loop_repair"
MAX_RECOVERY_STEPS = 5
TIME_BUDGET_SECONDS = 30

_BLOCKED_IMPLEMENTATION_PERMISSIONS = frozenset({"blocked", "suspended"})


@dataclass(slots=True)
class _RecoveryContext:
    state: object
    policy: object
    repo_root: Path
    runner: object
    max_steps: int
    time_budget_seconds: int
    deadline: float


@dataclass(slots=True)
class _RecoveryProgress:
    steps: list[dict[str, object]] = field(default_factory=list)
    latest_payload: dict[str, object] = field(default_factory=dict)


def run_pre_validation_recovery_loop_repair_phase(
    state,
    policy,
    *,
    repo_root: Path = REPO_ROOT,
    command_runner=None,
    max_steps: int = MAX_RECOVERY_STEPS,
    time_budget_seconds: int = TIME_BUDGET_SECONDS,
) -> dict[str, object]:
    """Run bounded startup-context ``next=`` repair before push validation."""
    runner = run_cmd if command_runner is None else command_runner
    context = _RecoveryContext(
        state=state,
        policy=policy,
        repo_root=repo_root,
        runner=runner,
        max_steps=max(1, int(max_steps)),
        time_budget_seconds=max(1, int(time_budget_seconds)),
        deadline=time.monotonic() + max(1, int(time_budget_seconds)),
    )
    if getattr(state, "errors", ()):
        return _record_result(
            context,
            status="forbidden",
            ok=False,
            reason="previous_phase_failed",
            retryable=False,
        )
    if not _recovery_required(state):
        return _record_result(
            context,
            status="not_needed",
            ok=True,
            reason="no_recoverable_startup_context_failure",
            retryable=False,
        )
    return _run_recovery_loop(context)


def mark_recovery_required_from_startup_context_step(state, step) -> dict[str, object]:
    """Record that managed projection sync found a bounded startup recovery."""
    payload = startup_context_payload_from_step(step)
    required = payload_allows_bounded_recovery(payload)
    record: dict[str, object] = {}
    record["required"] = required
    record["reason"] = (
        "bounded_startup_context_recovery"
        if required
        else "startup_context_failure_not_bounded"
    )
    record["attention_status"] = field_value(payload, "attention_status")
    record["recovery_action"] = field_value(payload, "recovery_action")
    record["next_command"] = startup_next_command(payload)
    record["startup_context_step"] = compact_step(step)
    _set_state_attr(state, "pre_validation_recovery_loop_repair_required", required)
    _set_state_attr(state, "pre_validation_recovery_loop_repair_startup", record)
    return record


def _run_recovery_loop(context: _RecoveryContext) -> dict[str, object]:
    progress = _RecoveryProgress()
    for attempt in range(context.max_steps + 1):
        if time.monotonic() >= context.deadline:
            return _block(context, progress, "time_budget_exceeded", retryable=True)

        startup_step = run_startup_context_summary(
            context.runner,
            repo_root=context.repo_root,
            deadline=context.deadline,
            attempt=attempt,
        )
        payload = startup_context_payload_from_step(startup_step)
        progress.latest_payload = payload
        progress.steps.append(step_record(startup_step, payload=payload))

        next_command = startup_next_command(payload)
        if _startup_context_ready(startup_step, payload):
            return _complete(context, progress, "startup_context_ready")
        if is_push_execute_command(next_command):
            return _complete(context, progress, "push_ready")
        if attempt >= context.max_steps:
            return _block(context, progress, "max_steps_exceeded", retryable=True)

        bounded_command, block_reason = bounded_recovery_command(next_command)
        if not bounded_command:
            return _block(
                context,
                progress,
                block_reason or "operator_scope_required",
                retryable=False,
            )
        if not payload_allows_bounded_recovery(payload):
            return _block(
                context,
                progress,
                "startup_context_recovery_not_bounded",
                retryable=False,
            )

        repair_step = run_bounded_command(
            context.runner,
            bounded_command,
            repo_root=context.repo_root,
            deadline=context.deadline,
            attempt=attempt,
        )
        progress.steps.append(step_record(repair_step, payload={}))
        if returncode(repair_step) != 0:
            return _block(
                context,
                progress,
                "bounded_recovery_command_failed",
                retryable=True,
            )

    return _block(context, progress, "max_steps_exceeded", retryable=True)


def _recovery_required(state) -> bool:
    if bool(getattr(state, "pre_validation_recovery_loop_repair_required", False)):
        return True
    sync = getattr(state, "pre_validation_managed_projection_sync", {})
    return isinstance(sync, dict) and bool(sync.get("startup_context_recovery_required"))


def _startup_context_ready(
    step: dict[str, object],
    payload: dict[str, object],
) -> bool:
    if returncode(step) == 0:
        return True
    permission = field_value(payload, "implementation_permission")
    return bool(permission and permission not in _BLOCKED_IMPLEMENTATION_PERMISSIONS)


def _complete(
    context: _RecoveryContext,
    progress: _RecoveryProgress,
    reason: str,
) -> dict[str, object]:
    return _record_result(
        context,
        status="completed",
        ok=True,
        reason=reason,
        retryable=False,
        progress=progress,
    )


def _block(
    context: _RecoveryContext,
    progress: _RecoveryProgress,
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
    return _record_result(
        context,
        status="blocked",
        ok=False,
        reason=reason,
        retryable=retryable,
        progress=progress,
    )


def _record_result(
    context: _RecoveryContext,
    *,
    status: str,
    ok: bool,
    reason: str,
    retryable: bool,
    progress: _RecoveryProgress | None = None,
) -> dict[str, object]:
    result = _phase_result(
        context,
        status=status,
        ok=ok,
        reason=reason,
        retryable=retryable,
        progress=progress,
    )
    _set_state_attr(context.state, "pre_validation_recovery_loop_repair", result)
    return result


def _phase_result(
    context: _RecoveryContext,
    *,
    status: str,
    ok: bool,
    reason: str,
    retryable: bool,
    progress: _RecoveryProgress | None,
) -> dict[str, object]:
    typed_action = build_recovery_loop_repair_action(
        repo_pack_id=context.policy.repo_pack_id,
        branch=getattr(context.state, "branch", ""),
        remote=getattr(context.state, "remote", ""),
        max_steps=context.max_steps,
        time_budget_seconds=context.time_budget_seconds,
    )
    latest_payload = progress.latest_payload if progress else {}
    artifact_paths = _artifact_paths(latest_payload)
    action_result = _action_result(ok, reason, retryable, artifact_paths)

    result: dict[str, object] = {}
    result["phase"] = PRE_VALIDATION_RECOVERY_LOOP_REPAIR
    result["allowed"] = True
    result["status"] = status
    result["ok"] = ok
    result["reason"] = reason
    result["retryable"] = retryable
    result["max_steps"] = context.max_steps
    result["time_budget_seconds"] = context.time_budget_seconds
    result["typed_action"] = asdict(typed_action)
    result["action_result"] = action_result.to_dict()
    if progress and progress.steps:
        result["steps"] = progress.steps
        result["step_count"] = len(progress.steps)
    if latest_payload:
        result["latest_startup_context"] = compact_startup_payload(latest_payload)
    if artifact_paths:
        result["artifact_paths"] = artifact_paths
    return result


def _action_result(
    ok: bool,
    reason: str,
    retryable: bool,
    artifact_paths: tuple[str, ...],
) -> ActionResult:
    return ActionResult(
        schema_version=ACTION_RESULT_SCHEMA_VERSION,
        contract_id=ACTION_RESULT_CONTRACT_ID,
        action_id=RECOVERY_LOOP_REPAIR_ACTION_ID,
        ok=ok,
        status=ActionOutcome.PASS if ok else ActionOutcome.FAIL,
        reason=reason,
        retryable=retryable,
        operator_guidance=(
            "Startup recovery completed; governed push may continue."
            if ok
            else "Review the bounded recovery phase and rerun governed push after the typed blocker clears."
        ),
        artifact_paths=artifact_paths,
    )


def _artifact_paths(payload: dict[str, object]) -> tuple[str, ...]:
    startup_receipt = payload.get("startup_receipt")
    if isinstance(startup_receipt, dict):
        path = field_value(startup_receipt, "path")
        return (path,) if path else ()
    receipt_path = field_value(payload, "startup_receipt_path")
    return (receipt_path,) if receipt_path else ()


def _set_state_attr(state, name: str, value: object) -> None:
    try:
        setattr(state, name, value)
    except (AttributeError, TypeError):
        pass


__all__ = [
    "MAX_RECOVERY_STEPS",
    "PRE_VALIDATION_RECOVERY_LOOP_REPAIR",
    "RECOVERY_LOOP_REPAIR_ACTION_ID",
    "TIME_BUDGET_SECONDS",
    "bounded_recovery_command",
    "mark_recovery_required_from_startup_context_step",
    "run_pre_validation_recovery_loop_repair_phase",
    "startup_context_payload_from_step",
    "startup_context_step_needs_recovery",
]
