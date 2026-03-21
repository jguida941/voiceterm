"""Runtime push/checkpoint state detection for startup surfaces."""

from __future__ import annotations

import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from ..config import REPO_ROOT
from .push_policy import PushCheckpointPolicy, PushPolicy


@dataclass(frozen=True, slots=True)
class PushEnforcementSnapshot:
    """Typed snapshot of the repo-owned push/checkpoint state."""

    default_remote: str
    development_branch: str
    release_branch: str
    pre_push_hook_path: str
    pre_push_hook_installed: bool
    raw_git_push_guarded: bool
    upstream_ref: str
    ahead_of_upstream_commits: int | None
    dirty_path_count: int
    untracked_path_count: int
    max_dirty_paths_before_checkpoint: int
    max_untracked_paths_before_checkpoint: int
    checkpoint_required: bool
    safe_to_continue_editing: bool
    checkpoint_reason: str
    worktree_dirty: bool
    push_ready: bool
    recommended_action: str


def detect_push_enforcement_state(
    policy: PushPolicy,
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, object]:
    """Return repo-owned push/checkpoint state for startup/runtime surfaces."""
    hook_path_text = _git_stdout(repo_root, "rev-parse", "--git-path", "hooks/pre-push")
    hook_path = (
        Path(hook_path_text)
        if hook_path_text
        else (repo_root / ".git" / "hooks" / "pre-push")
    )
    hook_installed = hook_path.is_file()
    raw_guarded = hook_installed and os.access(hook_path, os.X_OK)
    upstream_ref = _git_stdout(
        repo_root,
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{u}",
    )
    ahead: int | None = None
    if upstream_ref:
        ahead_text = _git_stdout(repo_root, "rev-list", "--count", f"{upstream_ref}..HEAD")
        if ahead_text.isdigit():
            ahead = int(ahead_text)
    dirty_path_count, untracked_path_count = _worktree_change_counts(repo_root)
    worktree_dirty = dirty_path_count > 0
    checkpoint_required = (
        dirty_path_count >= policy.checkpoint.max_dirty_paths_before_checkpoint
        or untracked_path_count >= policy.checkpoint.max_untracked_paths_before_checkpoint
    )
    safe_to_continue_editing = not checkpoint_required
    push_ready = not worktree_dirty
    checkpoint_reason = "clean_worktree"
    if checkpoint_required:
        recommended_action = "checkpoint_before_continue"
        checkpoint_reason = _checkpoint_reason(
            dirty_path_count=dirty_path_count,
            untracked_path_count=untracked_path_count,
            policy=policy.checkpoint,
        )
    elif worktree_dirty:
        recommended_action = "commit_before_push"
        checkpoint_reason = "within_dirty_budget"
    elif ahead == 0 and upstream_ref:
        recommended_action = "no_push_needed"
    else:
        recommended_action = "use_devctl_push"
    snapshot = PushEnforcementSnapshot(
        default_remote=policy.default_remote,
        development_branch=policy.development_branch,
        release_branch=policy.release_branch,
        pre_push_hook_path=str(hook_path),
        pre_push_hook_installed=hook_installed,
        raw_git_push_guarded=raw_guarded,
        upstream_ref=upstream_ref,
        ahead_of_upstream_commits=ahead,
        dirty_path_count=dirty_path_count,
        untracked_path_count=untracked_path_count,
        max_dirty_paths_before_checkpoint=(
            policy.checkpoint.max_dirty_paths_before_checkpoint
        ),
        max_untracked_paths_before_checkpoint=(
            policy.checkpoint.max_untracked_paths_before_checkpoint
        ),
        checkpoint_required=checkpoint_required,
        safe_to_continue_editing=safe_to_continue_editing,
        checkpoint_reason=checkpoint_reason,
        worktree_dirty=worktree_dirty,
        push_ready=push_ready,
        recommended_action=recommended_action,
    )
    return asdict(snapshot)


def _git_stdout(repo_root: Path, *cmd: str) -> str:
    """Run a git command and return stripped stdout, or empty on failure."""
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
    return result.stdout.strip() if result.returncode == 0 else ""


def _worktree_change_counts(repo_root: Path) -> tuple[int, int]:
    status_raw = _git_stdout(repo_root, "status", "--porcelain", "--untracked-files=all")
    if not status_raw:
        return 0, 0
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
        if not path:
            continue
        dirty_paths.add(path)
        if status == "??":
            untracked_paths.add(path)
    return len(dirty_paths), len(untracked_paths)


def _checkpoint_reason(
    *,
    dirty_path_count: int,
    untracked_path_count: int,
    policy: PushCheckpointPolicy,
) -> str:
    if (
        dirty_path_count >= policy.max_dirty_paths_before_checkpoint
        and untracked_path_count >= policy.max_untracked_paths_before_checkpoint
    ):
        return "dirty_and_untracked_budget_exceeded"
    if dirty_path_count >= policy.max_dirty_paths_before_checkpoint:
        return "dirty_path_budget_exceeded"
    if untracked_path_count >= policy.max_untracked_paths_before_checkpoint:
        return "untracked_path_budget_exceeded"
    return "within_dirty_budget"
