"""Collaboration-session parsing helpers for runtime review-state payloads."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .control_state import _int, _mapping, _string
from .review_state_parse_support import _bool
from .review_state_models import (
    AgentRegistryState,
    CollaborationArbitrationState,
    CollaborationParticipantState,
    CollaborationPeerReviewState,
    CollaborationReadyGateState,
    CollaborationRestartState,
    CollaborationRoleAssignmentState,
    CollaborationSessionState,
    DelegatedWorkReceiptState,
    ReviewBridgeState,
    ReviewCurrentSessionState,
)
from .role_profile import TandemRole, role_for_provider


def collaboration_state_from_payload(
    *,
    collaboration: Mapping[str, object],
    review: Mapping[str, object],
    current_session: ReviewCurrentSessionState,
    bridge: ReviewBridgeState,
    registry: AgentRegistryState,
) -> CollaborationSessionState:
    if collaboration:
        return CollaborationSessionState(
            schema_version=_int(collaboration.get("schema_version")) or 1,
            contract_id=_string(collaboration.get("contract_id")) or "CollaborationSession",
            session_id=_string(collaboration.get("session_id"))
            or _string(review.get("session_id"))
            or "review-channel",
            plan_id=_string(collaboration.get("plan_id")) or _string(review.get("plan_id")),
            status=_string(collaboration.get("status")) or "inactive",
            reviewer_mode=_string(collaboration.get("reviewer_mode"))
            or bridge.effective_reviewer_mode
            or bridge.reviewer_mode,
            operator_mode=_string(collaboration.get("operator_mode")) or "manual",
            lead_agent=_string(collaboration.get("lead_agent")),
            review_agent=_string(collaboration.get("review_agent")),
            coding_agent=_string(collaboration.get("coding_agent")),
            current_slice=_string(collaboration.get("current_slice")),
            peer_review=_peer_review_state_from_mapping(
                _mapping(collaboration.get("peer_review")),
                current_session=current_session,
            ),
            arbitration=_arbitration_state_from_mapping(
                _mapping(collaboration.get("arbitration"))
            ),
            restart=_restart_state_from_mapping(
                _mapping(collaboration.get("restart")),
                bridge=bridge,
            ),
            ready_gates=_ready_gates_from_value(collaboration.get("ready_gates")),
            role_assignments=_role_assignments_from_value(
                collaboration.get("role_assignments")
            ),
            participants=_participants_from_value(collaboration.get("participants")),
            delegated_work=_delegated_work_from_value(
                collaboration.get("delegated_work")
            ),
        )
    return _legacy_collaboration_state(
        review=review,
        current_session=current_session,
        bridge=bridge,
        registry=registry,
    )


def _peer_review_state_from_mapping(
    mapping: Mapping[str, object],
    *,
    current_session: ReviewCurrentSessionState,
) -> CollaborationPeerReviewState:
    if not mapping:
        return CollaborationPeerReviewState(
            current_instruction=current_session.current_instruction,
            current_instruction_revision=current_session.current_instruction_revision,
            open_findings=current_session.open_findings,
            implementer_status=current_session.implementer_status,
            implementer_ack=current_session.implementer_ack,
            implementer_ack_state=current_session.implementer_ack_state,
            implementer_state_hash=current_session.implementer_state_hash,
            last_reviewed_scope=current_session.last_reviewed_scope,
        )
    return CollaborationPeerReviewState(
        current_instruction=_string(mapping.get("current_instruction")),
        current_instruction_revision=_string(
            mapping.get("current_instruction_revision")
        ),
        open_findings=_string(mapping.get("open_findings")),
        implementer_status=_string(mapping.get("implementer_status")),
        implementer_ack=_string(mapping.get("implementer_ack")),
        implementer_ack_state=_string(mapping.get("implementer_ack_state")) or "unknown",
        implementer_state_hash=_string(mapping.get("implementer_state_hash")),
        last_reviewed_scope=_string(mapping.get("last_reviewed_scope")),
    )


def _arbitration_state_from_mapping(
    mapping: Mapping[str, object],
) -> CollaborationArbitrationState:
    return CollaborationArbitrationState(
        status=_string(mapping.get("status")) or "clear",
        summary=_string(mapping.get("summary")),
        owner=_string(mapping.get("owner")),
    )


def _restart_state_from_mapping(
    mapping: Mapping[str, object],
    *,
    bridge: ReviewBridgeState,
) -> CollaborationRestartState:
    if not mapping:
        return CollaborationRestartState(
            status="fresh_start",
            resumable=False,
            source="",
            launch_truth=bridge.launch_truth,
            reviewer_mode=bridge.reviewer_mode,
            effective_reviewer_mode=bridge.effective_reviewer_mode,
            last_codex_poll_utc=bridge.last_codex_poll_utc,
            last_worktree_hash=bridge.last_worktree_hash,
        )
    return CollaborationRestartState(
        status=_string(mapping.get("status")) or "fresh_start",
        resumable=_bool(mapping.get("resumable")),
        source=_string(mapping.get("source")),
        launch_truth=_string(mapping.get("launch_truth")) or bridge.launch_truth,
        reviewer_mode=_string(mapping.get("reviewer_mode")) or bridge.reviewer_mode,
        effective_reviewer_mode=_string(mapping.get("effective_reviewer_mode"))
        or bridge.effective_reviewer_mode,
        last_codex_poll_utc=_string(mapping.get("last_codex_poll_utc"))
        or bridge.last_codex_poll_utc,
        last_worktree_hash=_string(mapping.get("last_worktree_hash"))
        or bridge.last_worktree_hash,
    )


def _ready_gates_from_value(
    value: object,
) -> tuple[CollaborationReadyGateState, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(
        CollaborationReadyGateState(
            gate_id=_string(mapping.get("gate_id")),
            status=_string(mapping.get("status")) or "unknown",
            summary=_string(mapping.get("summary")),
        )
        for row in value
        if (mapping := _mapping(row)) and _string(mapping.get("gate_id"))
    )


def _role_assignments_from_value(
    value: object,
) -> tuple[CollaborationRoleAssignmentState, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(
        CollaborationRoleAssignmentState(
            role_id=_string(mapping.get("role_id")),
            agent_id=_string(mapping.get("agent_id")),
            provider=_string(mapping.get("provider")),
            display_name=_string(mapping.get("display_name")),
            status=_string(mapping.get("status")) or "unknown",
            source=_string(mapping.get("source")),
            session_name=_string(mapping.get("session_name")),
            live=_bool(mapping.get("live")),
        )
        for row in value
        if (mapping := _mapping(row)) and _string(mapping.get("role_id"))
    )


def _participants_from_value(
    value: object,
) -> tuple[CollaborationParticipantState, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(
        CollaborationParticipantState(
            agent_id=_string(mapping.get("agent_id")),
            provider=_string(mapping.get("provider")),
            display_name=_string(mapping.get("display_name"))
            or _string(mapping.get("agent_id")),
            role=_string(mapping.get("role")),
            session_name=_string(mapping.get("session_name")),
            live=_bool(mapping.get("live")),
            status=_string(mapping.get("status")) or "unknown",
            capture_mode=_string(mapping.get("capture_mode")),
            approval_mode=_string(mapping.get("approval_mode")),
            supervision_mode=_string(mapping.get("supervision_mode")),
            prepared_at=_string(mapping.get("prepared_at")),
            metadata_path=_string(mapping.get("metadata_path")),
            log_path=_string(mapping.get("log_path")),
            launch_command=_string(mapping.get("launch_command")),
            requested_worker_budget=_optional_int(
                mapping.get("requested_worker_budget")
            ),
            planned_lane_count=_int(mapping.get("planned_lane_count")),
        )
        for row in value
        if (mapping := _mapping(row)) and _string(mapping.get("agent_id"))
    )


def _delegated_work_from_value(
    value: object,
) -> tuple[DelegatedWorkReceiptState, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(
        DelegatedWorkReceiptState(
            receipt_id=_string(mapping.get("receipt_id")),
            agent_id=_string(mapping.get("agent_id")),
            provider=_string(mapping.get("provider")),
            role=_string(mapping.get("role")),
            owner_session=_string(mapping.get("owner_session")),
            source=_string(mapping.get("source")),
            status=_string(mapping.get("status")) or "unknown",
            lane=_string(mapping.get("lane")),
            mp_scope=_string(mapping.get("mp_scope")),
            worktree=_string(mapping.get("worktree")),
            branch=_string(mapping.get("branch")),
            live=_bool(mapping.get("live")),
        )
        for row in value
        if (mapping := _mapping(row)) and _string(mapping.get("receipt_id"))
    )


def _legacy_collaboration_state(
    *,
    review: Mapping[str, object],
    current_session: ReviewCurrentSessionState,
    bridge: ReviewBridgeState,
    registry: AgentRegistryState,
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
        session_id=_string(review.get("session_id")) or "review-channel",
        plan_id=_string(review.get("plan_id")),
        status="live" if has_runtime else "resumable" if has_context else "inactive",
        reviewer_mode=bridge.effective_reviewer_mode or bridge.reviewer_mode,
        operator_mode="manual",
        lead_agent=_legacy_agent_for_role(role_assignments, "lead_agent"),
        review_agent=_legacy_agent_for_role(role_assignments, "review_agent"),
        coding_agent=_legacy_agent_for_role(role_assignments, "coding_agent"),
        current_slice=current_session.current_instruction or current_session.last_reviewed_scope,
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
        "blocked" if bridge.review_needed or bridge.reviewed_hash_current is False else "ready"
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


def _capability_provider(capability: object, *, default: str) -> str:
    provider = getattr(capability, "provider", "")
    return str(provider or "").strip() or default


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return _int(value)
