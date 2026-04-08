"""Bounded reducer for live multi-agent coordination posture."""

from __future__ import annotations

from pathlib import Path

from ..config import get_repo_root
from ..governance.push_state import current_head_commit_sha
from ..runtime.review_state_locator import load_current_review_state
from ..runtime.startup_context import build_startup_context
from ..time_utils import utc_timestamp
from .coordination_snapshot_models import CoordinationSnapshot
from .coordination_snapshot_support import (
    actor_records,
    coordination_summary,
    declared_topology,
    duplicate_worktrees,
    fanout_posture,
    recommended_topology,
    repo_name,
    resync_reasons,
    safe_to_fanout,
    text,
    worktree_strategy,
)
from .planning_ir_reduction import build_conflicts


def build_coordination_snapshot(
    *,
    repo_root: Path | None = None,
    startup_context: object | None = None,
    review_state: object | None = None,
) -> CoordinationSnapshot:
    """Build one bounded answer for topology, ownership, fanout, and resync."""
    resolved_root = (repo_root or get_repo_root()).resolve()
    resolved_startup = startup_context or build_startup_context(repo_root=resolved_root)
    resolved_governance = getattr(resolved_startup, "governance", None)
    resolved_review_state = review_state or load_current_review_state(
        resolved_root,
        governance=resolved_governance,
    )
    work_intake = getattr(resolved_startup, "work_intake", None)
    if work_intake is None:
        raise ValueError("startup_context.work_intake is required")

    ownership = work_intake.ownership
    coordination = work_intake.coordination
    collaboration = getattr(resolved_review_state, "collaboration", None)
    delegated_work = tuple(getattr(collaboration, "delegated_work", ()) or ())
    participants = tuple(getattr(collaboration, "participants", ()) or ())
    duplicate_worktree_rows = duplicate_worktrees(
        delegated_work=delegated_work,
        startup_duplicates=tuple(coordination.duplicate_delegated_worktrees),
    )
    conflicts = build_conflicts(
        ownership=ownership,
        coordination=coordination,
    )
    declared_topology_value = declared_topology(
        collaboration=collaboration,
        observed_topology=coordination.collaboration_topology or "single_agent",
    )
    observed_topology = coordination.collaboration_topology or "single_agent"
    fanout_posture_value = fanout_posture(
        delegated_work=delegated_work,
        duplicate_worktrees=duplicate_worktree_rows,
        conflicts=conflicts,
        collaboration=collaboration,
        declared_topology=declared_topology_value,
        observed_topology=observed_topology,
    )
    worktree_strategy_value = worktree_strategy(
        delegated_work=delegated_work,
        duplicate_worktrees=duplicate_worktree_rows,
    )
    resync_reason_rows = resync_reasons(
        review_state=resolved_review_state,
        conflicts=conflicts,
        declared_topology=declared_topology_value,
        observed_topology=observed_topology,
    )
    safe_to_fanout_value = safe_to_fanout(
        fanout_posture=fanout_posture_value,
        duplicate_worktrees=duplicate_worktree_rows,
        resync_reasons=resync_reason_rows,
    )
    recommended_topology_value = recommended_topology(
        observed_topology=observed_topology,
        fanout_posture=fanout_posture_value,
        safe_to_fanout=safe_to_fanout_value,
        resync_reasons=resync_reason_rows,
    )
    repo_identity = getattr(resolved_governance, "repo_identity", None)
    current_slice = text(getattr(collaboration, "current_slice", "")) or text(
        getattr(getattr(resolved_review_state, "current_session", None), "current_instruction", "")
    )
    return CoordinationSnapshot(
        generated_at_utc=utc_timestamp(),
        repo_name=repo_name(resolved_governance, resolved_root),
        repo_root=str(resolved_root),
        current_branch=text(getattr(repo_identity, "current_branch", "")),
        head_commit_sha=current_head_commit_sha(repo_root=resolved_root) or "",
        active_target=getattr(work_intake, "active_target", None),
        current_slice=current_slice,
        scope_paths=tuple(getattr(ownership, "scope_paths", ()) or ()),
        ownership_status=text(getattr(ownership, "status", "")),
        authority_mode=text(getattr(coordination, "authority_mode", "")),
        work_ownership_mode=text(getattr(coordination, "work_ownership_mode", "")),
        sync_cadence_mode=text(getattr(coordination, "sync_cadence_mode", "")),
        declared_topology=declared_topology_value,
        observed_topology=observed_topology,
        recommended_topology=recommended_topology_value,
        fanout_posture=fanout_posture_value,
        safe_to_fanout=safe_to_fanout_value,
        worktree_strategy=worktree_strategy_value,
        resync_required=bool(resync_reason_rows),
        resync_reasons=resync_reason_rows,
        observed_active_participant_count=int(
            getattr(coordination, "active_participant_count", 0) or 0
        ),
        declared_participant_count=len(participants),
        planned_delegated_worker_count=len(delegated_work),
        live_delegated_worker_count=max(
            int(getattr(coordination, "live_delegated_worker_count", 0) or 0),
            sum(1 for receipt in delegated_work if bool(getattr(receipt, "live", False))),
        ),
        active_participants=tuple(getattr(coordination, "active_participants", ()) or ()),
        duplicate_worktrees=duplicate_worktree_rows,
        conflict_summaries=tuple(
            summary
            for conflict in conflicts
            if (summary := text(getattr(conflict, "summary", "")))
        ),
        actors=actor_records(
            review_state=resolved_review_state,
            active_participants=tuple(getattr(coordination, "active_participants", ()) or ()),
        ),
        summary=coordination_summary(
            observed_topology=observed_topology,
            declared_topology=declared_topology_value,
            fanout_posture=fanout_posture_value,
            recommended_topology=recommended_topology_value,
            resync_reasons=resync_reason_rows,
        ),
    )


__all__ = ["build_coordination_snapshot"]
