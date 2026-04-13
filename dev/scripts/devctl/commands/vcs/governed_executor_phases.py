"""Stage execution helpers for the governed VCS pipeline."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from ...runtime import ActionResult, TypedAction
from ...runtime.action_contracts import ActionOutcome
from ...runtime.remote_commit_pipeline_models import RemoteCommitPipelineContract
from ...runtime.startup_receipt import load_startup_receipt
from ...runtime.review_snapshot_refresh import refresh_and_stage_review_snapshot
from ...runtime.vcs import run_git_capture
from .governed_executor_actions import (
    _ACTIVE_PIPELINE_STATES,
    build_staged_pipeline,
)
from .governed_executor_field_access import (
    bool_field,
    field,
    string_field,
)
from .governed_executor_git import (
    current_branch,
    dirty_paths,
    index_tree_hash_result,
    normalize_paths,
    staged_diff_summary,
    staged_paths,
)

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


def _refresh_snapshot_staging(*, repo_root: Path) -> tuple[list[str], list[str]]:
    """Return refresh warnings plus the staged-path view after refresh."""
    return (
        refresh_and_stage_review_snapshot(repo_root=repo_root),
        staged_paths(repo_root),
    )


def _check_stage_preconditions(
    action: TypedAction,
    *,
    repo_root: Path,
    startup_context: Any,
    load_pipeline: Callable[[], RemoteCommitPipelineContract],
    pipeline_artifact_relpath: str,
    result_builder: ResultBuilder,
) -> ActionResult | None:
    """Return an early-exit ActionResult if stage preconditions fail, else None."""
    reviewer_gate = field(startup_context, "reviewer_gate")
    checkpoint_stage_allowed = (
        string_field(field(startup_context, "push_decision"), "action")
        == "await_checkpoint"
        and bool_field(reviewer_gate, "checkpoint_permitted", default=True)
    )
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
    attention_revision_block = _attention_revision_block(
        action=action,
        repo_root=repo_root,
        startup_context=startup_context,
        result_builder=result_builder,
    )
    if attention_revision_block is not None:
        return attention_revision_block
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
    return None


def _attention_revision_block(
    *,
    action: TypedAction,
    repo_root: Path,
    startup_context: Any,
    result_builder: ResultBuilder,
) -> ActionResult | None:
    packet_inbox = field(startup_context, "packet_inbox")
    current_attention_revision = string_field(packet_inbox, "attention_revision")
    if not current_attention_revision:
        return None
    agents = field(packet_inbox, "agents")
    if not isinstance(agents, (tuple, list)):
        return None
    target_agent = _startup_context_active_implementation_owner(startup_context)
    if not _target_agent_has_actionable_packet_attention(
        agents=agents,
        target_agent=target_agent,
    ):
        return None
    receipt = load_startup_receipt(repo_root=repo_root)
    if receipt is not None and receipt.attention_revision == current_attention_revision:
        return None
    return result_builder(
        action_id=action.action_id,
        ok=False,
        status=ActionOutcome.FAIL,
        reason="attention_revision_stale",
        operator_guidance=(
            "Typed packet attention changed since the last startup receipt. "
            "Rerun `python3 dev/scripts/devctl.py startup-context --format summary`, "
            "refresh `session-resume`, then acknowledge the new typed inbox state "
            "before staging more work."
        ),
    )


def _has_actionable_packet_attention(row: object) -> bool:
    pending_actionable_total = 0
    if isinstance(row, dict):
        pending_actionable_total = int(row.get("pending_actionable_total") or 0)
        wake_reason = str(row.get("wake_reason") or "").strip()
    else:
        pending_actionable_total = int(getattr(row, "pending_actionable_total", 0) or 0)
        wake_reason = str(getattr(row, "wake_reason", "") or "").strip()
    if pending_actionable_total > 0:
        return True
    return wake_reason == "finding_pending"


def _target_agent_has_actionable_packet_attention(
    *,
    agents: tuple[object, ...] | list[object],
    target_agent: str,
) -> bool:
    if target_agent:
        normalized_target = target_agent.strip().lower()
        for row in agents:
            if string_field(row, "agent").lower() != normalized_target:
                continue
            return _has_actionable_packet_attention(row)
        return False
    return any(_has_actionable_packet_attention(row) for row in agents)


def _startup_context_active_implementation_owner(startup_context: object) -> str:
    work_intake = field(startup_context, "work_intake")
    coordination = field(work_intake, "coordination")
    return string_field(coordination, "active_implementation_owner").lower()


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
