"""Validation and staging helpers extracted from commit_preflight."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .commit_guard_bundle import GUARD_PROFILE
from .commit_preflight_atomicity import preflight_import_index_atomicity
from .commit_pipeline_blocking import build_active_pipeline_block_report
from .commit_pipeline_blocking import (
    auto_transition_non_destructive_push_failure,
)
from .commit_preflight_support import (
    COMMIT_START_COMMAND,
    next_command_guidance,
)
from .commit_visibility import commit_visibility_payload
from .governed_executor import GovernedVcsExecutor
from .orphan_snapshot_advisory import append_orphan_snapshot_advisory
from .governed_executor_actions import (
    _build_report,
    build_stage_action,
)
from .governed_executor_commit_runtime import (
    post_commit_execution_handoff,
    post_commit_stage_handoff,
)
from .governed_executor_git import pipeline_is_stale_for_current_repo
from ...runtime.remote_commit_pipeline_state import BLOCKING_PIPELINE_STATES

_REUSABLE_PIPELINE_STATES = frozenset(
    {
        "staged",
        "guards_running",
        "guards_passed",
        "operator_approval_pending",
        "approved",
        "commit_pending",
    }
)
_PIPELINE_BLOCKING_STATES = BLOCKING_PIPELINE_STATES
_EXPLICIT_APPROVAL_PIPELINE_STATES = frozenset(
    {
        "guards_passed",
        "operator_approval_pending",
        "approved",
        "commit_pending",
    }
)


@dataclass(frozen=True, slots=True)
class CommitPreflightDeps:
    pipeline_is_stale_for_current_repo_fn: object = pipeline_is_stale_for_current_repo
    build_active_pipeline_block_report_fn: object = build_active_pipeline_block_report
    auto_transition_non_destructive_push_failure_fn: object = (
        auto_transition_non_destructive_push_failure
    )
    post_commit_execution_handoff_fn: object = post_commit_execution_handoff
    post_commit_stage_handoff_fn: object = post_commit_stage_handoff


def prepare_pipeline(
    *,
    args,
    repo_root: Path,
    resolved_policy,
    vcs_executor: GovernedVcsExecutor,
    deps: CommitPreflightDeps | None = None,
):
    """Load or restage the governed pipeline before guard replay."""
    resolved_deps = deps or CommitPreflightDeps()
    stage_warnings: list[str] = []
    pipeline = vcs_executor.load_pipeline()
    stale_pipeline = resolved_deps.pipeline_is_stale_for_current_repo_fn(
        repo_root=repo_root,
        pipeline=pipeline,
    )
    if stale_pipeline:
        stage_warnings.append(
            "Ignoring stale governed pipeline "
            f"`{pipeline.pipeline_id}` while preparing a new checkpoint for the current repo state."
        )
    if (
        pipeline.pipeline_id
        and pipeline.state in _PIPELINE_BLOCKING_STATES
        and not stale_pipeline
    ):
        pipeline = _reload_after_auto_push_failure_transition(
            repo_root=repo_root,
            pipeline=pipeline,
            vcs_executor=vcs_executor,
            deps=resolved_deps,
        )
        if pipeline.state in _PIPELINE_BLOCKING_STATES:
            return pipeline, stage_warnings, (
                resolved_deps.build_active_pipeline_block_report_fn(
                    repo_root=repo_root,
                    pipeline=pipeline,
                )
            )

    if (
        not pipeline.pipeline_id
        or pipeline.state not in _REUSABLE_PIPELINE_STATES
        or stale_pipeline
    ):
        stage_result = vcs_executor.execute(
            build_stage_action(
                repo_pack_id=resolved_policy.repo_pack_id,
                commit_message_draft=str(getattr(args, "message", "") or ""),
                push_requested=False,
                guard_profile=GUARD_PROFILE,
                work_intake_ref="devctl.commit",
                reuse_staged_index=True,
                allow_empty=bool(
                    getattr(args, "passthrough", ())
                    and "--allow-empty" in getattr(args, "passthrough", ())
                ),
                requested_by="devctl.commit",
            )
        )
        pipeline = vcs_executor.load_pipeline()
        stage_warnings = list(stage_result.warnings)
        if not stage_result.ok:
            report_warnings = list(stage_result.warnings)
            operator_guidance = stage_result.operator_guidance
            handoff_packet_id = ""
            handoff_target = ""
            handoff_error = ""
            if stage_result.reason == "git_index_write_blocked":
                commit_message = str(getattr(args, "message", "") or "")
                handoff_target, handoff_packet_id, handoff_error = (
                    resolved_deps.post_commit_stage_handoff_fn(
                        repo_root=repo_root,
                        review_channel_path=vcs_executor.review_channel_path,
                        commit_message_draft=commit_message,
                        stage_reason=stage_result.reason,
                        stage_warnings=report_warnings,
                    )
                )
                if handoff_packet_id and handoff_target:
                    operator_guidance = (
                        "The current execution sandbox cannot create `.git/index.lock`. "
                        f"Posted typed `action_request` packet `{handoff_packet_id}` "
                        f"to `{handoff_target}` so the remote-control lane can run "
                        "the same governed commit staging with repo-approved "
                        "filesystem access."
                    )
                    report_warnings.append(
                        f"commit_stage_request_packet={handoff_packet_id}"
                    )
                    report_warnings.append(
                        f"commit_stage_request_target={handoff_target}"
                    )
                elif handoff_error:
                    report_warnings.append(handoff_error)
            if (
                not handoff_packet_id
                and stage_result.reason == "git_index_write_blocked"
                and not stale_pipeline
                and pipeline.pipeline_id
                and str(getattr(pipeline, "approval_state", "") or "").strip()
                == "approved"
                and str(
                    getattr(getattr(pipeline, "intent", None), "staged_tree_hash", "")
                    or ""
                ).strip()
            ):
                handoff_target, handoff_packet_id, handoff_error = (
                    resolved_deps.post_commit_execution_handoff_fn(
                        pipeline=pipeline,
                        repo_root=repo_root,
                        review_channel_path=vcs_executor.review_channel_path,
                    )
                )
                if handoff_packet_id and handoff_target:
                    operator_guidance = (
                        "The current execution sandbox cannot create `.git/index.lock`. "
                        f"Posted typed `action_request` packet `{handoff_packet_id}` "
                        f"to `{handoff_target}` so the writable lane can run the "
                        "same approved governed commit."
                    )
                    report_warnings.append(
                        f"commit_execution_request_packet={handoff_packet_id}"
                    )
                    report_warnings.append(
                        f"commit_execution_request_target={handoff_target}"
                    )
                elif handoff_error:
                    report_warnings.append(handoff_error)
            return pipeline, stage_warnings, _build_report(
                status="blocked",
                reason=stage_result.reason,
                pipeline_id=pipeline.pipeline_id,
                pipeline_state=pipeline.state,
                operator_guidance=operator_guidance,
                warnings=report_warnings,
            )
    stage_warnings, atomicity_report = preflight_import_index_atomicity(
        repo_root=repo_root,
        pipeline=pipeline,
        stage_warnings=stage_warnings,
    )
    if atomicity_report is not None:
        return pipeline, stage_warnings, atomicity_report
    append_orphan_snapshot_advisory(
        stage_warnings,
        repo_root=repo_root,
        scan_trigger="commit_preflight",
    )
    return pipeline, stage_warnings, None


def _reload_after_auto_push_failure_transition(
    *,
    repo_root: Path,
    pipeline,
    vcs_executor: GovernedVcsExecutor,
    deps: CommitPreflightDeps,
):
    transitioned = deps.auto_transition_non_destructive_push_failure_fn(
        repo_root=repo_root,
        pipeline=pipeline,
    )
    if not transitioned:
        return pipeline
    return vcs_executor.load_pipeline()


def load_pipeline_for_explicit_approval(
    *,
    repo_root: Path,
    vcs_executor: GovernedVcsExecutor,
    deps: CommitPreflightDeps | None = None,
):
    """Return the existing governed pipeline for explicit operator approval."""
    resolved_deps = deps or CommitPreflightDeps()
    pipeline = vcs_executor.load_pipeline()
    if not pipeline.pipeline_id:
        return pipeline, _build_report(
            status="blocked",
            reason="no_pending_pipeline_to_approve",
            **commit_visibility_payload(pipeline),
            recommended_next_action="stage_commit_pipeline",
            next_command=COMMIT_START_COMMAND,
            operator_guidance=next_command_guidance(COMMIT_START_COMMAND),
        )
    if resolved_deps.pipeline_is_stale_for_current_repo_fn(
        repo_root=repo_root,
        pipeline=pipeline,
    ):
        return pipeline, _build_report(
            status="blocked",
            reason="pending_pipeline_stale_for_current_repo",
            pipeline_id=pipeline.pipeline_id,
            pipeline_state=pipeline.state,
            approval_state=pipeline.approval_state,
            **commit_visibility_payload(pipeline),
            recommended_next_action="stage_commit_pipeline",
            next_command=COMMIT_START_COMMAND,
            operator_guidance=next_command_guidance(COMMIT_START_COMMAND),
        )
    if pipeline.state in _PIPELINE_BLOCKING_STATES:
        return pipeline, resolved_deps.build_active_pipeline_block_report_fn(
            repo_root=repo_root,
            pipeline=pipeline,
        )
    if pipeline.state not in _EXPLICIT_APPROVAL_PIPELINE_STATES:
        return pipeline, _build_report(
            status="blocked",
            reason="pipeline_not_waiting_for_operator_approval",
            pipeline_id=pipeline.pipeline_id,
            pipeline_state=pipeline.state,
            approval_state=pipeline.approval_state,
            **commit_visibility_payload(pipeline),
            operator_guidance=(
                "Only guarded pipelines awaiting or holding approval may be "
                "resumed with `devctl commit --approve-pending`."
            ),
        )
    return pipeline, None
