"""Push-state authorization helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ..repo_packs import active_path_config
from ..review_channel.remote_commit_pipeline_artifact import (
    load_remote_commit_pipeline_contract,
)
from .push_policy import PushCheckpointPolicy


def current_approved_target_identity(*, repo_root: Path) -> str:
    """Return the current approved publish identity from the pipeline artifact."""
    pipeline = load_remote_commit_pipeline_contract(
        output_root=repo_root / active_path_config().review_status_dir_rel
    )
    if pipeline is None:
        return ""
    return str(pipeline.approved_target_identity or "").strip()


def current_push_authorization_state(
    *,
    repo_root: Path,
    current_head_commit: str,
    current_approved_target_identity: str,
) -> tuple[str, str, str, str, str, bool, bool, bool]:
    """Return the current push-authorization receipt summary."""
    pipeline = load_remote_commit_pipeline_contract(
        output_root=repo_root / active_path_config().review_status_dir_rel
    )
    authorization = None if pipeline is None else getattr(pipeline, "push_authorization", None)
    if authorization is None:
        return ("", "", "", "", "", False, False, False)
    authorized_head_commit = str(authorization.authorized_head_sha or "").strip()
    approved_target_identity = str(
        authorization.approved_target_identity or ""
    ).strip()
    matches_current_head = bool(
        current_head_commit
        and authorized_head_commit
        and current_head_commit == authorized_head_commit
    )
    matches_current_approved_target = bool(
        (
            not current_approved_target_identity
            and not approved_target_identity
        )
        or (
            current_approved_target_identity
            and approved_target_identity
            and current_approved_target_identity == approved_target_identity
        )
    )
    valid = bool(
        authorization.guard_status == "pass"
        and matches_current_head
        and matches_current_approved_target
        and not is_expired(authorization.expires_at_utc)
    )
    return (
        str(authorization.authorization_id or "").strip(),
        str(authorization.approval_mode or "").strip(),
        authorized_head_commit,
        str(authorization.expires_at_utc or "").strip(),
        approved_target_identity,
        matches_current_head,
        matches_current_approved_target,
        valid,
    )


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
