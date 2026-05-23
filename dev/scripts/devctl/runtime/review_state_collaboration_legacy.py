"""Legacy fallback builders for runtime collaboration-state payloads."""

from __future__ import annotations

from .collaboration_wake_contract import (
    loop_autonomy_contract,
    wake_continuity_contract,
)
from .collaboration_owner_selection import select_verification_owner
from .review_state_models import (
    AgentRegistryState,
    CollaborationArbitrationState,
    ConductorCapabilityState,
    CollaborationParticipantState,
    CollaborationPeerReviewState,
    CollaborationReadyGateState,
    CollaborationRestartState,
    CollaborationRoleAssignmentState,
    CollaborationSessionState,
    ReviewBridgeState,
    ReviewCurrentSessionState,
)
from .review_state_collaboration_legacy_support import (
    capability_provider,
    legacy_agent_for_capability,
    legacy_owner_status,
    legacy_watcher_owner,
    same_agent,
)
from .role_profile import normalize_role_id


def _legacy_collaboration_state(
    *,
    review,
    current_session: ReviewCurrentSessionState,
    bridge: ReviewBridgeState,
    registry: AgentRegistryState,
    string_fn,
) -> CollaborationSessionState:
    role_assignments = _legacy_role_assignments(bridge=bridge, registry=registry)
    participants = _legacy_participants(registry)
    mutation_owner = legacy_agent_for_capability(
        role_assignments,
        {"implementation", "mutation"},
    )
    verification_owner = select_verification_owner(
        role_assignments=role_assignments,
        mutation_owner=mutation_owner,
        same_agent_fn=same_agent,
    )
    verification_status = legacy_owner_status(
        verification_owner,
        participants=participants,
        role_assignments=role_assignments,
    )
    watcher_owner = legacy_watcher_owner(
        participants=participants,
        role_assignments=role_assignments,
        mutation_owner=mutation_owner,
        verification_owner=verification_owner,
    )
    watcher_status = legacy_owner_status(
        watcher_owner,
        participants=participants,
        role_assignments=role_assignments,
    )
    (
        mutation_wake_mode,
        verification_wake_mode,
        watcher_wake_mode,
        wake_continuity_ok,
        wake_gap_summary,
    ) = wake_continuity_contract(
        reviewer_mode=bridge.effective_reviewer_mode or bridge.reviewer_mode,
        mutation_owner=mutation_owner,
        verification_owner=verification_owner,
        watcher_owner=watcher_owner,
        participants=participants,
    )
    loop_autonomy = loop_autonomy_contract(
        reviewer_mode=bridge.effective_reviewer_mode or bridge.reviewer_mode,
        mutation_owner=mutation_owner,
        verification_owner=verification_owner,
        watcher_owner=watcher_owner,
        participants=participants,
    )
    has_runtime = any(participant.live for participant in participants)
    has_context = bool(
        participants or current_session.current_instruction or current_session.open_findings
    )
    return CollaborationSessionState(
        schema_version=1,
        contract_id="CollaborationSession",
        session_id=string_fn(review.get("session_id")) or "review-channel",
        plan_id=string_fn(review.get("plan_id")),
        status="live" if has_runtime else "resumable" if has_context else "inactive",
        reviewer_mode=bridge.effective_reviewer_mode or bridge.reviewer_mode,
        operator_mode="manual",
        lead_agent="",
        review_agent="",
        coding_agent="",
        current_slice=current_session.current_instruction
        or current_session.last_reviewed_scope,
        peer_review=CollaborationPeerReviewState(
            current_instruction=current_session.current_instruction,
            current_instruction_revision=current_session.current_instruction_revision,
            open_findings=current_session.open_findings,
            implementer_status=current_session.implementer_status,
            implementer_ack=current_session.implementer_ack,
            implementer_ack_state=current_session.implementer_ack_state,
            implementer_state_hash=current_session.implementer_state_hash,
            last_reviewed_scope=current_session.last_reviewed_scope,
        ),
        arbitration=CollaborationArbitrationState(
            status="clear",
            summary="",
            owner="",
        ),
        restart=CollaborationRestartState(
            status="resumable" if has_context else "fresh_start",
            resumable=has_context,
            source="legacy_projection" if has_context else "",
            launch_truth=bridge.launch_truth,
            reviewer_mode=bridge.reviewer_mode,
            effective_reviewer_mode=bridge.effective_reviewer_mode,
            last_codex_poll_utc=bridge.last_codex_poll_utc,
            last_worktree_hash=bridge.last_worktree_hash,
        ),
        ready_gates=_legacy_ready_gates(bridge=bridge, current_session=current_session),
        role_assignments=role_assignments,
        participants=participants,
        delegated_work=(),
        mutation_owner=mutation_owner,
        verification_owner=verification_owner,
        verification_status=verification_status,
        watcher_owner=watcher_owner,
        watcher_status=watcher_status,
        mutation_wake_mode=mutation_wake_mode,
        verification_wake_mode=verification_wake_mode,
        watcher_wake_mode=watcher_wake_mode,
        wake_continuity_ok=wake_continuity_ok,
        wake_gap_summary=wake_gap_summary,
        loop_wake_mode=loop_autonomy.loop_wake_mode,
        loop_wake_interval_seconds=loop_autonomy.loop_wake_interval_seconds,
        loop_driver_agent=loop_autonomy.loop_driver_agent,
        loop_autonomy_ok=loop_autonomy.loop_autonomy_ok,
        loop_gap_summary=loop_autonomy.loop_gap_summary,
    )


