"""Git index operations for the governed stage phase."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from ...runtime import ActionResult, TypedAction
from ...runtime.action_contracts import ActionOutcome
from ...runtime.vcs import run_git_capture
from .governed_executor_git import index_tree_hash_result
from .governed_executor_index_lock import (
    git_index_busy_guidance,
    git_index_failure_guidance,
    git_index_failure_reason,
    git_index_result_kwargs,
    git_index_write_blocked,
)

ResultBuilder = Callable[..., ActionResult]


def stage_selected_paths(
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
    staged_deletion_error = _retry_stage_without_already_staged_deletions(
        repo_root=repo_root,
        selected_paths=selected_paths,
        stage_error=stage_error,
    )
    if staged_deletion_error == "":
        return None
    if staged_deletion_error:
        stage_error = staged_deletion_error
    reason = git_index_failure_reason(stage_error, default="git_add_failed")
    return result_builder(
        action_id=action.action_id,
        ok=False,
        status=ActionOutcome.FAIL,
        reason=reason,
        operator_guidance=_index_failure_guidance(
            error=stage_error,
            reason=reason,
            fallback="Repair the git index error and rerun `vcs.stage`.",
        ),
        warnings=((stage_error,) if stage_error else ()),
        **git_index_result_kwargs(
            error=stage_error,
            reason=reason,
            default_reason="git_add_failed",
        ),
    )


def _retry_stage_without_already_staged_deletions(
    *,
    repo_root: Path,
    selected_paths: list[str],
    stage_error: str,
) -> str | None:
    if "pathspec" not in stage_error or "did not match any files" not in stage_error:
        return None
    staged_deletions = _staged_deletion_paths(
        repo_root=repo_root,
        selected_paths=selected_paths,
    )
    if not staged_deletions:
        return None
    retry_paths: list[str] = []
    for path in selected_paths:
        if path in staged_deletions:
            continue
        if (repo_root / path).exists():
            retry_paths.append(path)
            continue
        return None
    if not retry_paths:
        return ""
    retry_code, _, retry_error = run_git_capture(
        ["add", "-A", "--", *retry_paths],
        repo_root=repo_root,
    )
    return "" if retry_code == 0 else retry_error or stage_error


def _staged_deletion_paths(*, repo_root: Path, selected_paths: list[str]) -> set[str]:
    code, output, _ = run_git_capture(
        ["diff", "--cached", "--name-only", "--diff-filter=D", "--", *selected_paths],
        repo_root=repo_root,
    )
    if code != 0:
        return set()
    return {line.strip() for line in output.splitlines() if line.strip()}


def staged_tree_hash_or_failure(
    action: TypedAction,
    *,
    repo_root: Path,
    result_builder: ResultBuilder,
) -> tuple[str, ActionResult | None]:
    tree_hash, tree_error = index_tree_hash_result(repo_root)
    if tree_hash:
        return tree_hash, None
    reason = git_index_failure_reason(
        tree_error,
        default="staged_tree_hash_unavailable",
    )
    return "", result_builder(
        action_id=action.action_id,
        ok=False,
        status=ActionOutcome.FAIL,
        reason=reason,
        operator_guidance=_index_failure_guidance(
            error=tree_error,
            reason=reason,
            fallback="Repair the git index state and rerun `vcs.stage`.",
        ),
        warnings=((tree_error,) if tree_error else ()),
        **git_index_result_kwargs(
            error=tree_error,
            reason=reason,
            default_reason="staged_tree_hash_unavailable",
        ),
    )


def _index_failure_guidance(*, error: str, reason: str, fallback: str) -> str:
    if git_index_write_blocked(error):
        return git_index_failure_guidance()
    if reason == "git_index_lock_busy":
        return git_index_busy_guidance()
    return fallback
