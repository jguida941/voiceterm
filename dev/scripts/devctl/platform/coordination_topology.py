"""Bounded coordination/topology reducer shared by planning and status surfaces."""

from __future__ import annotations

from ..runtime.review_state_models import ReviewState
from ..runtime.work_intake_models import (
    WorkIntakeCoordinationState,
    WorkIntakeOwnershipState,
)
from .coordination_topology_models import (
    COORDINATION_TOPOLOGY_CONTRACT_ID,
    COORDINATION_TOPOLOGY_SCHEMA_VERSION,
    CoordinationParticipantRecord,
    CoordinationReadyGateRecord,
    CoordinationTopologySnapshot,
    DelegatedWorktreeRecord,
)
from .coordination_topology_support import (
    attention_status,
    fanout_posture,
    participant_records,
    ready_gate_records,
    resync_posture,
    reviewer_freshness,
    runtime_role_topology,
    runtime_provider_roles,
    topology_summary,
    delegated_worktree_records,
)

_MAX_PARTICIPANTS = 4
_MAX_DELEGATED_WORK = 6
_MAX_READY_GATES = 4
_MAX_SCOPE_PATHS = 6
_MAX_CONFLICTING_PATHS = 6


def build_coordination_topology_snapshot(
    *,
    review_state: ReviewState | None,
    ownership: WorkIntakeOwnershipState,
    coordination: WorkIntakeCoordinationState,
) -> CoordinationTopologySnapshot:
    """Join live runtime, ownership, and routing signals into one answer."""
    role_topology = runtime_role_topology(review_state)
    active_provider_role_map = runtime_provider_roles(review_state)
    participants = participant_records(
        review_state=review_state,
        active_provider_roles=active_provider_role_map,
        active_provider_ids=role_topology.active_providers,
        role_occupancies=role_topology.role_occupancies,
    )
    delegated_worktrees = delegated_worktree_records(
        review_state=review_state,
        duplicate_worktrees=coordination.duplicate_delegated_worktrees,
    )
    ready_gates = ready_gate_records(review_state)
    # Typed contract boundary: the support module must hand back the typed
    # coordination dataclasses so the snapshot cannot be filled with raw
    # tuples or mapping rows that bypass schema validation.
    for participant in participants:
        if not isinstance(participant, CoordinationParticipantRecord):
            raise TypeError(
                "participant_records must return CoordinationParticipantRecord rows"
            )
    for worktree in delegated_worktrees:
        if not isinstance(worktree, DelegatedWorktreeRecord):
            raise TypeError(
                "delegated_worktree_records must return DelegatedWorktreeRecord rows"
            )
    for gate in ready_gates:
        if not isinstance(gate, CoordinationReadyGateRecord):
            raise TypeError(
                "ready_gate_records must return CoordinationReadyGateRecord rows"
            )

    fanout_posture_value, fanout_safe, recommended_topology = fanout_posture(
        review_state=review_state,
        coordination=coordination,
        ownership=ownership,
        ready_gates=ready_gates,
        participants=participants,
        delegated_worktrees=delegated_worktrees,
    )
    resync_posture_value, resync_required, resync_reason, resync_command = resync_posture(
        review_state=review_state,
        coordination=coordination,
    )

    active_participant_count = sum(1 for row in participants if row.live)
    active_conductor_count = len(active_provider_role_map)
    typed_role_topology = role_topology.typed_role_topology_label
    collaboration_topology = _collaboration_topology(
        declared=coordination.collaboration_topology,
        typed_role_topology=typed_role_topology,
    )
    planned_lane_count = sum(row.planned_lane_count for row in participants)
    requested_worker_budget_total = sum(
        max(row.requested_worker_budget, 0) for row in participants
    )
    live_delegated_worker_count = sum(
        1 for row in delegated_worktrees if row.live
    )
    scope_paths = ownership.scope_paths[:_MAX_SCOPE_PATHS]
    conflicting_paths = (
        ownership.outside_scope_dirty_paths or ownership.dirty_paths
    )[:_MAX_CONFLICTING_PATHS]

    return CoordinationTopologySnapshot(
        collaboration_topology=collaboration_topology,
        authority_mode=coordination.authority_mode or "self_directed",
        work_ownership_mode=coordination.work_ownership_mode or "exclusive_slice",
        sync_cadence_mode=coordination.sync_cadence_mode or "continuous",
        interaction_mode=coordination.interaction_mode or "unresolved",
        ownership_status=ownership.status or "clear",
        reviewer_mode=coordination.reviewer_mode,
        effective_reviewer_mode=coordination.effective_reviewer_mode,
        reviewer_freshness=reviewer_freshness(review_state),
        attention_status=attention_status(review_state),
        active_participant_count=active_participant_count,
        active_conductor_count=active_conductor_count,
        planned_lane_count=planned_lane_count,
        requested_worker_budget_total=requested_worker_budget_total,
        live_delegated_worker_count=live_delegated_worker_count,
        fanout_posture=fanout_posture_value,
        fanout_safe=fanout_safe,
        recommended_topology=recommended_topology,
        resync_posture=resync_posture_value,
        resync_required=resync_required,
        resync_reason=resync_reason,
        resync_command=resync_command,
        scope_paths=scope_paths,
        conflicting_paths=conflicting_paths,
        duplicate_delegated_worktrees=coordination.duplicate_delegated_worktrees,
        active_participants=participants[:_MAX_PARTICIPANTS],
        delegated_worktrees=delegated_worktrees[:_MAX_DELEGATED_WORK],
        ready_gates=ready_gates[:_MAX_READY_GATES],
        summary=topology_summary(
            active_participant_count=active_participant_count,
            collaboration_topology=collaboration_topology,
            work_ownership_mode=coordination.work_ownership_mode or "exclusive_slice",
            fanout_posture=fanout_posture_value,
            resync_posture=resync_posture_value,
        ),
    )


def _collaboration_topology(*, declared: str, typed_role_topology: str) -> str:
    if typed_role_topology != "typed_role_topology_unresolved" and declared in {
        "",
        "single_agent",
    }:
        return typed_role_topology
    return declared or typed_role_topology


__all__ = [
    "COORDINATION_TOPOLOGY_CONTRACT_ID",
    "COORDINATION_TOPOLOGY_SCHEMA_VERSION",
    "CoordinationParticipantRecord",
    "CoordinationReadyGateRecord",
    "CoordinationTopologySnapshot",
    "DelegatedWorktreeRecord",
    "build_coordination_topology_snapshot",
]
