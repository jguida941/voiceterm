"""Push-state authorization helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ..review_channel.remote_commit_pipeline_artifact import (
    load_canonical_remote_commit_pipeline_contract,
)
from ..runtime.review_snapshot_refresh import receipt_commit_ancestor_shas
from .push_policy import PushCheckpointPolicy


def current_approved_target_identity(*, repo_root: Path) -> str:
    """Return the current approved publish identity from the pipeline artifact."""
    pipeline = load_canonical_remote_commit_pipeline_contract(repo_root=repo_root)
    return approved_target_identity_from_pipeline(pipeline)


def approved_target_identity_from_pipeline(pipeline: object) -> str:
    """Return the approved publish identity carried by one pipeline object."""
    if pipeline is None:
        return ""
    return str(getattr(pipeline, "approved_target_identity", "") or "").strip()


def approved_worktree_identity_from_pipeline(pipeline: object) -> str:
    """Return the approved worktree identity carried by one pipeline object."""
    if pipeline is None:
        return ""
    return str(getattr(pipeline, "worktree_identity", "") or "").strip()


def current_push_authorization_state(
    *,
    repo_root: Path,
    current_head_commit: str,
    current_approved_target_identity: str,
    current_worktree_identity: str,
) -> tuple[str, str, str, str, str, str, bool, bool, bool, bool]:
    """Return the current push-authorization receipt summary."""
    pipeline = load_canonical_remote_commit_pipeline_contract(repo_root=repo_root)
    return push_authorization_state_from_pipeline(
        pipeline=pipeline,
        current_head_commit=current_head_commit,
        current_approved_target_identity=current_approved_target_identity,
        current_worktree_identity=current_worktree_identity,
        managed_receipt_ancestor_commits=receipt_commit_ancestor_shas(
            repo_root=repo_root,
            current_head=current_head_commit,
            governance=None,
        ),
    )


def push_authorization_state_from_pipeline(
    *,
    pipeline: object,
    current_head_commit: str,
    current_approved_target_identity: str,
    current_worktree_identity: str,
    managed_receipt_ancestor_commits: tuple[str, ...] = (),
) -> tuple[str, str, str, str, str, str, bool, bool, bool, bool]:
    """Return the current push-authorization summary for one pipeline object."""
    authorization = (
        None if pipeline is None else getattr(pipeline, "push_authorization", None)
    )
    if authorization is None:
        return ("", "", "", "", "", "", False, False, False, False)
    authorized_head_commit = str(authorization.authorized_head_sha or "").strip()
    approved_target_identity = str(authorization.approved_target_identity or "").strip()
    approved_worktree_identity = str(authorization.worktree_identity or "").strip()
    matches_current_head = bool(
        current_head_commit
        and authorized_head_commit
        and (
            _same_commit(current_head_commit, authorized_head_commit)
            or any(
                _same_commit(ancestor, authorized_head_commit)
                for ancestor in managed_receipt_ancestor_commits
            )
        )
    )
    matches_current_approved_target = bool(
        (not current_approved_target_identity and not approved_target_identity)
        or (
            current_approved_target_identity
            and approved_target_identity
            and current_approved_target_identity == approved_target_identity
        )
    )
    matches_current_worktree = bool(
        not approved_worktree_identity
        or (
            current_worktree_identity
            and approved_worktree_identity
            and current_worktree_identity == approved_worktree_identity
        )
    )
    valid = bool(
        authorization.guard_status == "pass"
        and matches_current_head
        and matches_current_approved_target
        and matches_current_worktree
        and not is_expired(authorization.expires_at_utc)
    )
    return (
        str(authorization.authorization_id or "").strip(),
        str(authorization.approval_mode or "").strip(),
        authorized_head_commit,
        str(authorization.expires_at_utc or "").strip(),
        approved_target_identity,
        approved_worktree_identity,
        matches_current_head,
        matches_current_approved_target,
        matches_current_worktree,
        valid,
    )


def _same_commit(left: str, right: str) -> bool:
    left = str(left or "").strip()
    right = str(right or "").strip()
    return bool(left and right and (left.startswith(right) or right.startswith(left)))


def checkpoint_reason(
    *,
    dirty_path_count: int,
    untracked_path_count: int,
    policy: PushCheckpointPolicy,
) -> str:
    """Return the checkpoint-budget reason for the current worktree state."""
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


def is_expired(timestamp: str) -> bool:
    """Return whether one UTC timestamp has expired."""
    if not timestamp:
        return False
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed <= datetime.now(timezone.utc)
