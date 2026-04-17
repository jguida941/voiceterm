"""Typed models for repo-owned push/checkpoint state."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PushEnforcementSnapshot:
    """Typed snapshot of the repo-owned push/checkpoint state."""

    current_branch: str
    current_head_commit: str
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
    staged_path_count: int
    unstaged_path_count: int
    max_dirty_paths_before_checkpoint: int
    max_untracked_paths_before_checkpoint: int
    checkpoint_required: bool
    safe_to_continue_editing: bool
    checkpoint_reason: str
    worktree_dirty: bool
    worktree_clean: bool
    recommended_action: str
    pending_publication_commits: int | None = None
    publication_backlog_state: str = "none"
    publication_backlog_summary: str = ""
    publication_backlog_recommended: bool = False
    publication_backlog_urgent: bool = False
    recommend_after_ahead_commits: int = 2
    urgent_after_ahead_commits: int = 5
    latest_push_report_path: str = ""
    latest_push_report_branch: str = ""
    latest_push_report_remote: str = ""
    latest_push_report_head_commit: str = ""
    latest_push_report_status: str = ""
    latest_push_report_reason: str = ""
    latest_push_report_published_remote: bool = False
    latest_push_report_post_push_green: bool = False
    current_worktree_identity: str = ""
    current_approved_target_identity: str = ""
    latest_push_report_approved_worktree_identity: str = ""
    latest_push_report_approved_target_identity: str = ""
    latest_push_report_matches_current_approved_target: bool = False
    latest_push_report_matches_current_worktree: bool = False
    latest_push_report_matches_current_branch: bool = False
    latest_push_report_matches_current_head: bool = False
    selected_push_report_source: str = ""
    selected_push_report_branch: str = ""
    selected_push_report_remote: str = ""
    selected_push_report_head_commit: str = ""
    selected_push_report_status: str = ""
    selected_push_report_reason: str = ""
    selected_push_report_published_remote: bool = False
    selected_push_report_post_push_green: bool = False
    selected_push_report_approved_worktree_identity: str = ""
    selected_push_report_approved_target_identity: str = ""
    selected_push_report_matches_current_approved_target: bool = False
    selected_push_report_matches_current_worktree: bool = False
    selected_push_report_matches_current_branch: bool = False
    selected_push_report_matches_current_head: bool = False
    current_push_authorization_id: str = ""
    current_push_authorization_mode: str = ""
    current_push_authorization_head_commit: str = ""
    current_push_authorization_expires_at_utc: str = ""
    current_push_authorization_approved_worktree_identity: str = ""
    current_push_authorization_approved_target_identity: str = ""
    current_push_authorization_matches_current_head: bool = False
    current_push_authorization_matches_current_approved_target: bool = False
    current_push_authorization_matches_current_worktree: bool = False
    current_push_authorization_valid: bool = False


@dataclass(frozen=True, slots=True)
class PushDecisionInputs:
    """Inputs for the final push/checkpoint action recommendation."""

    checkpoint_required: bool
    worktree_dirty: bool
    max_dirty_paths_before_checkpoint: int
    max_untracked_paths_before_checkpoint: int
    dirty_path_count: int
    untracked_path_count: int
    staged_path_count: int
    unstaged_path_count: int
    recorded_remote_publication_for_current_target: bool
    ahead_of_upstream_commits: int | None
    upstream_ref: str
