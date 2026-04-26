"""Commit execution phase for the governed VCS pipeline."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from ...runtime import ActionResult, TypedAction
from ...runtime.action_contracts import ActionOutcome
from ...runtime.remote_commit_pipeline_models import RemoteCommitPipelineContract
from ...runtime.vcs import run_git_capture
from .governed_executor_actions import APPROVAL_PACKET_KIND
from .governed_executor_authorization import build_push_authorization
from ...runtime.commit_packet_gate import check_commit_packet_gate
from .governed_executor_commit_runtime import (
    attention_revision_stale as runtime_attention_revision_stale,
    live_attention_revision as runtime_live_attention_revision,
    load_live_review_state as runtime_load_live_review_state,
    post_commit_execution_handoff as runtime_post_commit_execution_handoff,
    refresh_and_recheck_attention_revision as runtime_refresh_and_recheck_attention_revision,
    resolve_commit_execution_target as runtime_resolve_commit_execution_target,
)
from .governed_executor_field_access import bool_field, string_value
from .governed_executor_git import head_commit, index_tree_hash
from .governed_executor_phases import (
    _git_index_failure_guidance,
    _git_index_failure_reason,
    _git_index_write_blocked,
)
from .governed_executor_support import (
    CommitBlock,
    CommitFailureDetails,
    CommitInvocation,
    commit_failed_pipeline,
    commit_recorded_pipeline,
    evaluate_commit_readiness,
)
from .governed_executor_sync import (
    get_approval_decision_packet,
    sync_pipeline_approval,
)

ResultBuilder = Callable[..., ActionResult]
PipelinePersister = Callable[[RemoteCommitPipelineContract], list[str]]
EventPacketsLoader = Callable[[], tuple[Any, ...]]


@dataclass(frozen=True, slots=True)
class CommitPipelineContext:
    """Immutable executor-owned inputs for the governed commit phase."""

    repo_root: Path
    review_channel_path: Path | None
    load_pipeline: Callable[[], RemoteCommitPipelineContract]
    persist_pipeline: PipelinePersister
    persist_pipeline_contract_only: PipelinePersister
    event_packets_loader: EventPacketsLoader
    pipeline_artifact_relpath: str
    result_builder: ResultBuilder


def execute_commit(
    action: TypedAction,
    *,
    context: CommitPipelineContext,
) -> ActionResult:
    """Run the commit phase of the governed commit pipeline."""
    pipeline = context.load_pipeline()
    requested_pipeline_id = string_value(action.parameters.get("pipeline_id"))
    if not pipeline.pipeline_id or (
        requested_pipeline_id and requested_pipeline_id != pipeline.pipeline_id
    ):
        return context.result_builder(
            action_id=action.action_id,
            ok=False,
            status=ActionOutcome.FAIL,
            reason="pipeline_not_found",
            operator_guidance="Stage a pipeline first, then rerun `vcs.commit`.",
        )

    pipeline = sync_pipeline_approval(
        pipeline,
        context.event_packets_loader(),
        approval_packet_kind=APPROVAL_PACKET_KIND,
    )
    pipeline = _acquire_attention_revision_lease(
        pipeline=pipeline,
        context=context,
    )
    attention_block = _attention_revision_preflight_block(
        action_id=action.action_id,
        context=context,
        pipeline=pipeline,
    )
    if attention_block is not None:
        return attention_block
    pending_block = check_commit_packet_gate(
        repo_root=context.repo_root,
        review_channel_path=context.review_channel_path,
        load_review_state_fn=lambda: runtime_load_live_review_state(
            repo_root=context.repo_root,
            review_channel_path=context.review_channel_path,
        ),
        resolve_target_fn=runtime_resolve_commit_execution_target,
    )
    if pending_block is not None:
        return _commit_block_result(
            action_id=action.action_id,
            context=context,
            blocked=CommitBlock(
                pipeline=replace(
                    pipeline,
                    state="push_blocked",
                    blocked_reason="pending_reviewer_packets",
                ),
                reason="pending_reviewer_packets",
                guidance=pending_block,
            ),
        )
    readiness = evaluate_commit_readiness(
        pipeline=pipeline,
        repo_root=context.repo_root,
        request=CommitInvocation(
            current_tree_hash=index_tree_hash(context.repo_root),
            requested_commit_message=string_value(
                action.parameters.get("commit_message_draft")
            ),
            amend=bool_field(action.parameters, "amend"),
            allow_empty=bool_field(action.parameters, "allow_empty"),
            no_edit=bool_field(action.parameters, "no_edit"),
        ),
    )
    if isinstance(readiness, CommitBlock):
        return _commit_block_result(
            action_id=action.action_id,
            context=context,
            blocked=readiness,
        )

    pipeline = readiness.pipeline
    commit_pending = replace(
        pipeline,
        state="commit_pending",
        commit_action_id=action.action_id,
        blocked_reason="",
    )
    context.persist_pipeline_contract_only(commit_pending)

    commit_code, _, commit_error = run_git_capture(
        list(readiness.git_commit_args),
        repo_root=context.repo_root,
        extra_env={"DEVCTL_GOVERNED_COMMIT": "1"},
    )
    if commit_code != 0:
        return _commit_failure_result(
            action_id=action.action_id,
            context=context,
            pending_pipeline=commit_pending,
            commit_error=commit_error,
        )

    commit_sha = head_commit(context.repo_root)
    decision = get_approval_decision_packet(
        context.event_packets_loader(),
        commit_pending,
        approval_packet_kind=APPROVAL_PACKET_KIND,
    )
    completed = commit_recorded_pipeline(
        pending_pipeline=commit_pending,
        action_id=action.action_id,
        commit_sha=commit_sha,
        push_authorization=build_push_authorization(
            pipeline=commit_pending,
            commit_sha=commit_sha,
            decision_packet=decision,
            approval_mode="commit_pipeline_approval",
            request_packet_id=commit_pending.approval_packet_id,
        ),
        artifact_relpath=context.pipeline_artifact_relpath,
        result_builder=context.result_builder,
    )
    return _commit_success_result(
        action_id=action.action_id,
        context=context,
        completed=completed,
    )


def _acquire_attention_revision_lease(
    *,
    pipeline: RemoteCommitPipelineContract,
    context: CommitPipelineContext,
) -> RemoteCommitPipelineContract:
    """Pin the live attention revision onto the pipeline at fresh approval.

    Q100 lease: once the pipeline holds `approval_state=approved`, subsequent
    typed-state writes (event projections, inbox updates, dogfood rows) will
    bump the live `packet_inbox.attention_revision`. Without a held lease the
    commit-record check would compare the pipeline's pre-guard revision to the
    post-guard live revision and self-invalidate the already-approved commit.
    Capturing the lease here locks the commit window to the approval-time
    revision so mid-bundle writes do not rescind the operator's approval.
    """
    if pipeline.approval_state != "approved":
        return pipeline
    if pipeline.attention_revision_lease:
        return pipeline
    live_revision = runtime_live_attention_revision(
        repo_root=context.repo_root,
        review_channel_path=context.review_channel_path,
    )
    if not live_revision:
        return pipeline
    leased = replace(pipeline, attention_revision_lease=live_revision)
    context.persist_pipeline_contract_only(leased)
    return leased


def _attention_revision_preflight_block(
    *,
    action_id: str,
    context: CommitPipelineContext,
    pipeline: RemoteCommitPipelineContract,
) -> ActionResult | None:
    if not runtime_attention_revision_stale(
        repo_root=context.repo_root,
        review_channel_path=context.review_channel_path,
        held_lease=pipeline.attention_revision_lease,
    ):
        return None
    attention_decision = runtime_refresh_and_recheck_attention_revision(
        repo_root=context.repo_root,
        review_channel_path=context.review_channel_path,
        held_lease=pipeline.attention_revision_lease,
        next_step_label="commit preflight",
        stale_check_fn=runtime_attention_revision_stale,
    )
    if attention_decision.status == "refresh_failed":
        return _commit_block_result(
            action_id=action_id,
            context=context,
            blocked=CommitBlock(
                pipeline=replace(
                    pipeline,
                    state="push_blocked",
                    blocked_reason="startup_context_refresh_failed",
                ),
                reason="startup_context_refresh_failed",
                guidance=(
                    "The governed commit preflight could not refresh "
                    "`startup-context`; repair that command before committing."
                ),
            ),
        )
    if attention_decision.status == "stale":
        return _attention_revision_stale_result(
            action_id=action_id,
            context=context,
            pipeline=pipeline,
        )
    return None


def _attention_revision_stale_result(
    *,
    action_id: str,
    context: CommitPipelineContext,
    pipeline: RemoteCommitPipelineContract,
) -> ActionResult:
    blocked = replace(
        pipeline,
        state="push_blocked",
        blocked_reason="attention_revision_stale",
    )
    warnings = context.persist_pipeline_contract_only(blocked)
    return context.result_builder(
        action_id=action_id,
        ok=False,
        status=ActionOutcome.FAIL,
        reason="attention_revision_stale",
        operator_guidance=(
            "Typed packet attention changed since the last startup receipt. "
            "Rerun `startup-context`, refresh `session-resume`, and acknowledge "
            "the new inbox state before committing."
        ),
        warnings=tuple(warnings),
        artifact_paths=(context.pipeline_artifact_relpath,),
    )


def _commit_block_result(
    *,
    action_id: str,
    context: CommitPipelineContext,
    blocked: CommitBlock,
) -> ActionResult:
    blocked_warnings = context.persist_pipeline_contract_only(blocked.pipeline)
    return context.result_builder(
        action_id=action_id,
        ok=False,
        status=ActionOutcome.FAIL,
        reason=blocked.reason,
        operator_guidance=blocked.guidance,
        warnings=tuple(blocked_warnings),
        artifact_paths=(context.pipeline_artifact_relpath,),
    )


def _commit_failure_result(
    *,
    action_id: str,
    context: CommitPipelineContext,
    pending_pipeline: RemoteCommitPipelineContract,
    commit_error: str,
) -> ActionResult:
    failure_reason = _git_index_failure_reason(
        commit_error,
        default="commit_failed",
    )
    failure_guidance = (
        _git_index_failure_guidance()
        if _git_index_write_blocked(commit_error)
        else "Inspect the git commit failure, repair the repo state, then recover the pipeline."
    )
    handoff_packet_id = ""
    handoff_target = ""
    handoff_error = ""
    if failure_reason == "git_index_write_blocked":
        handoff_target, handoff_packet_id, handoff_error = (
            runtime_post_commit_execution_handoff(
                repo_root=context.repo_root,
                review_channel_path=context.review_channel_path,
                pipeline=pending_pipeline,
            )
        )
        if handoff_packet_id and handoff_target:
            failure_guidance = (
                "The current execution sandbox cannot create `.git/index.lock`. "
                f"Posted typed `action_request` packet `{handoff_packet_id}` "
                f"to `{handoff_target}` so the writable lane can run the "
                "same approved governed commit."
            )
    failed = commit_failed_pipeline(
        pending_pipeline=pending_pipeline,
        action_id=action_id,
        commit_error=commit_error,
        artifact_relpath=context.pipeline_artifact_relpath,
        result_builder=context.result_builder,
        failure=CommitFailureDetails(
            reason=failure_reason,
            operator_guidance=failure_guidance,
        ),
    )
    warnings = context.persist_pipeline_contract_only(failed)
    if handoff_packet_id:
        warnings.append(f"commit_execution_request_packet={handoff_packet_id}")
    if handoff_target:
        warnings.append(f"commit_execution_request_target={handoff_target}")
    if handoff_error:
        warnings.append(handoff_error)
    if commit_error:
        warnings.append(commit_error)
    return context.result_builder(
        action_id=action_id,
        ok=False,
        status=ActionOutcome.FAIL,
        reason=failure_reason,
        operator_guidance=failure_guidance,
        warnings=tuple(warnings),
        artifact_paths=(context.pipeline_artifact_relpath,),
    )


def _commit_success_result(
    *,
    action_id: str,
    context: CommitPipelineContext,
    completed: RemoteCommitPipelineContract,
) -> ActionResult:
    warnings = context.persist_pipeline_contract_only(completed)
    return context.result_builder(
        action_id=action_id,
        ok=True,
        status=ActionOutcome.PASS,
        reason="commit_recorded",
        operator_guidance=(
            "Run the existing governed `vcs.push` action to publish the "
            "new commit."
        ),
        warnings=tuple(warnings),
        artifact_paths=(context.pipeline_artifact_relpath,),
    )
