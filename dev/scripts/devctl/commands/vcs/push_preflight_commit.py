"""Auto-commit preflight-generated changes to break the push dirty-tree loop."""

from __future__ import annotations

from pathlib import Path

from ...collect import collect_git_status
from ...config import REPO_ROOT
from ...runtime.vcs import run_git_capture
from .push_worktree_changes import blocking_dirty_paths


def auto_commit_preflight_generated_changes(
    state,
    policy,
    *,
    repo_root: Path = REPO_ROOT,
) -> None:
    """Auto-commit changes the preflight generated so the push doesn't loop.

    The preflight runs check-router which may trigger render-surfaces,
    code generation passes, or test updates. Those changes dirty the
    worktree, causing the push to fail its own clean-tree check on the
    next attempt — creating an infinite commit-push-fail loop.

    This function detects preflight-generated changes and auto-commits
    them with a machine-generated message so the push can proceed.
    """
    try:
        git = collect_git_status()
    except (OSError, FileNotFoundError):
        return
    changes = git.get("changes", [])
    exclusions = (
        *policy.checkpoint.compatibility_projection_paths,
        *policy.checkpoint.advisory_context_paths,
    )
    dirty = blocking_dirty_paths(changes, exclude_paths=exclusions)
    if not dirty:
        return
    add_code, _, add_error = run_git_capture(
        ["add", "--", *dirty],
        repo_root=repo_root,
    )
    if add_code != 0:
        state.errors.append(
            _auto_commit_failure_message(
                dirty=dirty,
                step="git add",
                error=add_error,
            )
        )
        return

    commit_code, _, commit_error = run_git_capture(
        ["commit", "-m", "chore(push): auto-commit preflight-generated changes"],
        repo_root=repo_root,
    )
    if commit_code != 0:
        state.errors.append(
            _auto_commit_failure_message(
                dirty=dirty,
                step="git commit",
                error=commit_error,
            )
        )


def _auto_commit_failure_message(
    *,
    dirty: list[str],
    step: str,
    error: str,
) -> str:
    paths = ", ".join(dirty[:5])
    detail = f": {error}" if error else ""
    return (
        f"Preflight generated {len(dirty)} dirty path(s) but {step} failed"
        f" for {paths}{detail}"
    )
