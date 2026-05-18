"""Push-governance records for the ProjectGovernance contract."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping

from ..governance.push_policy import PushPublicationPolicy
from .project_governance_push_ahead import ahead_commit_kwargs
from .project_governance_push_counts import worktree_change_counts_from_payload
from .project_governance_push_projection import push_projection_inputs_from_payload
from .value_coercion import (
    coerce_bool,
    coerce_int,
    coerce_string,
    coerce_string_items,
)


@dataclass(frozen=True, slots=True)
class PushEnforcement:
    """Repo-owned push/checkpoint posture for the current worktree."""

    current_branch: str = ""
    current_head_commit: str = ""
    default_remote: str = "origin"
    development_branch: str = "main"
    release_branch: str = "main"
    pre_push_hook_path: str = ""
    pre_push_hook_installed: bool = False
    raw_git_push_guarded: bool = False
    upstream_ref: str = ""
    ahead_of_upstream_commits: int | None = None
    ahead_of_upstream_source_commits: int | None = None
    ahead_of_upstream_managed_receipt_commits: int = 0
    ahead_of_upstream_unclassified_commits: int | None = None
    dirty_path_count: int = 0
    untracked_path_count: int = 0
    staged_path_count: int = 0
    unstaged_path_count: int = 0
    max_dirty_paths_before_checkpoint: int = 12
    max_untracked_paths_before_checkpoint: int = 6
    checkpoint_required: bool = False
    safe_to_continue_editing: bool = True
    checkpoint_reason: str = "clean_worktree"
    worktree_dirty: bool = False
    worktree_clean: bool = True
    excluded_path_count: int = 0
    managed_projection_drift: bool = False
    managed_projection_dirty_paths: tuple[str, ...] = ()
    advisory_context_dirty_paths: tuple[str, ...] = ()
    recommended_action: str = "use_devctl_push"
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
    latest_push_report_publication_mode: str = ""
    latest_push_report_governed_push_verified: bool = False
    latest_push_report_operator_bypass_evidence_required: bool = False
    current_worktree_identity: str = ""
    current_approved_target_identity: str = ""
    latest_push_report_approved_worktree_identity: str = ""
    latest_push_report_approved_target_identity: str = ""
    latest_push_report_matches_current_approved_target: bool = False
    latest_push_report_matches_current_worktree: bool = True
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
    selected_push_report_publication_mode: str = ""
    selected_push_report_governed_push_verified: bool = False
    selected_push_report_operator_bypass_evidence_required: bool = False
    selected_push_report_approved_worktree_identity: str = ""
    selected_push_report_approved_target_identity: str = ""
    selected_push_report_matches_current_approved_target: bool = False
    selected_push_report_matches_current_worktree: bool = True
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
    current_push_authorization_matches_current_worktree: bool = True
    current_push_authorization_valid: bool = False
    publication_audit_required: bool = False
    operator_bypass_evidence_required: bool = False


def _fallback_payload_value(
    payload: Mapping[str, object],
    key: str,
    *,
    fallback_key: str | None = None,
) -> object:
    value = payload.get(key)
    if value is not None or fallback_key is None:
        return value
    return payload.get(fallback_key)


def _push_report_projection_kwargs(
    payload: Mapping[str, object],
    *,
    prefix: str,
    current_worktree_identity: str,
    fallback_prefix: str | None = None,
) -> dict[str, object]:
    def _value(name: str) -> object:
        fallback_name = f"{fallback_prefix}_{name}" if fallback_prefix else None
        return _fallback_payload_value(
            payload,
            f"{prefix}_{name}",
            fallback_key=fallback_name,
        )

    approved_worktree_identity = coerce_string(_value("approved_worktree_identity"))
    published_remote = coerce_bool(_value("published_remote"))
    publication_mode = coerce_string(_value("publication_mode"))
    governed_raw = _value("governed_push_verified")
    governed_push_verified = (
        coerce_bool(governed_raw)
        if governed_raw is not None
        else bool(
            published_remote
            and publication_mode not in {"raw_no_verify", "ungoverned_remote_advance"}
        )
    )
    return {
        f"{prefix}_branch": coerce_string(_value("branch")),
        f"{prefix}_remote": coerce_string(_value("remote")),
        f"{prefix}_head_commit": coerce_string(_value("head_commit")),
        f"{prefix}_status": coerce_string(_value("status")),
        f"{prefix}_reason": coerce_string(_value("reason")),
        f"{prefix}_published_remote": published_remote,
        f"{prefix}_post_push_green": coerce_bool(_value("post_push_green")),
        f"{prefix}_publication_mode": publication_mode,
        f"{prefix}_governed_push_verified": governed_push_verified,
        f"{prefix}_operator_bypass_evidence_required": coerce_bool(
            _value("operator_bypass_evidence_required")
        ),
        f"{prefix}_approved_worktree_identity": approved_worktree_identity,
        f"{prefix}_approved_target_identity": coerce_string(
            _value("approved_target_identity")
        ),
        f"{prefix}_matches_current_approved_target": coerce_bool(
            _value("matches_current_approved_target")
        ),
        f"{prefix}_matches_current_worktree": _coerce_worktree_match(
            _value("matches_current_worktree"),
            approved_worktree_identity=approved_worktree_identity,
            current_worktree_identity=current_worktree_identity,
        ),
        f"{prefix}_matches_current_branch": coerce_bool(
            _value("matches_current_branch")
        ),
        f"{prefix}_matches_current_head": coerce_bool(_value("matches_current_head")),
    }


def _selected_push_report_source(payload: Mapping[str, object]) -> str:
    explicit = coerce_string(payload.get("selected_push_report_source"))
    if explicit:
        return explicit
    if (
        payload.get("selected_push_report_status") is None
        and (
            payload.get("latest_push_report_status") is not None
            or payload.get("latest_push_report_reason") is not None
        )
    ):
        return "latest_artifact"
    return ""


def push_enforcement_from_mapping(
    payload: Mapping[str, object],
) -> PushEnforcement:
    """Parse PushEnforcement from a JSON-like mapping."""
    ahead_raw = payload.get("ahead_of_upstream_commits")
    ahead = coerce_int(ahead_raw) if ahead_raw is not None else None
    change_counts = worktree_change_counts_from_payload(payload)
    publication_policy = PushPublicationPolicy(
        recommend_after_ahead_commits=(
            coerce_int(payload.get("recommend_after_ahead_commits")) or 2
        ),
        urgent_after_ahead_commits=(
            coerce_int(payload.get("urgent_after_ahead_commits")) or 5
        ),
    )
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
    projection_inputs = push_projection_inputs_from_payload(payload)
    current_worktree_identity = projection_inputs.current_worktree_identity
    current_push_authorization_approved_worktree_identity = coerce_string(
        payload.get("current_push_authorization_approved_worktree_identity")
    )
    latest_push_report_kwargs = _push_report_projection_kwargs(
        payload,
        prefix="latest_push_report",
        current_worktree_identity=current_worktree_identity,
    )
    selected_push_report_kwargs = _push_report_projection_kwargs(
        payload,
        prefix="selected_push_report",
        current_worktree_identity=current_worktree_identity,
        fallback_prefix="latest_push_report",
    )
    return PushEnforcement(
        current_branch=projection_inputs.current_branch,
        current_head_commit=projection_inputs.current_head_commit,
        default_remote=projection_inputs.default_remote,
        development_branch=coerce_string(payload.get("development_branch"))
        or "main",
        release_branch=coerce_string(payload.get("release_branch")) or "main",
        pre_push_hook_path=coerce_string(payload.get("pre_push_hook_path")),
        pre_push_hook_installed=coerce_bool(payload.get("pre_push_hook_installed")),
        raw_git_push_guarded=coerce_bool(payload.get("raw_git_push_guarded")),
        upstream_ref=projection_inputs.upstream_ref,
        ahead_of_upstream_commits=ahead,
        **ahead_commit_kwargs(payload),
        dirty_path_count=change_counts.dirty_path_count,
        untracked_path_count=change_counts.untracked_path_count,
        staged_path_count=change_counts.staged_path_count,
        unstaged_path_count=change_counts.unstaged_path_count,
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
        excluded_path_count=change_counts.excluded_path_count,
        managed_projection_drift=coerce_bool(
            payload.get("managed_projection_drift")
        ),
        managed_projection_dirty_paths=coerce_string_items(
            payload.get("managed_projection_dirty_paths")
        ),
        advisory_context_dirty_paths=coerce_string_items(
            payload.get("advisory_context_dirty_paths")
        ),
        recommended_action=coerce_string(payload.get("recommended_action"))
        or "use_devctl_push",
        pending_publication_commits=(
            coerce_int(payload.get("pending_publication_commits"))
            if payload.get("pending_publication_commits") is not None
            else None
        ),
        publication_backlog_state=coerce_string(payload.get("publication_backlog_state"))
        or "none",
        publication_backlog_summary=coerce_string(
            payload.get("publication_backlog_summary")
        ),
        publication_backlog_recommended=coerce_bool(
            payload.get("publication_backlog_recommended")
        ),
        publication_backlog_urgent=coerce_bool(
            payload.get("publication_backlog_urgent")
        ),
        publication_audit_required=coerce_bool(
            payload.get("publication_audit_required")
        ),
        operator_bypass_evidence_required=coerce_bool(
            payload.get("operator_bypass_evidence_required")
        ),
        recommend_after_ahead_commits=(
            publication_policy.recommend_after_ahead_commits
        ),
        urgent_after_ahead_commits=publication_policy.urgent_after_ahead_commits,
        latest_push_report_path=coerce_string(payload.get("latest_push_report_path")),
        current_worktree_identity=current_worktree_identity,
        current_approved_target_identity=(
            projection_inputs.current_approved_target_identity
        ),
        selected_push_report_source=_selected_push_report_source(payload),
        current_push_authorization_id=coerce_string(
            payload.get("current_push_authorization_id")
        ),
        current_push_authorization_mode=coerce_string(
            payload.get("current_push_authorization_mode")
        ),
        current_push_authorization_head_commit=coerce_string(
            payload.get("current_push_authorization_head_commit")
        ),
        current_push_authorization_expires_at_utc=coerce_string(
            payload.get("current_push_authorization_expires_at_utc")
        ),
        current_push_authorization_approved_worktree_identity=current_push_authorization_approved_worktree_identity,
        current_push_authorization_approved_target_identity=coerce_string(
            payload.get("current_push_authorization_approved_target_identity")
        ),
        current_push_authorization_matches_current_head=coerce_bool(
            payload.get("current_push_authorization_matches_current_head")
        ),
        current_push_authorization_matches_current_approved_target=coerce_bool(
            payload.get("current_push_authorization_matches_current_approved_target")
        ),
        current_push_authorization_matches_current_worktree=_coerce_worktree_match(
            payload.get("current_push_authorization_matches_current_worktree"),
            approved_worktree_identity=current_push_authorization_approved_worktree_identity,
            current_worktree_identity=current_worktree_identity,
        ),
        current_push_authorization_valid=coerce_bool(
            payload.get("current_push_authorization_valid")
        ),
        **latest_push_report_kwargs,
        **selected_push_report_kwargs,
    )


def _coerce_worktree_match(
    value: object,
    *,
    approved_worktree_identity: str,
    current_worktree_identity: str,
) -> bool:
    """Treat legacy blank worktree identity records as compatible with the current lane."""
    if value is not None:
        return coerce_bool(value)
    if not approved_worktree_identity:
        return True
    return bool(
        current_worktree_identity
        and approved_worktree_identity
        and current_worktree_identity == approved_worktree_identity
    )
