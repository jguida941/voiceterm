"""Auto-commit preflight-generated changes to break the push dirty-tree loop."""

from __future__ import annotations

from pathlib import Path

from ...collect import collect_git_status
from ...config import REPO_ROOT
from ...runtime.vcs import run_git_capture


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
    if state.errors:
        return
    try:
        git = collect_git_status()
    except (OSError, FileNotFoundError):
        return
    changes = git.get("changes", [])
    exclusions = (
        *policy.checkpoint.compatibility_projection_paths,
        *policy.checkpoint.advisory_context_paths,
    )
    dirty = _dirty_paths(changes, exclude_paths=exclusions)
    if not dirty:
        return
    try:
        run_git_capture(["git", "add"] + dirty, repo_root=repo_root)
        run_git_capture(
            ["git", "commit", "-m", "chore(push): auto-commit preflight-generated changes"],
            repo_root=repo_root,
        )
    except (OSError, ValueError):
        state.errors.append(
            f"Preflight generated {len(dirty)} dirty path(s) but auto-commit failed: "
            + ", ".join(dirty[:5])
        )


def _dirty_paths(
    changes: list[dict[str, object]],
    *,
    exclude_paths: tuple[str, ...] = (),
) -> list[str]:
    exclude_set = set(exclude_paths)
    return [
        str(c.get("path", "")).strip()
        for c in changes
        if str(c.get("path", "")).strip()
        and str(c.get("path", "")).strip() not in exclude_set
    ]
