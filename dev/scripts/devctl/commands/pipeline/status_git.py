"""Git probes for read-only commit-pipeline status."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def git_reconcile_state(repo_root: Path) -> dict[str, Any]:
    """Return cheap git state used to disambiguate interrupted VCS commands."""
    branch = _git_stdout(repo_root, ("git", "branch", "--show-current"))
    upstream = _git_stdout(
        repo_root,
        ("git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"),
    )
    ahead: int | None = None
    behind: int | None = None
    if upstream:
        counts = _git_stdout(
            repo_root,
            ("git", "rev-list", "--left-right", "--count", f"HEAD...{upstream}"),
        )
        parts = counts.split()
        if len(parts) == 2:
            ahead = _parse_int(parts[0])
            behind = _parse_int(parts[1])
    status = _git_stdout(repo_root, ("git", "status", "--porcelain"))
    return {
        "current_branch": branch or "",
        "upstream_ref": upstream or "",
        "ahead_of_upstream_commits": ahead,
        "behind_upstream_commits": behind,
        "worktree_clean": status == "" if status is not None else None,
    }


def _git_stdout(repo_root: Path, cmd: tuple[str, ...]) -> str | None:
    try:
        result = subprocess.run(
            list(cmd),
            cwd=str(repo_root),
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def _parse_int(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
