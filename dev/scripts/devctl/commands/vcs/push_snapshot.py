"""Push-report payload helpers for guarded push recovery."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...runtime import ActionResult
from .push_artifact import persist_latest_push_report
from .push_flow import PushFlowOutcome
from .push_report import PushReportInputs, PushStageTruth, build_push_report


@dataclass(frozen=True, slots=True)
class PushReportContext:
    """Inputs reused across final and intermediate push reports."""

    policy: object
    state: object
    args: object
    head_commit: str
    typed_action: dict[str, Any]
    artifact_path: str


def build_push_report_payload(
    context: PushReportContext,
    *,
    outcome: PushFlowOutcome,
) -> dict[str, Any]:
    """Build the canonical push report payload for the current execution state."""
    state = context.state
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
            artifact_path=context.artifact_path,
        )
    )


def persist_published_remote_snapshot(
    context: PushReportContext,
    *,
    reason: str,
    operator_guidance: str,
    partial_progress: bool,
) -> str:
    """Persist a recovery snapshot once remote publication is known to be real."""
    return persist_latest_push_report(
        build_push_report_payload(
            context,
            outcome=PushFlowOutcome(
                ok=True,
                reason=reason,
                operator_guidance=operator_guidance,
                stages=PushStageTruth(
                    validation_ready=True,
                    published_remote=True,
                ),
                partial_progress=partial_progress,
            ),
        )
    )
