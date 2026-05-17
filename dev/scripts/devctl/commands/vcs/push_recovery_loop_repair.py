"""Bounded review-loop recovery phase for governed push pre-validation."""

from __future__ import annotations

import time
from pathlib import Path

from ...common import run_cmd
from ...config import REPO_ROOT
from .governed_executor_recovery_actions import (
    RECOVERY_LOOP_REPAIR_ACTION_ID,
)
from .push_recovery_loop_handoff import completed_handoff_outcome_for_startup_payload
from .push_recovery_loop_commands import (
    bounded_recovery_command,
    is_push_execute_command,
    run_bounded_command,
    run_startup_context_summary,
)
from .push_recovery_loop_payload import (
    field_value,
    payload_allows_bounded_recovery,
    returncode,
    startup_context_payload_from_step,
    startup_context_step_needs_recovery,
    step_record,
    startup_next_command,
)
from .push_recovery_loop_result import (
    PRE_VALIDATION_RECOVERY_LOOP_REPAIR,
    block_recovery_result,
    complete_recovery_result,
    record_recovery_result,
)
from .push_recovery_loop_state import (
    mark_recovery_required_from_startup_context_step,
    recovery_required,
    startup_payload_from_state,
)
from .push_recovery_loop_types import (
    RecoveryContext,
    RecoveryProgress,
    RecoveryResultStatus,
)

MAX_RECOVERY_STEPS = 5
TIME_BUDGET_SECONDS = 180

_BLOCKED_IMPLEMENTATION_PERMISSIONS = frozenset({"blocked", "suspended"})


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

    context = RecoveryContext(
        state=state,
        policy=policy,
        repo_root=repo_root,
        runner=runner,
        max_steps=max(1, int(max_steps)),
        time_budget_seconds=max(1, int(time_budget_seconds)),
        deadline=time.monotonic() + max(1, int(time_budget_seconds)),
    )

    if getattr(state, "errors", ()):
        return record_recovery_result(
            context,
            RecoveryResultStatus(
                status="forbidden",
                ok=False,
                reason="previous_phase_failed",
                retryable=False,
            ),
        )

    if not recovery_required(state):
        return record_recovery_result(
            context,
            RecoveryResultStatus(
                status="not_needed",
                ok=True,
                reason="no_recoverable_startup_context_failure",
                retryable=False,
            ),
        )

    startup_payload = startup_payload_from_state(state)
    handoff_outcome = completed_handoff_outcome_for_startup_payload(
        repo_root=context.repo_root,
        payload=startup_payload,
    )
    if handoff_outcome is not None:
        progress = RecoveryProgress(latest_payload=startup_payload)
        return record_recovery_result(
            context,
            RecoveryResultStatus(
                status="completed",
                ok=True,
                reason="agent_session_completed_handoff",
                retryable=False,
            ),
            progress=progress,
            agent_session_outcome=handoff_outcome,
        )

    return _run_recovery_loop(context)


def _run_recovery_loop(context: RecoveryContext) -> dict[str, object]:
    progress = RecoveryProgress()
    for attempt in range(context.max_steps + 1):
        if time.monotonic() >= context.deadline:
            return block_recovery_result(
                context,
                progress,
                "time_budget_exceeded",
                retryable=True,
            )

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
        handoff_outcome = completed_handoff_outcome_for_startup_payload(
            repo_root=context.repo_root,
            payload=payload,
        )
        if handoff_outcome is not None:
            return record_recovery_result(
                context,
                RecoveryResultStatus(
                    status="completed",
                    ok=True,
                    reason="agent_session_completed_handoff",
                    retryable=False,
                ),
                progress=progress,
                agent_session_outcome=handoff_outcome,
            )
        if _startup_context_ready(startup_step, payload):
            return complete_recovery_result(context, progress, "startup_context_ready")
        if is_push_execute_command(next_command):
            return complete_recovery_result(context, progress, "push_ready")
        if attempt >= context.max_steps:
            return block_recovery_result(
                context,
                progress,
                "max_steps_exceeded",
                retryable=True,
            )

        bounded_command, block_reason = bounded_recovery_command(next_command)
        if not bounded_command:
            return block_recovery_result(
                context,
                progress,
                block_reason or "operator_scope_required",
                retryable=False,
            )
        if not payload_allows_bounded_recovery(payload):
            return block_recovery_result(
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
            return block_recovery_result(
                context,
                progress,
                "bounded_recovery_command_failed",
                retryable=True,
            )

    return block_recovery_result(
        context,
        progress,
        "max_steps_exceeded",
        retryable=True,
    )


def _startup_context_ready(
    step: dict[str, object],
    payload: dict[str, object],
) -> bool:
    if returncode(step) == 0:
        return True
    permission = field_value(payload, "implementation_permission")
    return bool(permission and permission not in _BLOCKED_IMPLEMENTATION_PERMISSIONS)


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
