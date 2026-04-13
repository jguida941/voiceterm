"""Bounded reducer for live multi-agent coordination posture."""

from __future__ import annotations

from pathlib import Path
import re
from types import SimpleNamespace

from ..config import get_repo_root
from ..governance.push_state import current_head_commit_sha
from ..runtime.review_state_locator import load_current_review_state
from ..runtime.startup_context import build_startup_context
from ..runtime.work_intake_coordination import build_work_intake_coordination_state
from ..runtime.work_intake_ownership import build_work_intake_ownership_state
from ..runtime.work_intake_selection import build_target_ref, select_active_plan_entry
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

_MP_SCOPE_TOKEN_RE = re.compile(r"MP-\d+(?:\.\.MP-\d+)?", re.IGNORECASE)


def build_coordination_snapshot(
    *,
    repo_root: Path | None = None,
    startup_context: object | None = None,
    review_state: object | None = None,
    governance: object | None = None,
    work_intake: object | None = None,
) -> CoordinationSnapshot:
    """Build one bounded answer for topology, ownership, fanout, and resync.

    Callers that already resolved a typed ``review_state`` for the current proof
    tick should pass it explicitly so this reducer does not refresh live review
    state a second time through ``load_current_review_state``.
    """
    resolved_root = (repo_root or get_repo_root()).resolve()
    resolved_startup = startup_context
    resolved_governance = (
        getattr(resolved_startup, "governance", None)
        if resolved_startup is not None
        else governance
    )
    resolved_work_intake = (
        getattr(resolved_startup, "work_intake", None)
        if resolved_startup is not None
        else work_intake
    )
    if resolved_governance is None or resolved_work_intake is None:
        resolved_startup = startup_context or build_startup_context(repo_root=resolved_root)
        if resolved_governance is None:
            resolved_governance = getattr(resolved_startup, "governance", None)
        if resolved_work_intake is None:
            resolved_work_intake = getattr(resolved_startup, "work_intake", None)
    resolved_review_state = review_state or load_current_review_state(
        resolved_root,
        governance=resolved_governance,
    )
    if resolved_work_intake is None:
        raise ValueError("coordination snapshot requires startup_context.work_intake")

    ownership = resolved_work_intake.ownership
    coordination = resolved_work_intake.coordination
    collaboration = getattr(resolved_review_state, "collaboration", None)
    delegated_work = tuple(getattr(collaboration, "delegated_work", ()) or ())
    participants = tuple(getattr(collaboration, "participants", ()) or ())
    continuity = getattr(resolved_work_intake, "continuity", None)
    active_target = getattr(resolved_work_intake, "active_target", None)
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
    persisted_coordination = getattr(resolved_review_state, "coordination", None)
    current_slice = _select_current_slice(
        text(getattr(persisted_coordination, "current_slice", "")),
        text(getattr(collaboration, "current_slice", "")),
        text(getattr(getattr(resolved_review_state, "current_session", None), "current_instruction", "")),
        text(getattr(continuity, "current_goal", "")),
        text(getattr(continuity, "next_action", "")),
        text(getattr(continuity, "summary", "")),
        text(getattr(active_target, "plan_title", "")),
        text(getattr(active_target, "plan_path", "")),
    )
    return CoordinationSnapshot(
        generated_at_utc=utc_timestamp(),
        repo_name=repo_name(resolved_governance, resolved_root),
        repo_root=str(resolved_root),
        current_branch=text(getattr(repo_identity, "current_branch", "")),
        head_commit_sha=current_head_commit_sha(repo_root=resolved_root) or "",
        active_target=active_target,
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


def build_coordination_snapshot_for_review_state(
    *,
    repo_root: Path | None = None,
    governance: object | None,
    review_state: object | None,
    reviewer_gate: object | None = None,
) -> CoordinationSnapshot | None:
    """Bridge typed review-state runtime into the canonical coordination reducer.

    ``reviewer_gate`` is forwarded to ``build_work_intake_coordination_state``
    so callers that already derived a typed gate (startup-context, the shared
    coordination loader) get the same reviewer-gate-aware reducer as the
    upstream ``build_startup_context`` path. Without this, dashboard and
    session-resume see raw review-state topology while startup-context sees
    the gate-corrected topology — that asymmetry is the F1 divergence.
    """
    if governance is None or review_state is None:
        return None
    resolved_root = (repo_root or get_repo_root()).resolve()
    ownership = build_work_intake_ownership_state(
        repo_root=resolved_root,
        review_state=review_state,
    )
    coordination = build_work_intake_coordination_state(
        governance=governance,
        review_state=review_state,
        ownership=ownership,
        reviewer_gate=reviewer_gate,
    )
    active_target = build_target_ref(
        resolved_root,
        select_active_plan_entry(governance, review_state),
    )
    return build_coordination_snapshot(
        repo_root=resolved_root,
        review_state=review_state,
        governance=governance,
        work_intake=SimpleNamespace(
            active_target=active_target,
            ownership=ownership,
            coordination=coordination,
        ),
    )


__all__ = [
    "build_coordination_snapshot",
    "build_coordination_snapshot_for_review_state",
]


def _select_current_slice(*candidates: str) -> str:
    fallback = ""
    for candidate in candidates:
        value = text(candidate)
        if not value:
            continue
        if _is_scope_only_slice(value):
            if not fallback:
                fallback = value
            continue
        return value
    return fallback


def _is_scope_only_slice(value: str) -> bool:
    if not value:
        return False
    matches = list(_MP_SCOPE_TOKEN_RE.finditer(value))
    if not matches:
        return False
    stripped = _MP_SCOPE_TOKEN_RE.sub("", value)
    stripped = re.sub(r"[\s,;:/()._-]+", "", stripped)
    return not stripped
