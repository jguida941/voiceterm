"""Core ReviewSnapshot dataclasses: identity, governance, and delta."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SnapshotIdentity:
    """Repo identity and HEAD metadata that names the snapshot."""

    generation_stamp: str = ""
    generated_at_utc: str = ""
    repo_name: str = ""
    repo_description: str = ""
    product_thesis: str = ""
    remote_url: str = ""
    branch: str = ""
    default_branch: str = ""
    head_sha: str = ""
    head_sha_short: str = ""
    head_subject: str = ""
    head_author: str = ""
    head_timestamp_utc: str = ""
    tree_hash: str = ""
    previous_snapshot_head_sha: str = ""
    commits_since_previous: int = 0


@dataclass(frozen=True, slots=True)
class SnapshotGovernanceState:
    """Typed governance projection: push decision, reviewer runtime, pipeline."""

    push_action: str = ""
    push_reason: str = ""
    push_eligible_now: bool = False
    next_step_command: str = ""
    publication_backlog_state: str = ""
    publication_guidance: str = ""
    latest_push_report_path: str = ""
    latest_push_report_status: str = ""
    latest_push_report_reason: str = ""
    latest_push_report_published_remote: bool = False
    latest_push_report_post_push_green: bool = False
    pipeline_push_report_path: str = ""
    current_push_authorization_id: str = ""
    current_push_authorization_valid: bool = False
    current_push_authorization_head_commit: str = ""
    current_push_authorization_approved_target_identity: str = ""
    interaction_mode: str = "unresolved"
    reviewer_mode: str = ""
    reviewer_freshness: str = "unknown"
    reviewer_publish_clear: bool = False
    reviewer_implementation_blocked: bool = False
    reviewer_block_reason: str = ""
    pipeline_state: str = ""
    pipeline_blocked_reason: str = ""
    pipeline_approval_state: str = ""
    advisory_action: str = ""
    advisory_reason: str = ""
    active_mp_scope: tuple[str, ...] = ()
    active_plan_title: str = ""
    active_plan_path: str = ""
    worktree_clean: bool = False
    checkpoint_required: bool = False


@dataclass(frozen=True, slots=True)
class CommitRow:
    """One commit in the delta range, with derived classification hints."""

    sha: str = ""
    sha_short: str = ""
    subject: str = ""
    author: str = ""
    timestamp_utc: str = ""
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0
    bundle_class: str = "unknown"
    mp_refs: tuple[str, ...] = ()
    checkpoint_markers: tuple[str, ...] = ()
    risk_addons: tuple[str, ...] = ()
    authority_surfaces_touched: tuple[str, ...] = ()
    contracts_mutated: tuple[str, ...] = ()
    remote_url: str = ""
    body_excerpt: str = ""


@dataclass(frozen=True, slots=True)
class FileStatRow:
    """One file change with typed insertion/deletion counts and bundle class."""

    path: str = ""
    insertions: int = 0
    deletions: int = 0
    change_kind: str = "modified"
    bundle_class: str = "unknown"


@dataclass(frozen=True, slots=True)
class SnapshotDelta:
    """Aggregated 'what changed' block pointing the reviewer at new work."""

    from_sha: str = ""
    to_sha: str = ""
    commit_count: int = 0
    files_changed_count: int = 0
    total_insertions: int = 0
    total_deletions: int = 0
    commits: tuple[CommitRow, ...] = ()
    files: tuple[FileStatRow, ...] = ()
    bundle_classes_touched: tuple[str, ...] = ()
    risk_addons_triggered: tuple[str, ...] = ()
    authority_surfaces_touched: tuple[str, ...] = ()


__all__ = [
    "CommitRow",
    "FileStatRow",
    "SnapshotDelta",
    "SnapshotGovernanceState",
    "SnapshotIdentity",
]
