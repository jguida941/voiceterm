"""Git/worktree helpers for push-state detection."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
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


@dataclass(frozen=True, slots=True)
class WorktreeChangeCounts:
    """Structured git-status counts for startup/push enforcement."""

    dirty_path_count: int = 0
    untracked_path_count: int = 0
    staged_path_count: int = 0
    unstaged_path_count: int = 0
    excluded_path_count: int = 0
    excluded_paths: tuple[str, ...] = ()


def parse_worktree_change_summary(
    status_raw: str,
    *,
    exclude_paths: tuple[str, ...] = (),
) -> WorktreeChangeCounts:
    """Parse ``git status --porcelain`` output into structured counts."""
    if not status_raw:
        return WorktreeChangeCounts()
    exclude_set = set(exclude_paths)
    dirty_paths: set[str] = set()
    untracked_paths: set[str] = set()
    staged_paths: set[str] = set()
    unstaged_paths: set[str] = set()
    excluded_dirty_paths: set[str] = set()
    for line in status_raw.splitlines():
        if not line:
            continue
        index_status = line[0]
        worktree_status = line[1]
        status = line[:2].strip()
        path = line[3:]
        if "->" in path:
            path = path.split("->")[-1].strip()
        path = path.strip()
        if not path or path in exclude_set:
            if path:
                excluded_dirty_paths.add(path)
            continue
        dirty_paths.add(path)
        if status == "??":
            untracked_paths.add(path)
            continue
        if index_status not in {" ", "?"}:
            staged_paths.add(path)
        if worktree_status not in {" ", "?"}:
            unstaged_paths.add(path)
    return WorktreeChangeCounts(
        dirty_path_count=len(dirty_paths),
        untracked_path_count=len(untracked_paths),
        staged_path_count=len(staged_paths),
        unstaged_path_count=len(unstaged_paths),
        excluded_path_count=len(excluded_dirty_paths),
        excluded_paths=tuple(sorted(excluded_dirty_paths)),
    )


def worktree_change_summary(
    repo_root: Path,
    *,
    exclude_paths: tuple[str, ...] = (),
) -> WorktreeChangeCounts:
    """Return structured staged/unstaged/untracked counts for the worktree."""
    status_raw = git_stdout(repo_root, "status", "--porcelain", "--untracked-files=all")
    return parse_worktree_change_summary(
        status_raw,
        exclude_paths=exclude_paths,
    )


def worktree_change_counts(
    repo_root: Path,
    *,
    exclude_paths: tuple[str, ...] = (),
) -> tuple[int, int]:
    """Return dirty and untracked path counts, excluding advisory paths."""
    summary = worktree_change_summary(repo_root, exclude_paths=exclude_paths)
    return summary.dirty_path_count, summary.untracked_path_count
