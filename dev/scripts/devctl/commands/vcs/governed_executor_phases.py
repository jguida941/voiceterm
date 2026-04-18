"""Stage execution helpers for the governed VCS pipeline."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from ...runtime import ActionResult, TypedAction
from ...runtime.action_contracts import ActionOutcome
from ...runtime.remote_commit_pipeline_models import RemoteCommitPipelineContract
from ...runtime.vcs import run_git_capture
from .governed_executor_actions import build_staged_pipeline
from .governed_executor_field_access import bool_field
from .governed_executor_git import (
    current_branch,
    dirty_paths,
    index_tree_hash_result,
    normalize_paths,
    staged_diff_summary,
)
from .governed_executor_stage_attention import (
    attention_revision_block as _attention_revision_block,
    check_stage_preconditions as _check_stage_preconditions,
)
from .governed_executor_stage_snapshot import refresh_snapshot_staging

ResultBuilder = Callable[..., ActionResult]
PipelinePersister = Callable[[RemoteCommitPipelineContract], list[str]]


def _git_index_write_blocked(error: str) -> bool:
    text = str(error or "")
    return "index.lock" in text and "Operation not permitted" in text


def _git_index_failure_reason(error: str, *, default: str) -> str:
    if _git_index_write_blocked(error):
        return "git_index_write_blocked"
    return default


def _git_index_failure_guidance() -> str:
    return (
        "The current execution sandbox cannot create `.git/index.lock`. "
        "Rerun the governed command with repo-approved filesystem access or "
        "from the implementer-owned local terminal lane, then retry `vcs.stage`."
    )


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


def _stage_selected_paths(
    action: TypedAction,
    *,
    repo_root: Path,
    selected_paths: list[str],
    result_builder: ResultBuilder,
) -> ActionResult | None:
    stage_code, _, stage_error = run_git_capture(
        ["add", "-A", "--", *selected_paths],
        repo_root=repo_root,
    )
    if stage_code == 0:
        return None
    guidance = (
        _git_index_failure_guidance()
        if _git_index_write_blocked(stage_error)
        else "Repair the git index error and rerun `vcs.stage`."
    )
    return result_builder(
        action_id=action.action_id,
        ok=False,
        status=ActionOutcome.FAIL,
        reason=_git_index_failure_reason(
            stage_error,
            default="git_add_failed",
        ),
        operator_guidance=guidance,
        warnings=((stage_error,) if stage_error else ()),
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
        repo_root=repo_root
    )
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

    tree_hash, tree_error = index_tree_hash_result(repo_root)
    if not tree_hash:
        guidance = (
            _git_index_failure_guidance()
            if _git_index_write_blocked(tree_error)
            else "Repair the git index state and rerun `vcs.stage`."
        )
        return result_builder(
            action_id=action.action_id,
            ok=False,
            status=ActionOutcome.FAIL,
            reason=_git_index_failure_reason(
                tree_error,
                default="staged_tree_hash_unavailable",
            ),
            operator_guidance=guidance,
            warnings=((tree_error,) if tree_error else ()),
        )

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
