"""Stage and commit execution phases for the governed VCS pipeline."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

from ...runtime import ActionResult, TypedAction
from ...runtime.action_contracts import ActionOutcome
from ...runtime.remote_commit_pipeline_models import RemoteCommitPipelineContract
from ...runtime.review_snapshot_refresh import refresh_and_stage_review_snapshot
from ...runtime.vcs import run_git_capture
from .governed_executor_actions import (
    APPROVAL_PACKET_KIND,
    _ACTIVE_PIPELINE_STATES,
    build_stage_action,
    build_staged_pipeline,
)
from .governed_executor_authorization import build_push_authorization
from .governed_executor_field_access import (
    bool_field,
    field,
    string_field,
    string_value,
)
from .governed_executor_git import (
    current_branch,
    dirty_paths,
    head_commit,
    index_tree_hash,
    normalize_paths,
    staged_diff_summary,
    staged_paths,
)
from .governed_executor_support import (
    CommitBlock,
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
EventPacketsLoader = Callable[[], tuple]


def _refresh_snapshot_staging(*, repo_root: Path) -> tuple[list[str], list[str]]:
    """Return refresh warnings plus the staged-path view after refresh."""
    return (
        refresh_and_stage_review_snapshot(repo_root=repo_root),
        staged_paths(repo_root),
    )


def execute_stage(
    action: TypedAction,
    *,
    repo_root: Path,
    startup_context_fn: Any,
    load_pipeline: Callable[[], RemoteCommitPipelineContract],
    persist_pipeline: PipelinePersister,
    pipeline_artifact_relpath: str,
    result_builder: ResultBuilder,
) -> ActionResult:
    """Run the stage phase of the governed commit pipeline."""
    refresh_warnings: list[str] = []
    startup_context = startup_context_fn(repo_root=repo_root)
    reviewer_gate = field(startup_context, "reviewer_gate")
    checkpoint_stage_allowed = (
        string_field(field(startup_context, "push_decision"), "action")
        == "await_checkpoint"
        and bool_field(reviewer_gate, "checkpoint_permitted", default=True)
    )
    # `vcs.stage` is the governed checkpoint path, so allow it on `await_checkpoint`.
    if (
        bool_field(reviewer_gate, "implementation_blocked")
        and not checkpoint_stage_allowed
    ):
        return result_builder(
            action_id=action.action_id,
            ok=False,
            status=ActionOutcome.FAIL,
            reason=string_field(reviewer_gate, "implementation_block_reason")
            or "reviewer_gate_blocked",
            operator_guidance=(
                "Repair the review/startup state before staging a remote "
                "commit pipeline."
            ),
        )

    current = load_pipeline()
    if current.pipeline_id and current.state in _ACTIVE_PIPELINE_STATES:
        return result_builder(
            action_id=action.action_id,
            ok=False,
            status=ActionOutcome.FAIL,
            reason="active_pipeline_exists",
            operator_guidance=(
                "Recover or complete the current remote commit pipeline "
                "before staging another one."
            ),
            warnings=(f"active_pipeline_id={current.pipeline_id}",),
            artifact_paths=(pipeline_artifact_relpath,),
        )

    reuse_staged_index = bool_field(action.parameters, "reuse_staged_index")
    allow_empty = bool_field(action.parameters, "allow_empty")
    worktree_dirty = dirty_paths(repo_root)
    selected_paths = normalize_paths(action.parameters.get("paths"))
    if reuse_staged_index:
        refresh_warnings, staged = _refresh_snapshot_staging(repo_root=repo_root)
        if not staged and not allow_empty:
            return result_builder(
                action_id=action.action_id,
                ok=False,
                status=ActionOutcome.FAIL,
                reason="no_staged_changes",
                operator_guidance=(
                    "Stage changes first or rerun with `--allow-empty`."
                ),
            )
    elif not worktree_dirty:
        return result_builder(
            action_id=action.action_id,
            ok=False,
            status=ActionOutcome.FAIL,
            reason="no_changes_to_stage",
            operator_guidance="Create or modify repo files before running `vcs.stage`.",
        )
    if not reuse_staged_index and selected_paths:
        outside_scope = sorted(set(worktree_dirty) - set(selected_paths))
        if outside_scope:
            return result_builder(
                action_id=action.action_id,
                ok=False,
                status=ActionOutcome.FAIL,
                reason="dirty_paths_outside_scope",
                operator_guidance=(
                    "Either expand the selected stage scope or clean the "
                    "other dirty paths before retrying."
                ),
                warnings=tuple(outside_scope),
            )
    elif not reuse_staged_index:
        selected_paths = worktree_dirty

    if not reuse_staged_index:
        stage_code, _, stage_error = run_git_capture(
            ["add", "-A", "--", *selected_paths],
            repo_root=repo_root,
        )
        if stage_code != 0:
            return result_builder(
                action_id=action.action_id,
                ok=False,
                status=ActionOutcome.FAIL,
                reason="git_add_failed",
                operator_guidance="Repair the git index error and rerun `vcs.stage`.",
                warnings=((stage_error,) if stage_error else ()),
            )

        refresh_warnings, staged = _refresh_snapshot_staging(repo_root=repo_root)
        if not staged and not allow_empty:
            return result_builder(
                action_id=action.action_id,
                ok=False,
                status=ActionOutcome.FAIL,
                reason="no_staged_changes",
                operator_guidance=(
                    "The selected scope did not produce a staged snapshot. "
                    "Adjust the path list or make a real change first."
                ),
                warnings=tuple(refresh_warnings),
            )

    tree_hash = index_tree_hash(repo_root)
    if not tree_hash:
        return result_builder(
            action_id=action.action_id,
            ok=False,
            status=ActionOutcome.FAIL,
            reason="staged_tree_hash_unavailable",
            operator_guidance="Repair the git index state and rerun `vcs.stage`.",
        )

    new_pipeline = build_staged_pipeline(
        action=action,
        staged=staged,
        tree_hash=tree_hash,
        diff_summary=staged_diff_summary(repo_root),
        branch=current_branch(repo_root),
    )
    return result_builder(
        action_id=action.action_id,
        ok=True,
        status=ActionOutcome.PASS,
        reason="pipeline_staged",
        operator_guidance=(
            "Run the routed guard bundle, then post the operator approval "
            "packet before `vcs.commit`."
        ),
        warnings=tuple([*refresh_warnings, *persist_pipeline(new_pipeline)]),
        artifact_paths=(pipeline_artifact_relpath,),
    )


def execute_commit(
    action: TypedAction,
    *,
    repo_root: Path,
    load_pipeline: Callable[[], RemoteCommitPipelineContract],
    persist_pipeline: PipelinePersister,
    event_packets_loader: EventPacketsLoader,
    pipeline_artifact_relpath: str,
    result_builder: ResultBuilder,
) -> ActionResult:
    """Run the commit phase of the governed commit pipeline."""
    pipeline = load_pipeline()
    requested_pipeline_id = string_value(action.parameters.get("pipeline_id"))
    if not pipeline.pipeline_id or (
        requested_pipeline_id and requested_pipeline_id != pipeline.pipeline_id
    ):
        return result_builder(
            action_id=action.action_id,
            ok=False,
            status=ActionOutcome.FAIL,
            reason="pipeline_not_found",
            operator_guidance="Stage a pipeline first, then rerun `vcs.commit`.",
        )

    pipeline = sync_pipeline_approval(
        pipeline,
        event_packets_loader(),
        approval_packet_kind=APPROVAL_PACKET_KIND,
    )
    readiness = evaluate_commit_readiness(
        pipeline=pipeline,
        current_tree_hash=index_tree_hash(repo_root),
        requested_commit_message=string_value(
            action.parameters.get("commit_message_draft")
        ),
        amend=bool_field(action.parameters, "amend"),
        allow_empty=bool_field(action.parameters, "allow_empty"),
        no_edit=bool_field(action.parameters, "no_edit"),
    )
    if isinstance(readiness, CommitBlock):
        blocked_warnings = persist_pipeline(readiness.pipeline)
        return result_builder(
            action_id=action.action_id,
            ok=False,
            status=ActionOutcome.FAIL,
            reason=readiness.reason,
            operator_guidance=readiness.guidance,
            warnings=tuple(blocked_warnings),
            artifact_paths=(pipeline_artifact_relpath,),
        )
    pipeline = readiness.pipeline
    commit_pending = replace(
        pipeline,
        state="commit_pending",
        commit_action_id=action.action_id,
        blocked_reason="",
    )
    persist_pipeline(commit_pending)

    commit_code, _, commit_error = run_git_capture(
        list(readiness.git_commit_args),
        repo_root=repo_root,
    )
    if commit_code != 0:
        failed = commit_failed_pipeline(
            pending_pipeline=commit_pending,
            action_id=action.action_id,
            commit_error=commit_error,
            artifact_relpath=pipeline_artifact_relpath,
            result_builder=result_builder,
        )
        warnings = persist_pipeline(failed)
        return result_builder(
            action_id=action.action_id,
            ok=False,
            status=ActionOutcome.FAIL,
            reason="commit_failed",
            operator_guidance=(
                "Inspect the git commit failure, repair the repo state, "
                "then recover the pipeline."
            ),
            warnings=tuple(warnings + ([commit_error] if commit_error else [])),
            artifact_paths=(pipeline_artifact_relpath,),
        )

    commit_sha = head_commit(repo_root)
    decision = get_approval_decision_packet(
        event_packets_loader(),
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
        artifact_relpath=pipeline_artifact_relpath,
        result_builder=result_builder,
    )
    warnings = persist_pipeline(completed)
    return result_builder(
        action_id=action.action_id,
        ok=True,
        status=ActionOutcome.PASS,
        reason="commit_recorded",
        operator_guidance=(
            "Run the existing governed `vcs.push` action to publish the "
            "new commit."
        ),
        warnings=tuple(warnings),
        artifact_paths=(pipeline_artifact_relpath,),
    )
