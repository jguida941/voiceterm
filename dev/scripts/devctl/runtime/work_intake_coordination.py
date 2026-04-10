"""Bounded coordination-state reduction for startup work-intake."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .conductor_capability import normalize_reviewer_mode
from .project_governance import ProjectGovernance
from .review_state_models import ReviewState
from .work_intake_coordination_status import (
    active_implementation_owner,
    resync_required,
)
from .work_intake_models import (
    WorkIntakeCoordinationState,
    WorkIntakeOwnershipState,
)

if TYPE_CHECKING:
    from .startup_context import ReviewerGateState

_MAX_ACTIVE_ROLES = 3
_MAX_ACTIVE_PARTICIPANTS = 3
_MAX_DELEGATED_AGENTS = 3
_MAX_DELEGATED_WORKTREES = 3


def build_work_intake_coordination_state(
    *,
    governance: ProjectGovernance,
    review_state: ReviewState | None,
    ownership: WorkIntakeOwnershipState,
    reviewer_gate: "ReviewerGateState | None" = None,
) -> WorkIntakeCoordinationState:
    """Reduce runtime/review state into one bounded coordination summary."""
    participants = _live_participants(review_state)
    delegated_work = _live_delegated_work(review_state)
    delegated_agents = _delegated_agents(delegated_work)
    delegated_worktrees = _delegated_worktrees(delegated_work)
    duplicate_delegated_worktrees = _duplicate_worktrees(delegated_work)
    active_roles = _active_roles(participants)
    active_participants = _active_participants(participants)
    resolved_implementation_owner = active_implementation_owner(participants)
    resolved_reviewer_mode = _reviewer_mode(review_state, reviewer_gate=reviewer_gate)
    resolved_effective_mode = _effective_reviewer_mode(
        review_state,
        reviewer_gate=reviewer_gate,
    )

    collaboration_topology = _collaboration_topology(
        active_roles=active_roles,
        participant_count=len(participants),
        live_delegated_worker_count=len(delegated_agents),
        reviewer_mode=resolved_reviewer_mode,
        effective_reviewer_mode=resolved_effective_mode,
    )
    authority_mode = _authority_mode(
        governance=governance,
        review_state=review_state,
        reviewer_mode=resolved_reviewer_mode,
        effective_reviewer_mode=resolved_effective_mode,
        bridge_active=_bridge_active(reviewer_gate),
    )
    requires_resync = resync_required(
        review_state=review_state,
        duplicate_delegated_worktrees=duplicate_delegated_worktrees,
        ownership=ownership,
        collaboration_topology=collaboration_topology,
    )
    work_ownership_mode = _work_ownership_mode(ownership.status)
    if duplicate_delegated_worktrees:
        work_ownership_mode = "concurrent_writer_conflict"
    elif delegated_agents and work_ownership_mode == "exclusive_slice":
        work_ownership_mode = "shared_slice"
    sync_cadence_mode = _sync_cadence_mode(
        governance=governance,
        review_state=review_state,
        work_ownership_mode=work_ownership_mode,
        collaboration_topology=collaboration_topology,
    )

    return WorkIntakeCoordinationState(
        collaboration_topology=collaboration_topology,
        authority_mode=authority_mode,
        work_ownership_mode=work_ownership_mode,
        sync_cadence_mode=sync_cadence_mode,
        reviewer_mode=resolved_reviewer_mode,
        effective_reviewer_mode=resolved_effective_mode,
        interaction_mode=_interaction_mode(_interaction_mode_value(reviewer_gate)),
        summary=_summary(
            collaboration_topology=collaboration_topology,
            authority_mode=authority_mode,
            work_ownership_mode=work_ownership_mode,
            sync_cadence_mode=sync_cadence_mode,
            review_gate_allows_push=_review_gate_allows_push(reviewer_gate),
        ),
        active_implementation_owner=resolved_implementation_owner,
        active_participant_count=len(participants),
        live_delegated_worker_count=len(delegated_agents),
        active_roles=active_roles[:_MAX_ACTIVE_ROLES],
        active_participants=active_participants[:_MAX_ACTIVE_PARTICIPANTS],
        delegated_agents=delegated_agents[:_MAX_DELEGATED_AGENTS],
        delegated_worktrees=delegated_worktrees[:_MAX_DELEGATED_WORKTREES],
        duplicate_delegated_worktrees=duplicate_delegated_worktrees[
            :_MAX_DELEGATED_WORKTREES
        ],
        resync_required=requires_resync,
        concurrent_writer_conflict_detected=bool(duplicate_delegated_worktrees)
        or ownership.concurrent_writer_detected,
    )


def _live_participants(review_state: ReviewState | None) -> tuple[tuple[str, str], ...]:
    if review_state is None:
        return ()
    participants: list[tuple[str, str]] = []
    for participant in review_state.collaboration.participants:
        if not participant.live:
            continue
        name = participant.agent_id or participant.provider
        role = participant.role or "unknown"
        if not name:
            continue
        row = (name, role)
        if row not in participants:
            participants.append(row)
    return tuple(participants)


def _live_delegated_work(
    review_state: ReviewState | None,
) -> tuple[tuple[str, str], ...]:
    if review_state is None:
        return ()
    delegated_work: list[tuple[str, str]] = []
    for receipt in review_state.collaboration.delegated_work:
        if not receipt.live or not receipt.agent_id:
            continue
        row = (
            receipt.agent_id,
            str(receipt.worktree or "").strip(),
        )
        delegated_work.append(row)
    return tuple(delegated_work)


def _delegated_agents(delegated_work: tuple[tuple[str, str], ...]) -> tuple[str, ...]:
    agents: list[str] = []
    for agent_id, _worktree in delegated_work:
        if agent_id not in agents:
            agents.append(agent_id)
    return tuple(agents)


def _delegated_worktrees(
    delegated_work: tuple[tuple[str, str], ...],
) -> tuple[str, ...]:
    worktrees: list[str] = []
    for _agent_id, worktree in delegated_work:
        if not worktree:
            continue
        if worktree not in worktrees:
            worktrees.append(worktree)
    return tuple(worktrees)


def _duplicate_worktrees(
    delegated_work: tuple[tuple[str, str], ...],
) -> tuple[str, ...]:
    counts: dict[str, int] = {}
    duplicates: list[str] = []
    for _agent_id, value in delegated_work:
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
        if counts[value] == 2:
            duplicates.append(value)
    return tuple(duplicates)


def _active_roles(participants: tuple[tuple[str, str], ...]) -> tuple[str, ...]:
    roles: list[str] = []
    for _, role in participants:
        if role and role not in roles:
            roles.append(role)
    return tuple(roles)


def _active_participants(
    participants: tuple[tuple[str, str], ...],
) -> tuple[str, ...]:
    return tuple(f"{name}:{role}" for name, role in participants)


def _bridge_mode(review_state: ReviewState | None) -> str:
    if review_state is None:
        return ""
    return review_state.bridge.reviewer_mode


def _bridge_effective_mode(review_state: ReviewState | None) -> str:
    if review_state is None:
        return ""
    return review_state.bridge.effective_reviewer_mode


def _reviewer_mode(
    review_state: ReviewState | None,
    *,
    reviewer_gate: "ReviewerGateState | None",
) -> str:
    if reviewer_gate is not None and reviewer_gate.reviewer_mode:
        return reviewer_gate.reviewer_mode
    return _bridge_mode(review_state)


def _effective_reviewer_mode(
    review_state: ReviewState | None,
    *,
    reviewer_gate: "ReviewerGateState | None",
) -> str:
    if reviewer_gate is not None and reviewer_gate.effective_reviewer_mode:
        return reviewer_gate.effective_reviewer_mode
    bridge_mode = _bridge_effective_mode(review_state)
    if bridge_mode:
        return bridge_mode
    return _reviewer_mode(review_state, reviewer_gate=reviewer_gate)


def _interaction_mode_value(
    reviewer_gate: "ReviewerGateState | None",
) -> str:
    if reviewer_gate is None:
        return ""
    return str(reviewer_gate.operator_interaction_mode or "").strip()


def _bridge_active(reviewer_gate: "ReviewerGateState | None") -> bool:
    if reviewer_gate is None:
        return False
    return bool(reviewer_gate.bridge_active)


def _review_gate_allows_push(reviewer_gate: "ReviewerGateState | None") -> bool:
    if reviewer_gate is None:
        return False
    return bool(reviewer_gate.review_gate_allows_push)


def _collaboration_topology(
    *,
    active_roles: tuple[str, ...],
    participant_count: int,
    live_delegated_worker_count: int,
    reviewer_mode: str,
    effective_reviewer_mode: str,
) -> str:
    if live_delegated_worker_count > 0:
        return "multi_agent_orchestrated"
    normalized_mode = normalize_reviewer_mode(
        effective_reviewer_mode or reviewer_mode
    )
    if participant_count == 1 and normalized_mode == "active_dual_agent":
        return "observer_plus_implementer"
    if (
        participant_count >= 2
        and "operator" in active_roles
        and "implementer" in active_roles
        and "reviewer" not in active_roles
    ):
        return "observer_plus_implementer"
    if participant_count >= 2:
        return "dual_agent"
    return "single_agent"


def _authority_mode(
    *,
    governance: ProjectGovernance,
    review_state: ReviewState | None,
    reviewer_mode: str,
    effective_reviewer_mode: str,
    bridge_active: bool,
) -> str:
    approval_state = ""
    if review_state is not None:
        approval_state = str(review_state.commit_pipeline.approval_state or "").strip()
        if review_state.pending_approvals():
            return "operator_approval_required"
    if approval_state in {"pending", "requested"}:
        return "operator_approval_required"

    push = governance.push_enforcement
    if push.checkpoint_required or not push.safe_to_continue_editing:
        return "push_locked"
    if review_state is not None and review_state.queue.pending_total > 0:
        return "packet_gated"
    if bridge_active or (
        normalize_reviewer_mode(effective_reviewer_mode or reviewer_mode)
        == "active_dual_agent"
    ):
        return "reviewer_gated"
    return "self_directed"


def _work_ownership_mode(status: str) -> str:
    if status == "concurrent_writer_activity":
        return "concurrent_writer_conflict"
    if status == "scope_unknown_dirty_paths":
        return "scope_unknown"
    if status == "outside_scope_dirty_paths":
        return "handoff_pending"
    return "exclusive_slice"


def _sync_cadence_mode(
    *,
    governance: ProjectGovernance,
    review_state: ReviewState | None,
    work_ownership_mode: str,
    collaboration_topology: str,
) -> str:
    push = governance.push_enforcement
    if push.worktree_clean and push.ahead_of_upstream_commits not in (0, None):
        return "before_publish"
    if push.checkpoint_required:
        return "checkpointed"
    if work_ownership_mode in {
        "concurrent_writer_conflict",
        "handoff_pending",
        "scope_unknown",
    }:
        return "before_scope_change"
    if review_state is not None:
        attention = review_state.attention
        if attention is not None and attention.status not in {"", "healthy"}:
            return "on_red_streak"
    if collaboration_topology in {
        "dual_agent",
        "multi_agent_orchestrated",
        "observer_plus_implementer",
    }:
        return "continuous"
    return "checkpointed"


def _interaction_mode(raw: str) -> str:
    normalized = str(raw or "").strip().lower()
    if normalized in {
        "local_terminal",
        "remote_control",
        "dashboard_only",
        "unattended",
    }:
        return normalized
    return "unresolved"


def _summary(
    *,
    collaboration_topology: str,
    authority_mode: str,
    work_ownership_mode: str,
    sync_cadence_mode: str,
    review_gate_allows_push: bool,
) -> str:
    publish_note = "publish-ready" if review_gate_allows_push else "not publish-ready"
    return (
        f"{collaboration_topology}, {authority_mode}, {work_ownership_mode}, "
        f"{sync_cadence_mode}, {publish_note}"
    )


__all__ = ["build_work_intake_coordination_state"]
