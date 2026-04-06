"""Git/worktree helpers for push-state detection."""

from __future__ import annotations

import subprocess
from pathlib import Path


def git_stdout(repo_root: Path, *cmd: str) -> str:
    """Run a git command and return rstrip'd stdout, or empty on failure."""
    try:
        result = subprocess.run(
            ["git", *cmd],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.rstrip() if result.returncode == 0 else ""


def worktree_change_counts(
    repo_root: Path,
    *,
    exclude_paths: tuple[str, ...] = (),
) -> tuple[int, int]:
    """Return dirty and untracked path counts, excluding advisory paths."""
    status_raw = git_stdout(repo_root, "status", "--porcelain", "--untracked-files=all")
    if not status_raw:
        return 0, 0
    exclude_set = set(exclude_paths)
    dirty_paths: set[str] = set()
    untracked_paths: set[str] = set()
    for line in status_raw.splitlines():
        if not line:
            continue
        status = line[:2].strip()
        path = line[3:]
        if "->" in path:
            path = path.split("->")[-1].strip()
        path = path.strip()
        if not path or path in exclude_set:
            continue
        dirty_paths.add(path)
        if status == "??":
            untracked_paths.add(path)
    return len(dirty_paths), len(untracked_paths)
