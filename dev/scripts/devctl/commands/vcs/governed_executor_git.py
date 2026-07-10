"""Git-querying helpers for the governed remote commit/push pipeline."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from ...runtime.dirty_path_filter import (
    ignored_dirty_path_prefixes,
    path_is_ignored_for_dirty_paths,
)
from ...runtime.vcs import run_git_capture
from .governed_executor_field_access import string_value


def dirty_paths(repo_root: Path) -> list[str]:
    """Return worktree-dirty paths, excluding governance/review artifacts."""
    code, output, error = run_git_capture(
        ["status", "--porcelain", "--untracked-files=all"],
        repo_root=repo_root,
    )
    if code != 0:
        raise ValueError(error or "git status failed")
    result: list[str] = []
    ignored_prefixes = ignored_dirty_path_prefixes()
    for line in output.splitlines():
        if not line:
            continue
        parts = line.split(maxsplit=1)
        path = parts[1] if len(parts) == 2 else ""
        if "->" in path:
            path = path.split("->")[-1].strip()
        normalized = path.strip()
        if not normalized or path_is_ignored_for_dirty_paths(
            normalized,
            ignored_prefixes,
        ):
            continue
        result.append(normalized)
    return result


def unstaged_paths(repo_root: Path) -> list[str]:
    """Return dirty paths not fully represented in the git index."""
    code, output, error = run_git_capture(
        ["status", "--porcelain", "--untracked-files=all"],
        repo_root=repo_root,
    )
    if code != 0:
        raise ValueError(error or "git status failed")
    result: list[str] = []
    ignored_prefixes = ignored_dirty_path_prefixes()
    for line in output.splitlines():
        if not line:
            continue
        status = line[:2]
        if status[1:2] == " ":
            continue
        path = line[3:].strip()
        if "->" in path:
            path = path.split("->")[-1].strip()
        if not path or path_is_ignored_for_dirty_paths(path, ignored_prefixes):
            continue
        result.append(path)
    return result


def staged_paths(repo_root: Path) -> list[str]:
    """Return paths currently staged in the git index."""
    code, output, error = run_git_capture(
        ["diff", "--cached", "--name-only", "--diff-filter=ACDMRTUXB"],
        repo_root=repo_root,
    )
    if code != 0:
        raise ValueError(error or "git diff --cached failed")
    return [line.strip() for line in output.splitlines() if line.strip()]


def staged_diff_summary(repo_root: Path) -> str:
    """Return a one-line --stat summary for the staged snapshot."""
    code, output, error = run_git_capture(
        ["diff", "--cached", "--stat"],
        repo_root=repo_root,
    )
    if code != 0:
        raise ValueError(error or "git diff --cached --stat failed")
    return output


def index_tree_hash_result(repo_root: Path) -> tuple[str, str]:
    """Return the staged-tree hash plus the git error when write-tree fails."""
    code, output, error = run_git_capture(["write-tree"], repo_root=repo_root)
    if code == 0:
        return output, ""
    return "", error or "git write-tree failed"


def index_tree_hash(repo_root: Path) -> str:
    """Return the SHA for the current staged tree, or empty on failure."""
    output, _ = index_tree_hash_result(repo_root)
    return output


def current_branch(repo_root: Path) -> str:
    """Return the current branch name, or empty on detached HEAD."""
    code, output, _ = run_git_capture(
        ["rev-parse", "--abbrev-ref", "HEAD"],
        repo_root=repo_root,
    )
    return output if code == 0 else ""


def head_commit(repo_root: Path) -> str:
    """Return the current HEAD SHA, or empty on failure."""
    code, output, _ = run_git_capture(["rev-parse", "HEAD"], repo_root=repo_root)
    return output if code == 0 else ""


def pipeline_is_stale_for_current_repo(pipeline: object, *, repo_root: Path) -> bool:
    """Return True when a stored pipeline no longer matches the current repo state."""
    pipeline_id = string_value(getattr(pipeline, "pipeline_id", ""))
    if not pipeline_id:
        return False

    pipeline_branch = string_value(getattr(pipeline, "branch", ""))
    active_branch = current_branch(repo_root)
    if pipeline_branch and active_branch and pipeline_branch != active_branch:
        return True

    pipeline_commit_sha = string_value(getattr(pipeline, "commit_sha", ""))
    active_head = head_commit(repo_root)
    return bool(pipeline_commit_sha and active_head and pipeline_commit_sha != active_head)


def normalize_paths(value: object) -> list[str]:
    """Extract a list of non-empty string paths from a sequence-typed value."""
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    paths: list[str] = []
    for item in value:
        text = string_value(item)
        if text:
            paths.append(text)
    return paths


def repo_relpath(path: Path, *, repo_root: Path) -> str:
    """Return *path* relative to *repo_root*, falling back to absolute."""
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path.resolve())
