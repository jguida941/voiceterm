"""Git tracking helpers for schema fixture guard files."""

from __future__ import annotations

import subprocess
from pathlib import Path


def inside_git_worktree(repo_root: Path) -> bool:
    completed = _run_git(repo_root, "rev-parse", "--is-inside-work-tree")
    return completed.returncode == 0 and completed.stdout.strip() == "true"


def git_path_tracked(*, repo_root: Path, path: Path) -> bool:
    try:
        relative = path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        relative = path.as_posix()
    completed = _run_git(repo_root, "ls-files", "--error-unmatch", "--", relative)
    return completed.returncode == 0


def _run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ("git", "-C", str(repo_root), *args),
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return subprocess.CompletedProcess(
            args=("git", "-C", str(repo_root), *args),
            returncode=1,
            stdout="",
            stderr="",
        )
