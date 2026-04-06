"""Git path resolution for review-candidate builders."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .reviewer_head_tracking import current_head_sha


def resolve_changed_paths(
    *,
    repo_root: Path,
    base_sha: str,
) -> tuple[str, tuple[str, ...]]:
    """Return (artifact_kind, changed_paths) from worktree or commit range."""
    worktree_paths = git_worktree_paths(repo_root)
    if worktree_paths:
        return "dirty_tree", worktree_paths
    head_sha = current_head_sha(repo_root)
    if base_sha and head_sha and base_sha != head_sha:
        commit_paths = git_commit_range_paths(repo_root, base_sha, head_sha)
        if commit_paths:
            return "commit_range", commit_paths
    return "", ()


def git_worktree_paths(repo_root: Path) -> tuple[str, ...]:
    """Return changed + untracked paths in the worktree."""
    try:
        tracked = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        ).stdout.splitlines()
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        ).stdout.splitlines()
    except (OSError, subprocess.TimeoutExpired):
        return ()

    paths: list[str] = []
    for raw_path in (*tracked, *untracked):
        path = raw_path.strip()
        if path and path not in paths:
            paths.append(path)
    return tuple(paths)


def git_commit_range_paths(
    repo_root: Path,
    base_sha: str,
    head_sha: str,
) -> tuple[str, ...]:
    """Return paths changed between base_sha and head_sha."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base_sha}..{head_sha}"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ()
    return tuple(path.strip() for path in result.stdout.splitlines() if path.strip())
