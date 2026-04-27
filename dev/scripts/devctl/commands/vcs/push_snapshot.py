"""Push-report payload helpers for guarded push recovery."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...runtime import ActionResult
from .push_artifact import persist_latest_push_report
from .push_findings import append_finding
from .push_flow import PushFlowOutcome
from .push_report import PushReportInputs, PushStageTruth, build_push_report

SILENT_PUSH_FAILURE = "SilentPushFailure"


@dataclass(frozen=True, slots=True)
class PushReportContext:
    """Inputs reused across final and intermediate push reports."""

    repo_root: Path
    policy: object
    state: object
    args: object
    head_commit: str
    typed_action: dict[str, Any]
    artifact_path: str
    current_worktree_identity: str = ""
    approved_target_identity: str = ""
    approved_worktree_identity: str = ""
    push_authorization_id: str = ""
    push_authorization_mode: str = ""


def build_push_report_payload(
    context: PushReportContext,
    *,
    outcome: PushFlowOutcome,
) -> dict[str, Any]:
    """Build the canonical push report payload for the current execution state."""
    state = context.state
    outcome = _enforce_execution_truth(context, outcome)
    action_result = ActionResult(
        schema_version=1,
        contract_id="ActionResult",
        action_id="vcs.push",
        ok=outcome.ok,
        status=outcome.status,
        reason=outcome.reason,
        retryable=not outcome.ok,
        partial_progress=outcome.partial_progress,
        operator_guidance=outcome.operator_guidance,
        warnings=tuple(state.warnings),
        findings_count=len(getattr(state, "findings", []) or []),
        artifact_paths=(context.artifact_path,),
    ).to_dict()
    return build_push_report(
        PushReportInputs(
            policy=context.policy,
            branch=state.branch,
            remote=state.remote,
            head_commit=context.head_commit,
            execute=bool(context.args.execute),
            skip_preflight=bool(context.args.skip_preflight),
            skip_post_push=bool(context.args.skip_post_push),
            dirty_paths=state.dirty_paths,
            fetch_step=state.fetch_step,
            preflight_step=state.preflight_step,
            push_step=state.push_step,
            post_push_steps=state.post_push_steps,
            push_stages=outcome.stages,
            typed_action=context.typed_action,
            action_result=action_result,
            warnings=state.warnings,
            errors=state.errors,
            findings=list(getattr(state, "findings", []) or []),
            artifact_path=context.artifact_path,
            current_worktree_identity=context.current_worktree_identity,
            approved_target_identity=context.approved_target_identity,
            approved_worktree_identity=context.approved_worktree_identity,
            push_authorization_id=context.push_authorization_id,
            push_authorization_mode=context.push_authorization_mode,
            pre_validation_managed_projection_sync=getattr(
                state,
                "pre_validation_managed_projection_sync",
                {},
            ),
            pre_validation_recovery_loop_repair=getattr(
                state,
                "pre_validation_recovery_loop_repair",
                {},
            ),
            post_validation_auto_commit_repair=getattr(
                state,
                "post_validation_auto_commit_repair",
                {},
            ),
        )
    )


def _enforce_execution_truth(
    context: PushReportContext,
    outcome: PushFlowOutcome,
) -> PushFlowOutcome:
    """Fail closed when a report claims publication without subprocess proof."""
    if not bool(context.args.execute) or not outcome.stages.published_remote:
        return outcome
    state = context.state
    missing: list[str] = []
    for field_name in ("fetch_step", "preflight_step", "push_step"):
        if getattr(state, field_name, None) is None:
            missing.append(field_name)
    if not list(getattr(state, "post_push_steps", []) or []):
        missing.append("post_push_steps")
    push_step = getattr(state, "push_step", None)
    if isinstance(push_step, dict) and _returncode(push_step.get("returncode")) != 0:
        missing.append("push_step.returncode")
    remote_head_after = str(getattr(state, "remote_head_after", "") or "").strip()
    if remote_head_after and remote_head_after != context.head_commit:
        missing.append("remote_head_after")
    if not missing:
        return outcome
    append_finding(
        state,
        SILENT_PUSH_FAILURE,
        (
            "Push report attempted to claim remote publication without complete "
            "execution evidence."
        ),
        evidence={
            "missing_or_invalid_fields": tuple(sorted(set(missing))),
            "head_commit": context.head_commit,
            "remote_head_after": remote_head_after,
        },
    )
    return PushFlowOutcome(
        ok=False,
        reason="silent_push_failure",
        operator_guidance=(
            "The governed push report could not prove subprocess execution and "
            "remote-ref publication. Inspect the typed finding and rerun through "
            "`devctl push --execute` after repairing the push path."
        ),
        stages=PushStageTruth(),
        partial_progress=False,
    )

def _returncode(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 1


def persist_published_remote_snapshot(
    context: PushReportContext,
    *,
    reason: str,
    operator_guidance: str,
    partial_progress: bool,
) -> str:
    """Persist a recovery snapshot once remote publication is known to be real."""
    return _persist_snapshot(
        context,
        reason=reason,
        operator_guidance=operator_guidance,
        partial_progress=partial_progress,
        stages=PushStageTruth(
            validation_ready=True,
            published_remote=True,
        ),
    )


def persist_push_progress_snapshot(
    context: PushReportContext,
    *,
    reason: str,
    operator_guidance: str,
    stages: PushStageTruth,
    partial_progress: bool = True,
) -> str:
    """Persist one in-flight push snapshot for startup/runtime consumers."""
    return _persist_snapshot(
        context,
        reason=reason,
        operator_guidance=operator_guidance,
        partial_progress=partial_progress,
        stages=stages,
    )


def _persist_snapshot(
    context: PushReportContext,
    *,
    reason: str,
    operator_guidance: str,
    partial_progress: bool,
    stages: PushStageTruth,
) -> str:
    """Persist one non-terminal push snapshot to the managed latest artifact."""
    return persist_latest_push_report(
        build_push_report_payload(
            context,
            outcome=PushFlowOutcome(
                ok=False,
                reason=reason,
                operator_guidance=operator_guidance,
                stages=stages,
                partial_progress=partial_progress,
            ),
        ),
        repo_root=context.repo_root,
    )
