"""Runtime push/checkpoint state detection for startup surfaces."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path

from ..commands.vcs.push_artifact import (
    load_latest_push_report,
    latest_push_report_relpath,
    lookup_push_receipt,
)
from ..config import REPO_ROOT
from ..repo_packs import active_path_config
from ..review_channel.remote_commit_pipeline_artifact import (
    load_remote_commit_pipeline_contract,
)
from .push_publication import build_publication_backlog_state
from .push_policy import PushCheckpointPolicy, PushPolicy
from .push_state_authorization import (
    approved_target_identity_from_pipeline as _approved_target_identity_from_pipeline,
    checkpoint_reason as _checkpoint_reason,
    push_authorization_state_from_pipeline as _push_authorization_state_from_pipeline,
)
from .push_state_git import (
    git_stdout as _git_stdout,
    worktree_change_counts as _worktree_change_counts,
)
from .push_state_report import (
    current_target_remote as _current_target_remote,
    latest_push_report_approved_target_identity as _latest_push_report_approved_target_identity,
    latest_push_report_state as _latest_push_report_state,
)


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
    current_approved_target_identity: str = ""
    latest_push_report_approved_target_identity: str = ""
    latest_push_report_matches_current_approved_target: bool = False
    latest_push_report_matches_current_branch: bool = False
    latest_push_report_matches_current_head: bool = False
    current_push_authorization_id: str = ""
    current_push_authorization_mode: str = ""
    current_push_authorization_head_commit: str = ""
    current_push_authorization_expires_at_utc: str = ""
    current_push_authorization_approved_target_identity: str = ""
    current_push_authorization_matches_current_head: bool = False
    current_push_authorization_matches_current_approved_target: bool = False
    current_push_authorization_valid: bool = False


def detect_push_enforcement_state(
    policy: PushPolicy,
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, object]:
    """Return repo-owned push/checkpoint state for startup/runtime surfaces."""
    runtime = _detect_runtime_inputs(policy=policy, repo_root=repo_root)
    excluded_paths = (
        *policy.checkpoint.compatibility_projection_paths,
        *policy.checkpoint.advisory_context_paths,
    )
    dirty_path_count, untracked_path_count = _worktree_change_counts(
        repo_root,
        exclude_paths=excluded_paths,
    )
    worktree_dirty = dirty_path_count > 0
    worktree_clean = not worktree_dirty
    checkpoint_required = (
        dirty_path_count >= policy.checkpoint.max_dirty_paths_before_checkpoint
        or untracked_path_count >= policy.checkpoint.max_untracked_paths_before_checkpoint
    )
    safe_to_continue_editing = not checkpoint_required
    checkpoint_reason = "clean_worktree"
    receipt = lookup_push_receipt(
        branch=runtime.current_branch,
        head_commit=runtime.current_head_commit,
        repo_root=repo_root,
    )
    latest_push_report = receipt or load_latest_push_report(repo_root=repo_root) or {}
    push_stages = latest_push_report.get("push_stages")
    if not isinstance(push_stages, dict):
        push_stages = {}
    (
        latest_push_report_branch,
        latest_push_report_remote,
        latest_push_report_head_commit,
        latest_push_report_approved_target_identity,
        latest_push_report_matches_current_branch,
        latest_push_report_matches_current_head,
        latest_push_report_matches_current_approved_target,
    ) = _latest_push_report_state(
        report=latest_push_report,
        current_branch=runtime.current_branch,
        current_head_commit=runtime.current_head_commit,
        current_approved_target_identity=runtime.current_approved_target_identity,
    )
    current_target_remote = _current_target_remote(
        upstream_ref=runtime.upstream_ref,
        default_remote=policy.default_remote,
    )
    recorded_remote_publication_for_current_target = (
        bool(push_stages.get("published_remote"))
        and latest_push_report_matches_current_branch
        and latest_push_report_matches_current_head
        and latest_push_report_matches_current_approved_target
        and (not latest_push_report_remote or latest_push_report_remote == current_target_remote)
    )
    has_remote_work_to_push = not (
        recorded_remote_publication_for_current_target
        or (runtime.ahead_of_upstream_commits == 0 and runtime.upstream_ref)
    )
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
    elif recorded_remote_publication_for_current_target or (
        runtime.ahead_of_upstream_commits == 0 and runtime.upstream_ref
    ):
        recommended_action = "no_push_needed"
    else:
        recommended_action = "use_devctl_push"
    publication_backlog = build_publication_backlog_state(
        ahead_of_upstream_commits=runtime.ahead_of_upstream_commits,
        has_remote_work_to_push=has_remote_work_to_push,
        recommend_after_ahead_commits=policy.publication.recommend_after_ahead_commits,
        urgent_after_ahead_commits=policy.publication.urgent_after_ahead_commits,
    )
    snapshot = PushEnforcementSnapshot(
        current_branch=runtime.current_branch,
        current_head_commit=runtime.current_head_commit,
        default_remote=policy.default_remote,
        development_branch=policy.development_branch,
        release_branch=policy.release_branch,
        pre_push_hook_path=str(runtime.hook_path),
        pre_push_hook_installed=runtime.hook_installed,
        raw_git_push_guarded=runtime.raw_git_push_guarded,
        upstream_ref=runtime.upstream_ref,
        ahead_of_upstream_commits=runtime.ahead_of_upstream_commits,
        dirty_path_count=dirty_path_count,
        untracked_path_count=untracked_path_count,
        max_dirty_paths_before_checkpoint=policy.checkpoint.max_dirty_paths_before_checkpoint,
        max_untracked_paths_before_checkpoint=policy.checkpoint.max_untracked_paths_before_checkpoint,
        checkpoint_required=checkpoint_required,
        safe_to_continue_editing=safe_to_continue_editing,
        checkpoint_reason=checkpoint_reason,
        worktree_dirty=worktree_dirty,
        worktree_clean=worktree_clean,
        recommended_action=recommended_action,
        pending_publication_commits=publication_backlog.pending_publication_commits,
        publication_backlog_state=publication_backlog.backlog_state,
        publication_backlog_summary=publication_backlog.backlog_summary,
        publication_backlog_recommended=publication_backlog.backlog_recommended,
        publication_backlog_urgent=publication_backlog.backlog_urgent,
        recommend_after_ahead_commits=publication_backlog.recommend_after_ahead_commits,
        urgent_after_ahead_commits=publication_backlog.urgent_after_ahead_commits,
        latest_push_report_path=latest_push_report_relpath(repo_root=repo_root),
        latest_push_report_branch=latest_push_report_branch,
        latest_push_report_remote=latest_push_report_remote,
        latest_push_report_head_commit=latest_push_report_head_commit,
        latest_push_report_status=str(latest_push_report.get("status") or "").strip(),
        latest_push_report_reason=str(latest_push_report.get("reason") or "").strip(),
        latest_push_report_published_remote=bool(push_stages.get("published_remote")),
        latest_push_report_post_push_green=bool(push_stages.get("post_push_green")),
        current_approved_target_identity=runtime.current_approved_target_identity,
        latest_push_report_approved_target_identity=latest_push_report_approved_target_identity,
        latest_push_report_matches_current_approved_target=latest_push_report_matches_current_approved_target,
        latest_push_report_matches_current_branch=latest_push_report_matches_current_branch,
        latest_push_report_matches_current_head=latest_push_report_matches_current_head,
        current_push_authorization_id=runtime.current_push_authorization_id,
        current_push_authorization_mode=runtime.current_push_authorization_mode,
        current_push_authorization_head_commit=runtime.current_push_authorization_head_commit,
        current_push_authorization_expires_at_utc=runtime.current_push_authorization_expires_at_utc,
        current_push_authorization_approved_target_identity=(
            runtime.current_push_authorization_approved_target_identity
        ),
        current_push_authorization_matches_current_head=(
            runtime.current_push_authorization_matches_current_head
        ),
        current_push_authorization_matches_current_approved_target=(
            runtime.current_push_authorization_matches_current_approved_target
        ),
        current_push_authorization_valid=runtime.current_push_authorization_valid,
    )
    return asdict(snapshot)


@dataclass(frozen=True, slots=True)
class _PushRuntimeInputs:
    hook_path: Path
    hook_installed: bool
    raw_git_push_guarded: bool
    current_branch: str
    current_head_commit: str
    current_approved_target_identity: str
    current_push_authorization_id: str
    current_push_authorization_mode: str
    current_push_authorization_head_commit: str
    current_push_authorization_expires_at_utc: str
    current_push_authorization_approved_target_identity: str
    current_push_authorization_matches_current_head: bool
    current_push_authorization_matches_current_approved_target: bool
    current_push_authorization_valid: bool
    upstream_ref: str
    ahead_of_upstream_commits: int | None


def _detect_runtime_inputs(
    *,
    policy: PushPolicy,
    repo_root: Path,
) -> _PushRuntimeInputs:
    """Return current git/push-authorization facts used by push-state detection."""
    hook_path_text = _git_stdout(repo_root, "rev-parse", "--git-path", "hooks/pre-push")
    hook_path = (
        Path(hook_path_text)
        if hook_path_text
        else (repo_root / ".git" / "hooks" / "pre-push")
    )
    current_branch = _git_stdout(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    current_head_commit = current_head_commit_sha(repo_root=repo_root)
    pipeline = load_remote_commit_pipeline_contract(
        output_root=repo_root / active_path_config().review_status_dir_rel
    )
    current_approved_target_identity = _approved_target_identity_from_pipeline(
        pipeline
    )
    authorization_state = _push_authorization_state_from_pipeline(
        pipeline=pipeline,
        current_head_commit=current_head_commit,
        current_approved_target_identity=current_approved_target_identity,
    )
    upstream_ref = current_upstream_ref(repo_root=repo_root)
    ahead: int | None = None
    if upstream_ref:
        ahead_text = _git_stdout(repo_root, "rev-list", "--count", f"{upstream_ref}..HEAD")
        ahead = int(ahead_text) if ahead_text.isdigit() else None
    hook_installed = hook_path.is_file()
    return _PushRuntimeInputs(
        hook_path=hook_path,
        hook_installed=hook_installed,
        raw_git_push_guarded=hook_installed and os.access(hook_path, os.X_OK),
        current_branch=current_branch,
        current_head_commit=current_head_commit,
        current_approved_target_identity=current_approved_target_identity,
        current_push_authorization_id=authorization_state[0],
        current_push_authorization_mode=authorization_state[1],
        current_push_authorization_head_commit=authorization_state[2],
        current_push_authorization_expires_at_utc=authorization_state[3],
        current_push_authorization_approved_target_identity=authorization_state[4],
        current_push_authorization_matches_current_head=authorization_state[5],
        current_push_authorization_matches_current_approved_target=authorization_state[6],
        current_push_authorization_valid=authorization_state[7],
        upstream_ref=upstream_ref,
        ahead_of_upstream_commits=ahead,
    )


def current_upstream_ref(*, repo_root: Path = REPO_ROOT) -> str:
    """Return the current branch's tracked upstream ref, or empty when unset."""
    return _git_stdout(
        repo_root,
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{u}",
    )


def current_head_commit_sha(*, repo_root: Path = REPO_ROOT) -> str:
    """Return the current HEAD commit SHA, or empty when unavailable."""
    return _git_stdout(repo_root, "rev-parse", "HEAD")
