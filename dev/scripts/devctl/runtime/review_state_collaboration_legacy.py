"""Legacy fallback builders for runtime collaboration-state payloads."""

from __future__ import annotations

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
from .role_profile import TandemRole, role_for_provider


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
        lead_agent=_legacy_agent_for_role(role_assignments, "lead_agent"),
        review_agent=_legacy_agent_for_role(role_assignments, "review_agent"),
        coding_agent=_legacy_agent_for_role(role_assignments, "coding_agent"),
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
    )


def _legacy_role_assignments(
    *,
    bridge: ReviewBridgeState,
    registry: AgentRegistryState,
) -> tuple[CollaborationRoleAssignmentState, ...]:
    reviewer_provider = _provider_from_registry(
        registry,
        TandemRole.REVIEWER.value,
    ) or _capability_provider(bridge.reviewer_capability, default="codex")
    implementer_provider = _provider_from_registry(
        registry,
        TandemRole.IMPLEMENTER.value,
    ) or _capability_provider(bridge.implementer_capability, default="claude")
    operator_provider = _provider_from_registry(
        registry,
        TandemRole.OPERATOR.value,
    ) or "operator"
    return (
        CollaborationRoleAssignmentState(
            role_id="lead_agent",
            agent_id=reviewer_provider,
            provider=reviewer_provider,
            display_name=reviewer_provider.title(),
            status="declared",
            source="legacy_projection",
        ),
        CollaborationRoleAssignmentState(
            role_id="review_agent",
            agent_id=reviewer_provider,
            provider=reviewer_provider,
            display_name=reviewer_provider.title(),
            status="declared",
            source="legacy_projection",
        ),
        CollaborationRoleAssignmentState(
            role_id="coding_agent",
            agent_id=implementer_provider,
            provider=implementer_provider,
            display_name=implementer_provider.title(),
            status="declared",
            source="legacy_projection",
        ),
        CollaborationRoleAssignmentState(
            role_id="operator_agent",
            agent_id=operator_provider,
            provider=operator_provider,
            display_name=operator_provider.title(),
            status="declared",
            source="legacy_projection",
        ),
    )


def _legacy_participants(
    registry: AgentRegistryState,
) -> tuple[CollaborationParticipantState, ...]:
    participants: list[CollaborationParticipantState] = []
    for agent in registry.agents:
        if not agent.agent_id:
            continue
        provider = agent.provider or agent.agent_id
        role = role_for_provider(provider).value
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


def _legacy_agent_for_role(
    assignments: tuple[CollaborationRoleAssignmentState, ...],
    role_id: str,
) -> str:
    for assignment in assignments:
        if assignment.role_id == role_id:
            return assignment.agent_id
    return ""


def _provider_from_registry(
    registry: AgentRegistryState,
    role_name: str,
) -> str:
    for agent in registry.agents:
        provider = agent.provider or agent.agent_id
        if role_for_provider(provider).value == role_name:
            return provider
    return ""


def _capability_provider(
    capability: ConductorCapabilityState | None,
    *,
    default: str,
) -> str:
    provider = capability.provider if capability is not None else ""
    return provider.strip() or default
