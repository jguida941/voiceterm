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
from .reviewer_mode_projection import write_reviewer_mode
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


# Any next-step command string starting with one of these prefixes is a
# governed publication action. If the reviewer verdict does not authorize push,
# the snapshot must downgrade these to a recovery command instead of letting a
# stale refreshed snapshot route an operator/tool into publishing a blocked
# head. The canonical recovery command is `review-channel --action status`,
# which re-reads typed reviewer state before any further decision.
_GATED_NEXT_STEP_PREFIXES: tuple[str, ...] = (
    "python3 dev/scripts/devctl.py push",
    "devctl push",
    "devctl.py push",
)

_REVIEWER_RECOVERY_NEXT_STEP = (
    "python3 dev/scripts/devctl.py review-channel "
    "--action status --terminal none --format json"
)


def _reviewer_gated_push_projection(
    *,
    push: Mapping[str, object],
    gate: Mapping[str, object],
) -> tuple[bool, str]:
    """Project reviewer-gated push eligibility for the external review snapshot.

    Rule: the snapshot must never advertise ``push_eligible_now=True`` or a
    governed push next-step command when the live reviewer verdict has not
    accepted the current HEAD. This protects any tool or operator flow that
    trusts the refreshed snapshot instead of re-reading typed reviewer state
    directly. Fails closed: if the reviewer gate is dual-agent-active and
    acceptance/publish_clear is missing, the snapshot downgrades both fields
    even when upstream ``push_decision`` still reports eligible.
    """
    raw_eligible = bool(push.get("push_eligible_now"))
    raw_next_step = str(push.get("next_step_command") or "")
    if not _reviewer_blocks_push(gate):
        return raw_eligible, raw_next_step
    downgraded_next = (
        raw_next_step
        if raw_next_step and not _is_gated_push_command(raw_next_step)
        else _REVIEWER_RECOVERY_NEXT_STEP
    )
    return False, downgraded_next


def _reviewer_blocks_push(gate: Mapping[str, object]) -> bool:
    """Return True when the reviewer verdict blocks publication right now.

    The gate blocks push when any of the following hold, **regardless of
    reviewer mode**:
      - implementation is blocked for a reviewer-state reason,
      - the reviewer has not accepted the current implementer state
        (``review_accepted=False``),
      - the reviewer runtime has explicitly disallowed publish
        (``review_gate_allows_push=False``).

    The rule must apply to both ``active_dual_agent`` and ``single_agent``
    remote-control lanes. In the ``single_agent`` lane, upstream
    ``push_decision`` alone cannot observe a follow-up-required reviewer
    verdict, so the snapshot must gate on the reviewer verdict directly.
    Gating only when ``effective_reviewer_mode == active_dual_agent``
    leaves the snapshot advertising ``push_eligible_now=True`` against a
    non-accepted verdict in every other lane — which is the exact
    regression the upstream review layer caught against this file.
    """
    bridge_active = bool(gate.get("bridge_active"))
    implementation_blocked = bool(gate.get("implementation_blocked"))
    review_accepted = bool(gate.get("review_accepted"))
    publish_clear = bool(gate.get("review_gate_allows_push"))
    if not (bridge_active or implementation_blocked):
        return False
    if implementation_blocked:
        return True
    if not review_accepted:
        return True
    if not publish_clear:
        return True
    return False


def _is_gated_push_command(next_step_command: str) -> bool:
    """Return True when the given next-step command is a governed push action."""
    lowered = next_step_command.strip().lower()
    return any(lowered.startswith(prefix) for prefix in _GATED_NEXT_STEP_PREFIXES)


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
    push_eligible_now, next_step_command = _reviewer_gated_push_projection(
        push=push,
        gate=gate,
    )
    return SnapshotGovernanceState(
        push_action=str(push.get("action") or ""),
        push_reason=str(push.get("reason") or ""),
        push_eligible_now=push_eligible_now,
        next_step_command=next_step_command,
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
            or push_enforcement.get(
                "current_push_authorization_approved_target_identity"
            )
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
    write_reviewer_mode(stamp_inputs, governance_state.reviewer_mode)
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


__all__ = [
    "attach_generation_stamp",
    "build_governance_state",
    "build_identity",
]