def _legacy_role_assignments(
    *,
    bridge: ReviewBridgeState,
    registry: AgentRegistryState,
) -> tuple[CollaborationRoleAssignmentState, ...]:
    assignments: list[CollaborationRoleAssignmentState] = []
    for agent in registry.agents:
        if not agent.agent_id:
            continue
        provider = agent.provider or agent.agent_id
        role_id = normalize_role_id(agent.lane or agent.current_job)
        if not role_id:
            continue
        assignments.append(
            CollaborationRoleAssignmentState(
                role_id=role_id,
                agent_id=agent.agent_id,
                provider=provider,
                display_name=agent.display_name or agent.agent_id,
                status=agent.job_state or "declared",
                source="legacy_projection:migrated_registry_lane",
                live=agent.job_state not in {"inactive", "idle", "", "unknown"},
            )
        )
    for capability in (
        bridge.reviewer_capability,
        bridge.implementer_capability,
        getattr(bridge, "operator_capability", None),
    ):
        provider = capability_provider(capability, default="")
        role_id = normalize_role_id(
            getattr(capability, "role", "")
            or getattr(capability, "role_id", "")
            or getattr(capability, "target_role", "")
        )
        if not provider or not role_id:
            continue
        if any(
            assignment.provider == provider and assignment.role_id == role_id
            for assignment in assignments
        ):
            continue
        assignments.append(
            CollaborationRoleAssignmentState(
                role_id=role_id,
                agent_id=provider,
                provider=provider,
                display_name=provider.title(),
                status="declared",
                source="legacy_projection:migrated_capability_role",
            )
        )
    return tuple(assignments)


def _legacy_participants(
    registry: AgentRegistryState,
) -> tuple[CollaborationParticipantState, ...]:
    participants: list[CollaborationParticipantState] = []
    for agent in registry.agents:
        if not agent.agent_id:
            continue
        provider = agent.provider or agent.agent_id
        role = normalize_role_id(agent.lane or agent.current_job)
        live = agent.job_state not in {"inactive", "idle", "", "unknown"}
        participants.append(
            CollaborationParticipantState(
                agent_id=agent.agent_id,
                provider=provider,
                display_name=agent.display_name or agent.agent_id,
                role=role,
                session_name="",
                live=live,
                status=agent.job_state or "unknown",
                capture_mode="",
                approval_mode="",
                supervision_mode="",
                prepared_at="",
                metadata_path="",
                log_path="",
                launch_command="",
                requested_worker_budget=None,
                planned_lane_count=0,
                host_wake_mode="continuous" if live else "inactive",
            )
        )
    return tuple(participants)


def _legacy_ready_gates(
    *,
    bridge: ReviewBridgeState,
    current_session: ReviewCurrentSessionState,
) -> tuple[CollaborationReadyGateState, ...]:
    review_status = (
        "blocked"
        if bridge.review_needed or bridge.reviewed_hash_current is False
        else "ready"
    )
    implementer_status = (
        "ready" if current_session.implementer_ack_state == "current" else "pending"
    )
    return (
        CollaborationReadyGateState(
            gate_id="review_truth",
            status=review_status,
            summary=(
                "Reviewer follow-up is still required."
                if review_status == "blocked"
                else "Reviewer truth is current."
            ),
        ),
        CollaborationReadyGateState(
            gate_id="implementer_state",
            status=implementer_status,
            summary=(
                "Implementer state matches the current instruction revision."
                if implementer_status == "ready"
                else "Implementer state has not acknowledged the current instruction revision yet."
            ),
        ),
    )
