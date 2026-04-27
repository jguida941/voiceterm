"""Stage execution helpers for the governed VCS pipeline."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from ...runtime import ActionResult, TypedAction
from ...runtime.action_contracts import ActionOutcome
from ...runtime.remote_commit_pipeline_models import RemoteCommitPipelineContract
from .governed_executor_actions import build_staged_pipeline
from .governed_executor_field_access import bool_field
from .governed_executor_git import (
    current_branch,
    dirty_paths,
    normalize_paths,
    staged_diff_summary,
)
from .governed_executor_stage_attention import (
    attention_revision_block as _attention_revision_block,
    check_stage_preconditions as _check_stage_preconditions,
)
from .governed_executor_stage_snapshot import (
    non_receipt_artifact_paths,
    refresh_and_stage_review_snapshot,
    refresh_snapshot_staging,
)
from .governed_executor_index_lock import (
    git_index_busy_guidance as _git_index_busy_guidance,
    git_index_failure_guidance as _git_index_failure_guidance,
    git_index_failure_reason as _git_index_failure_reason,
    git_index_result_kwargs as _git_index_result_kwargs,
    git_index_write_blocked as _git_index_write_blocked,
    review_snapshot_index_failure_warning as _review_snapshot_index_failure_warning,
)
from .governed_executor_stage_index import (
    stage_selected_paths as _stage_selected_paths,
    staged_tree_hash_or_failure,
)

ResultBuilder = Callable[..., ActionResult]
PipelinePersister = Callable[[RemoteCommitPipelineContract], list[str]]


def _staged_index_preservation_failed(
    action: TypedAction,
    *,
    refresh_warnings: list[str],
    lost_paths: list[str],
    operator_guidance: str,
    result_builder: ResultBuilder,
) -> ActionResult:
    return result_builder(
        action_id=action.action_id,
        ok=False,
        status=ActionOutcome.FAIL,
        reason="staged_index_preservation_failed",
        operator_guidance=operator_guidance,
        warnings=tuple([*refresh_warnings, *lost_paths]),
    )


def _no_staged_changes_result(
    action: TypedAction,
    *,
    operator_guidance: str,
    warnings: tuple[str, ...] = (),
    result_builder: ResultBuilder,
) -> ActionResult:
    return result_builder(
        action_id=action.action_id,
        ok=False,
        status=ActionOutcome.FAIL,
        reason="no_staged_changes",
        operator_guidance=operator_guidance,
        warnings=warnings,
    )


def _snapshot_only_staged_scope_result(
    action: TypedAction,
    *,
    repo_root: Path,
    staged: list[str],
    worktree_dirty: list[str],
    result_builder: ResultBuilder,
) -> ActionResult | None:
    """Block snapshot-only governed commits when real work remains dirty."""
    non_artifact_staged = non_receipt_artifact_paths(
        repo_root=repo_root,
        paths=staged,
    )
    non_artifact_dirty = non_receipt_artifact_paths(
        repo_root=repo_root,
        paths=worktree_dirty,
    )
    if non_artifact_staged or not non_artifact_dirty:
        return None
    return result_builder(
        action_id=action.action_id,
        ok=False,
        status=ActionOutcome.FAIL,
        reason="staged_scope_missing_dirty_work",
        operator_guidance=(
            "The ReviewSnapshot refresh staged only receipt artifacts while "
            "real work remains dirty. Stage the intended paths first, or use "
            "`review-snapshot --write --receipt-commit` for a snapshot-only receipt."
        ),
        warnings=tuple(non_artifact_dirty),
    )


def _refresh_staged_snapshot(
    action: TypedAction,
    *,
    repo_root: Path,
    allow_empty: bool,
    no_staged_guidance: str,
    lost_paths_guidance: str,
    result_builder: ResultBuilder,
) -> tuple[ActionResult | None, list[str], list[str]]:
    refresh_warnings, staged, lost_paths = refresh_snapshot_staging(
        repo_root=repo_root,
        refresh_snapshot_fn=refresh_and_stage_review_snapshot,
    )
    index_failure = _review_snapshot_index_failure_result(
        action=action,
        refresh_warnings=refresh_warnings,
        result_builder=result_builder,
    )
    if index_failure is not None:
        return index_failure, [], []
    if lost_paths:
        return (
            _staged_index_preservation_failed(
                action,
                refresh_warnings=refresh_warnings,
                lost_paths=lost_paths,
                operator_guidance=lost_paths_guidance,
                result_builder=result_builder,
            ),
            [],
            [],
        )
    if not staged and not allow_empty:
        return (
            _no_staged_changes_result(
                action,
                operator_guidance=no_staged_guidance,
                warnings=tuple(refresh_warnings),
                result_builder=result_builder,
            ),
            [],
            [],
        )
    return None, refresh_warnings, staged


def _review_snapshot_index_failure_result(
    *,
    action: TypedAction,
    refresh_warnings: list[str],
    result_builder: ResultBuilder,
) -> ActionResult | None:
    index_warning = _review_snapshot_index_failure_warning(refresh_warnings)
    if not index_warning:
        return None
    reason = _git_index_failure_reason(
        index_warning,
        default="review_snapshot_stage_failed",
    )
    guidance = (
        _git_index_failure_guidance()
        if _git_index_write_blocked(index_warning)
        else _git_index_busy_guidance()
        if reason == "git_index_lock_busy"
        else "Repair ReviewSnapshot staging and rerun `vcs.stage`."
    )
    return result_builder(
        action_id=action.action_id,
        ok=False,
        status=ActionOutcome.FAIL,
        reason=reason,
        operator_guidance=guidance,
        warnings=tuple(refresh_warnings),
        **_git_index_result_kwargs(
            error=index_warning,
            reason=reason,
            default_reason="review_snapshot_stage_failed",
        ),
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

    precondition_fail = _check_stage_preconditions(
        action,
        repo_root=repo_root,
        startup_context=startup_context,
        load_pipeline=load_pipeline,
        pipeline_artifact_relpath=pipeline_artifact_relpath,
        result_builder=result_builder,
    )
    if precondition_fail is not None:
        return precondition_fail

    reuse_staged_index = bool_field(action.parameters, "reuse_staged_index")
    allow_empty = bool_field(action.parameters, "allow_empty")
    worktree_dirty = dirty_paths(repo_root)
    selected_paths = normalize_paths(action.parameters.get("paths"))
    if reuse_staged_index:
        failure, refresh_warnings, staged = _refresh_staged_snapshot(
            action,
            repo_root=repo_root,
            allow_empty=allow_empty,
            no_staged_guidance="Stage changes first or rerun with `--allow-empty`.",
            lost_paths_guidance=(
                "The managed ReviewSnapshot refresh removed user-staged "
                "content from the index. Restage the affected paths and "
                "rerun `devctl commit`; the refresh path must add the "
                "artifact, not replace your staged set."
            ),
            result_builder=result_builder,
        )
        if failure is not None:
            return failure
        scope_failure = _snapshot_only_staged_scope_result(
            action,
            repo_root=repo_root,
            staged=staged,
            worktree_dirty=worktree_dirty,
            result_builder=result_builder,
        )
        if scope_failure is not None:
            return scope_failure
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
        stage_failure = _stage_selected_paths(
            action,
            repo_root=repo_root,
            selected_paths=selected_paths,
            result_builder=result_builder,
        )
        if stage_failure is not None:
            return stage_failure
        failure, refresh_warnings, staged = _refresh_staged_snapshot(
            action,
            repo_root=repo_root,
            allow_empty=allow_empty,
            no_staged_guidance=(
                "The selected scope did not produce a staged snapshot. "
                "Adjust the path list or make a real change first."
            ),
            lost_paths_guidance=(
                "The managed ReviewSnapshot refresh removed staged content "
                "from the index after `git add`. Restage the affected "
                "paths and rerun `vcs.stage`."
            ),
            result_builder=result_builder,
        )
        if failure is not None:
            return failure

    tree_hash, tree_failure = staged_tree_hash_or_failure(
        action,
        repo_root=repo_root,
        result_builder=result_builder,
    )
    if tree_failure is not None:
        return tree_failure

    new_pipeline = build_staged_pipeline(
        action=action,
        staged=staged,
        tree_hash=tree_hash,
        diff_summary=staged_diff_summary(repo_root),
        branch=current_branch(repo_root),
        repo_root=repo_root,
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
