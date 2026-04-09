"""Identity and governance-state builders for ReviewSnapshot orchestration."""

from __future__ import annotations

import datetime as _dt
from collections.abc import Mapping
from pathlib import Path

from ..config import REPO_ROOT
from .review_snapshot_git import (
    current_branch,
    head_author_and_time,
    head_sha,
    head_subject,
    tree_hash,
)
from .review_snapshot_models_core import (
    SnapshotDelta,
    SnapshotGovernanceState,
    SnapshotIdentity,
)
from .review_snapshot_models_quality import SnapshotQualitySignals
from .review_snapshot_utils import as_mapping, coerce_str_tuple
from .surface_snapshot import build_surface_snapshot_id


def build_identity(
    *,
    repo_root: Path = REPO_ROOT,
    startup: Mapping[str, object],
    previous_head_sha: str,
) -> SnapshotIdentity:
    full_sha, short_sha = head_sha(repo_root)
    subject = head_subject(repo_root, "HEAD")
    author, timestamp = head_author_and_time(repo_root, "HEAD")
    tree = tree_hash(repo_root, "HEAD")
    branch = current_branch(repo_root)
    governance = as_mapping(startup.get("governance"))
    repo_identity = as_mapping(governance.get("repo_identity"))
    repo_pack = as_mapping(governance.get("repo_pack"))
    generated_at = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return SnapshotIdentity(
        generation_stamp="",
        generated_at_utc=generated_at,
        repo_name=str(repo_identity.get("repo_name") or ""),
        repo_description=str(repo_pack.get("description") or ""),
        product_thesis=str(startup.get("product_thesis") or ""),
        remote_url=str(repo_identity.get("remote_url") or ""),
        branch=branch,
        default_branch=str(repo_identity.get("default_branch") or ""),
        head_sha=full_sha,
        head_sha_short=short_sha,
        head_subject=subject,
        head_author=author,
        head_timestamp_utc=timestamp,
        tree_hash=tree,
        previous_snapshot_head_sha=previous_head_sha,
        commits_since_previous=0,
    )


def build_governance_state(*, startup: Mapping[str, object]) -> SnapshotGovernanceState:
    push = as_mapping(startup.get("push_decision"))
    gate = as_mapping(startup.get("reviewer_gate"))
    pipeline = as_mapping(startup.get("remote_commit_pipeline"))
    work_intake = as_mapping(startup.get("work_intake"))
    continuity = as_mapping(work_intake.get("continuity"))
    backlog = as_mapping(push.get("publication_backlog"))
    push_enforcement = as_mapping(
        as_mapping(startup.get("governance")).get("push_enforcement")
    )
    push_authorization = as_mapping(pipeline.get("push_authorization"))
    return SnapshotGovernanceState(
        push_action=str(push.get("action") or ""),
        push_reason=str(push.get("reason") or ""),
        push_eligible_now=bool(push.get("push_eligible_now")),
        next_step_command=str(push.get("next_step_command") or ""),
        publication_backlog_state=str(backlog.get("backlog_state") or ""),
        publication_guidance=str(push.get("publication_guidance") or ""),
        latest_push_report_path=str(
            push_enforcement.get("latest_push_report_path") or ""
        ),
        latest_push_report_status=str(
            push_enforcement.get("latest_push_report_status") or ""
        ),
        latest_push_report_reason=str(
            push_enforcement.get("latest_push_report_reason") or ""
        ),
        latest_push_report_published_remote=bool(
            push_enforcement.get("latest_push_report_published_remote")
        ),
        latest_push_report_post_push_green=bool(
            push_enforcement.get("latest_push_report_post_push_green")
        ),
        pipeline_push_report_path=str(pipeline.get("push_report_path") or ""),
        current_push_authorization_id=str(
            push_authorization.get("authorization_id")
            or push_enforcement.get("current_push_authorization_id")
            or ""
        ),
        current_push_authorization_valid=bool(
            push_enforcement.get("current_push_authorization_valid")
        ),
        current_push_authorization_head_commit=str(
            push_authorization.get("authorized_head_sha")
            or push_enforcement.get("current_push_authorization_head_commit")
            or ""
        ),
        current_push_authorization_approved_target_identity=str(
            push_authorization.get("approved_target_identity")
            or push_enforcement.get("current_push_authorization_approved_target_identity")
            or ""
        ),
        interaction_mode=str(gate.get("operator_interaction_mode") or "unresolved"),
        reviewer_mode=str(gate.get("effective_reviewer_mode") or ""),
        reviewer_freshness=str(gate.get("required_checks_status") or "unknown"),
        reviewer_publish_clear=bool(gate.get("review_gate_allows_push")),
        reviewer_implementation_blocked=bool(gate.get("implementation_blocked")),
        reviewer_block_reason=str(gate.get("implementation_block_reason") or ""),
        pipeline_state=str(pipeline.get("state") or ""),
        pipeline_blocked_reason=str(pipeline.get("blocked_reason") or ""),
        pipeline_approval_state=str(pipeline.get("approval_state") or ""),
        advisory_action=str(startup.get("advisory_action") or ""),
        advisory_reason=str(startup.get("advisory_reason") or ""),
        active_mp_scope=coerce_str_tuple(continuity.get("source_scope")),
        active_plan_title=str(continuity.get("source_plan_title") or ""),
        active_plan_path=str(continuity.get("source_plan_path") or ""),
        worktree_clean=bool(push.get("worktree_clean")),
        staged_path_count=int(push_enforcement.get("staged_path_count") or 0),
        unstaged_path_count=int(push_enforcement.get("unstaged_path_count") or 0),
        checkpoint_required=bool(push_enforcement.get("checkpoint_required")),
    )


def attach_generation_stamp(
    identity: SnapshotIdentity,
    governance_state: SnapshotGovernanceState,
    delta: SnapshotDelta,
    quality: SnapshotQualitySignals,
) -> SnapshotIdentity:
    stamp_inputs: dict[str, object] = {}
    stamp_inputs["head_sha"] = identity.head_sha
    stamp_inputs["tree_hash"] = identity.tree_hash
    stamp_inputs["push_action"] = governance_state.push_action
    stamp_inputs["reviewer_mode"] = governance_state.reviewer_mode
    stamp_inputs["pipeline_state"] = governance_state.pipeline_state
    stamp_inputs["commit_count"] = delta.commit_count
    stamp_inputs["governance_open"] = quality.governance_open_findings
    stamp = build_surface_snapshot_id(
        reviewer_runtime=stamp_inputs,
        commit_pipeline={"state": governance_state.pipeline_state},
        push_decision={"action": governance_state.push_action},
    )
    return SnapshotIdentity(
        generation_stamp=stamp,
        generated_at_utc=identity.generated_at_utc,
        repo_name=identity.repo_name,
        repo_description=identity.repo_description,
        product_thesis=identity.product_thesis,
        remote_url=identity.remote_url,
        branch=identity.branch,
        default_branch=identity.default_branch,
        head_sha=identity.head_sha,
        head_sha_short=identity.head_sha_short,
        head_subject=identity.head_subject,
        head_author=identity.head_author,
        head_timestamp_utc=identity.head_timestamp_utc,
        tree_hash=identity.tree_hash,
        previous_snapshot_head_sha=identity.previous_snapshot_head_sha,
        commits_since_previous=delta.commit_count,
    )


__all__ = ["attach_generation_stamp", "build_governance_state", "build_identity"]
