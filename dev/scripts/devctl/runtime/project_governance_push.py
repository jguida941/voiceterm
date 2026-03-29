"""Push-governance records for the ProjectGovernance contract."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping

from .value_coercion import coerce_bool, coerce_int, coerce_string


@dataclass(frozen=True, slots=True)
class PushEnforcement:
    """Repo-owned push/checkpoint posture for the current worktree."""

    default_remote: str = "origin"
    development_branch: str = "main"
    release_branch: str = "main"
    pre_push_hook_path: str = ""
    pre_push_hook_installed: bool = False
    raw_git_push_guarded: bool = False
    upstream_ref: str = ""
    ahead_of_upstream_commits: int | None = None
    dirty_path_count: int = 0
    untracked_path_count: int = 0
    max_dirty_paths_before_checkpoint: int = 12
    max_untracked_paths_before_checkpoint: int = 6
    checkpoint_required: bool = False
    safe_to_continue_editing: bool = True
    checkpoint_reason: str = "clean_worktree"
    worktree_dirty: bool = False
    worktree_clean: bool = True
    recommended_action: str = "use_devctl_push"
    latest_push_report_path: str = ""
    latest_push_report_status: str = ""
    latest_push_report_reason: str = ""
    latest_push_report_published_remote: bool = False
    latest_push_report_post_push_green: bool = False


def push_enforcement_from_mapping(
    payload: Mapping[str, object],
) -> PushEnforcement:
    """Parse PushEnforcement from a JSON-like mapping."""
    ahead_raw = payload.get("ahead_of_upstream_commits")
    ahead = coerce_int(ahead_raw) if ahead_raw is not None else None
    worktree_dirty = coerce_bool(payload.get("worktree_dirty"))
    worktree_clean_raw = payload.get("worktree_clean")
    if worktree_clean_raw is None:
        legacy_push_ready = payload.get("push_ready")
        if legacy_push_ready is not None:
            worktree_clean = coerce_bool(legacy_push_ready)
        else:
            worktree_clean = not worktree_dirty
    else:
        worktree_clean = coerce_bool(worktree_clean_raw)
    return PushEnforcement(
        default_remote=coerce_string(payload.get("default_remote")) or "origin",
        development_branch=coerce_string(payload.get("development_branch"))
        or "main",
        release_branch=coerce_string(payload.get("release_branch")) or "main",
        pre_push_hook_path=coerce_string(payload.get("pre_push_hook_path")),
        pre_push_hook_installed=coerce_bool(payload.get("pre_push_hook_installed")),
        raw_git_push_guarded=coerce_bool(payload.get("raw_git_push_guarded")),
        upstream_ref=coerce_string(payload.get("upstream_ref")),
        ahead_of_upstream_commits=ahead,
        dirty_path_count=coerce_int(payload.get("dirty_path_count")),
        untracked_path_count=coerce_int(payload.get("untracked_path_count")),
        max_dirty_paths_before_checkpoint=(
            coerce_int(payload.get("max_dirty_paths_before_checkpoint")) or 12
        ),
        max_untracked_paths_before_checkpoint=(
            coerce_int(payload.get("max_untracked_paths_before_checkpoint")) or 6
        ),
        checkpoint_required=coerce_bool(payload.get("checkpoint_required")),
        safe_to_continue_editing=(
            True
            if payload.get("safe_to_continue_editing") is None
            else coerce_bool(payload.get("safe_to_continue_editing"))
        ),
        checkpoint_reason=coerce_string(payload.get("checkpoint_reason"))
        or "clean_worktree",
        worktree_dirty=worktree_dirty,
        worktree_clean=worktree_clean,
        recommended_action=coerce_string(payload.get("recommended_action"))
        or "use_devctl_push",
        latest_push_report_path=coerce_string(payload.get("latest_push_report_path")),
        latest_push_report_status=coerce_string(payload.get("latest_push_report_status")),
        latest_push_report_reason=coerce_string(payload.get("latest_push_report_reason")),
        latest_push_report_published_remote=coerce_bool(
            payload.get("latest_push_report_published_remote")
        ),
        latest_push_report_post_push_green=coerce_bool(
            payload.get("latest_push_report_post_push_green")
        ),
    )
