"""Stage-failure reporting for governed commit preflight."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...review_channel.packet_contract import STAGE_PIPELINE_ACTION_REQUEST_ACTIONS
from .commit_action_result_report import action_result_report_fields
from .governed_executor_actions import _build_report


@dataclass(frozen=True, slots=True)
class StageFailureContext:
    args: object
    repo_root: Path
    vcs_executor: object
    deps: object
    pipeline: object
    stage_result: object
    stale_pipeline: bool


def stage_failure_report(context: StageFailureContext) -> dict[str, object]:
    report_warnings = list(context.stage_result.warnings)
    operator_guidance = context.stage_result.operator_guidance
    handoff_packet_id = ""
    if _stage_handoff_requested(context.stage_result):
        operator_guidance, handoff_packet_id = _post_stage_index_handoff(
            context=context,
            report_warnings=report_warnings,
            fallback_guidance=operator_guidance,
        )
    if _should_post_execution_handoff(
        pipeline=context.pipeline,
        stage_result=context.stage_result,
        stale_pipeline=context.stale_pipeline,
        handoff_packet_id=handoff_packet_id,
    ):
        operator_guidance = _post_execution_index_handoff(
            context=context,
            report_warnings=report_warnings,
            fallback_guidance=operator_guidance,
        )
    return _build_report(
        status="blocked",
        reason=context.stage_result.reason,
        pipeline_id=context.pipeline.pipeline_id,
        pipeline_state=context.pipeline.state,
        **action_result_report_fields(context.stage_result),
        operator_guidance=operator_guidance,
        warnings=report_warnings,
    )


def _post_stage_index_handoff(
    *,
    context: StageFailureContext,
    report_warnings: list[str],
    fallback_guidance: str,
) -> tuple[str, str]:
    commit_message = str(getattr(context.args, "message", "") or "")
    handoff_target, handoff_packet_id, handoff_error = (
        context.deps.post_commit_stage_handoff_fn(
            repo_root=context.repo_root,
            review_channel_path=context.vcs_executor.review_channel_path,
            commit_message_draft=commit_message,
            stage_reason=context.stage_result.reason,
            stage_warnings=report_warnings,
        )
    )
    if handoff_packet_id and handoff_target:
        report_warnings.extend(
            [
                f"commit_stage_request_packet={handoff_packet_id}",
                f"commit_stage_request_target={handoff_target}",
            ]
        )
        return (
            "The current execution sandbox cannot create `.git/index.lock`. "
            f"Posted typed `action_request` packet `{handoff_packet_id}` "
            f"to `{handoff_target}` so the remote-control lane can run the "
            "same governed commit staging with repo-approved filesystem access.",
            handoff_packet_id,
        )
    if handoff_error:
        report_warnings.append(handoff_error)
    return fallback_guidance, ""


def _should_post_execution_handoff(
    *,
    pipeline,
    stage_result,
    stale_pipeline: bool,
    handoff_packet_id: str,
) -> bool:
    if handoff_packet_id or stage_result.reason != "git_index_write_blocked":
        return False
    if stale_pipeline or not pipeline.pipeline_id:
        return False
    approved = str(getattr(pipeline, "approval_state", "") or "").strip() == "approved"
    staged_tree = str(
        getattr(getattr(pipeline, "intent", None), "staged_tree_hash", "") or ""
    ).strip()
    return approved and bool(staged_tree)


def _stage_handoff_requested(stage_result: object) -> bool:
    remediation = str(getattr(stage_result, "remediation", "") or "").strip()
    if remediation in STAGE_PIPELINE_ACTION_REQUEST_ACTIONS:
        return True
    return str(getattr(stage_result, "reason", "") or "") == "git_index_write_blocked"


def _post_execution_index_handoff(
    *,
    context: StageFailureContext,
    report_warnings: list[str],
    fallback_guidance: str,
) -> str:
    handoff_target, handoff_packet_id, handoff_error = (
        context.deps.post_commit_execution_handoff_fn(
            pipeline=context.pipeline,
            repo_root=context.repo_root,
            review_channel_path=context.vcs_executor.review_channel_path,
        )
    )
    if handoff_packet_id and handoff_target:
        report_warnings.extend(
            [
                f"commit_execution_request_packet={handoff_packet_id}",
                f"commit_execution_request_target={handoff_target}",
            ]
        )
        return (
            "The current execution sandbox cannot create `.git/index.lock`. "
            f"Posted typed `action_request` packet `{handoff_packet_id}` "
            f"to `{handoff_target}` so the writable lane can run the same "
            "approved governed commit."
        )
    if handoff_error:
        report_warnings.append(handoff_error)
    return fallback_guidance
