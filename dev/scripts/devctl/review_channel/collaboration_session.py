"""Builders for the typed collaboration-session review-state contract."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ..runtime.review_state_models import (
    CollaborationArbitrationState,
    CollaborationParticipantState,
    CollaborationPeerReviewState,
    CollaborationReadyGateState,
    CollaborationRestartState,
    CollaborationRoleAssignmentState,
    CollaborationSessionState,
    DelegatedWorkReceiptState,
    ReviewCurrentSessionState,
)
from ..runtime.role_profile import TandemRole, build_default_tandem_profile, role_for_provider
from .session_probe import ConductorSessionRecord, load_conductor_sessions


def build_collaboration_session(
    *,
    timestamp: str,
    plan_id: str,
    session_id: str,
    bridge_liveness: Mapping[str, object],
    current_session: ReviewCurrentSessionState,
    attention: Mapping[str, object] | None = None,
    session_output_root: Path | None = None,
) -> CollaborationSessionState:
    """Build the typed collaboration/session state for review-channel runtime."""
    session_records = (
        load_conductor_sessions(session_output_root=session_output_root)
        if session_output_root is not None
        else ()
    )
    participants = _build_participants(session_records)
    role_assignments = _build_role_assignments(session_records)
    delegated_work = _build_delegated_work(session_records)
    peer_review = CollaborationPeerReviewState(
        current_instruction=current_session.current_instruction,
        current_instruction_revision=current_session.current_instruction_revision,
        open_findings=current_session.open_findings,
        implementer_status=current_session.implementer_status,
        implementer_ack=current_session.implementer_ack,
        implementer_ack_state=current_session.implementer_ack_state,
        implementer_state_hash=current_session.implementer_state_hash,
        last_reviewed_scope=current_session.last_reviewed_scope,
    )
    reviewer_mode = _text(bridge_liveness.get("reviewer_mode")) or "tools_only"
    effective_mode = _text(bridge_liveness.get("effective_reviewer_mode")) or reviewer_mode
    current_slice = current_session.current_instruction or current_session.last_reviewed_scope
    return CollaborationSessionState(
        schema_version=1,
        contract_id="CollaborationSession",
        session_id=session_id or "review-channel",
        plan_id=plan_id,
        status=_collaboration_status(
            participants=participants,
            delegated_work=delegated_work,
            current_session=current_session,
        ),
        reviewer_mode=effective_mode,
        operator_mode=_operator_mode(attention),
        lead_agent=_agent_for_role(role_assignments, "lead_agent"),
        review_agent=_agent_for_role(role_assignments, "review_agent"),
        coding_agent=_agent_for_role(role_assignments, "coding_agent"),
        current_slice=current_slice,
        peer_review=peer_review,
        arbitration=_build_arbitration(attention),
        restart=_build_restart_state(
            participants=participants,
            delegated_work=delegated_work,
            bridge_liveness=bridge_liveness,
            reviewer_mode=reviewer_mode,
            effective_mode=effective_mode,
            current_session=current_session,
        ),
        ready_gates=_build_ready_gates(
            participants=participants,
            delegated_work=delegated_work,
            session_records=session_records,
            bridge_liveness=bridge_liveness,
            reviewer_mode=effective_mode,
            current_session=current_session,
        ),
        role_assignments=role_assignments,
        participants=participants,
        delegated_work=delegated_work,
    )


def _build_participants(
    session_records: tuple[ConductorSessionRecord, ...],
) -> tuple[CollaborationParticipantState, ...]:
    return tuple(
        CollaborationParticipantState(
            agent_id=record.provider,
            provider=record.provider,
            display_name=record.provider_name,
            role=role_for_provider(record.provider).value,
            session_name=record.session_name,
            live=record.live,
            status="live" if record.live else "configured",
            capture_mode=record.capture_mode,
            approval_mode=record.approval_mode,
            supervision_mode=record.supervision_mode,
            prepared_at=record.prepared_at,
            metadata_path=record.metadata_path,
            log_path=record.log_path,
            launch_command=record.launch_command,
            requested_worker_budget=record.requested_worker_budget,
            planned_lane_count=record.planned_lane_count,
        )
        for record in session_records
    )


def _build_role_assignments(
    session_records: tuple[ConductorSessionRecord, ...],
) -> tuple[CollaborationRoleAssignmentState, ...]:
    default_profile = build_default_tandem_profile()
    reviewer_provider = _provider_for_role(session_records, TandemRole.REVIEWER) or default_profile.reviewer.provider
    implementer_providers = _providers_for_role(
        session_records,
        TandemRole.IMPLEMENTER,
    ) or tuple(item.provider for item in default_profile.implementers)
    operator_provider = _provider_for_role(session_records, TandemRole.OPERATOR) or default_profile.operator.provider
    profile = build_default_tandem_profile(
        reviewer_provider=reviewer_provider,
        implementer_providers=implementer_providers,
        operator_provider=operator_provider,
    )
    return (
        _role_assignment("lead_agent", profile.reviewer.provider, profile.reviewer.display_name, session_records),
        _role_assignment("review_agent", profile.reviewer.provider, profile.reviewer.display_name, session_records),
        _role_assignment(
            "coding_agent",
            profile.implementers[0].provider,
            profile.implementers[0].display_name,
            session_records,
        ),
        _role_assignment("operator_agent", profile.operator.provider, profile.operator.display_name, session_records),
    )


def _role_assignment(
    role_id: str,
    provider: str,
    display_name: str,
    session_records: tuple[ConductorSessionRecord, ...],
) -> CollaborationRoleAssignmentState:
    record = next((row for row in session_records if row.provider == provider), None)
    if record is None:
        return CollaborationRoleAssignmentState(
            role_id=role_id,
            agent_id=provider,
            provider=provider,
            display_name=display_name,
            status="declared",
            source="compatibility_profile",
        )
    return CollaborationRoleAssignmentState(
        role_id=role_id,
        agent_id=provider,
        provider=provider,
        display_name=display_name,
        status="live" if record.live else "configured",
        source="session_metadata",
        session_name=record.session_name,
        live=record.live,
    )


def _build_delegated_work(
    session_records: tuple[ConductorSessionRecord, ...],
) -> tuple[DelegatedWorkReceiptState, ...]:
    receipts: list[DelegatedWorkReceiptState] = []
    for record in session_records:
        for index, lane in enumerate(record.planned_lanes, start=1):
            provider = _text(lane.get("provider")) or record.provider
            agent_id = _text(lane.get("agent_id")) or f"{record.session_name}-lane-{index}"
            receipts.append(
                DelegatedWorkReceiptState(
                    receipt_id=f"{record.session_name}:{agent_id}",
                    agent_id=agent_id,
                    provider=provider,
                    role=role_for_provider(provider).value,
                    owner_session=record.session_name,
                    source="session_metadata",
                    status="planned",
                    lane=_text(lane.get("lane")),
                    mp_scope=_text(lane.get("mp_scope")),
                    worktree=_text(lane.get("worktree")),
                    branch=_text(lane.get("branch")),
                    live=False,
                )
            )
    return tuple(receipts)


def _build_arbitration(
    attention: Mapping[str, object] | None,
) -> CollaborationArbitrationState:
    if not isinstance(attention, Mapping):
        return CollaborationArbitrationState(status="clear", summary="", owner="")
    owner = _text(attention.get("owner"))
    summary = _text(attention.get("summary"))
    if owner == "operator" and summary:
        return CollaborationArbitrationState(
            status="operator_attention",
            summary=summary,
            owner=owner,
        )
    if owner and owner != "system" and summary:
        return CollaborationArbitrationState(
            status="attention",
            summary=summary,
            owner=owner,
        )
    return CollaborationArbitrationState(status="clear", summary="", owner=owner)


def _build_restart_state(
    *,
    participants: tuple[CollaborationParticipantState, ...],
    delegated_work: tuple[DelegatedWorkReceiptState, ...],
    bridge_liveness: Mapping[str, object],
    reviewer_mode: str,
    effective_mode: str,
    current_session: ReviewCurrentSessionState,
) -> CollaborationRestartState:
    if any(participant.live for participant in participants):
        status = "live"
        source = "session_metadata"
    elif participants or delegated_work:
        status = "resumable"
        source = "session_metadata"
    elif current_session.current_instruction or current_session.open_findings:
        status = "handoff_only"
        source = "review_state"
    else:
        status = "fresh_start"
        source = ""
    return CollaborationRestartState(
        status=status,
        resumable=status != "fresh_start",
        source=source,
        launch_truth=_text(bridge_liveness.get("launch_truth")),
        reviewer_mode=reviewer_mode,
        effective_reviewer_mode=effective_mode,
        last_codex_poll_utc=_text(bridge_liveness.get("last_codex_poll_utc")),
        last_worktree_hash=_text(bridge_liveness.get("last_worktree_hash")),
    )


def _build_ready_gates(
    *,
    participants: tuple[CollaborationParticipantState, ...],
    delegated_work: tuple[DelegatedWorkReceiptState, ...],
    session_records: tuple[ConductorSessionRecord, ...],
    bridge_liveness: Mapping[str, object],
    reviewer_mode: str,
    current_session: ReviewCurrentSessionState,
) -> tuple[CollaborationReadyGateState, ...]:
    return (
        CollaborationReadyGateState(
            gate_id="runtime_truth",
            status=_runtime_gate_status(reviewer_mode, participants),
            summary=_runtime_gate_summary(reviewer_mode, participants),
        ),
        CollaborationReadyGateState(
            gate_id="review_truth",
            status=_review_gate_status(bridge_liveness),
            summary=_review_gate_summary(bridge_liveness),
        ),
        CollaborationReadyGateState(
            gate_id="implementer_state",
            status=_implementer_gate_status(current_session),
            summary=_implementer_gate_summary(current_session),
        ),
        CollaborationReadyGateState(
            gate_id="delegated_work",
            status=_delegated_gate_status(session_records, delegated_work),
            summary=_delegated_gate_summary(session_records, delegated_work),
        ),
    )


def _runtime_gate_status(
    reviewer_mode: str,
    participants: tuple[CollaborationParticipantState, ...],
) -> str:
    if reviewer_mode != "active_dual_agent":
        return "not_required"
    reviewer_live = any(
        participant.live and participant.role == TandemRole.REVIEWER.value
        for participant in participants
    )
    implementer_live = any(
        participant.live and participant.role == TandemRole.IMPLEMENTER.value
        for participant in participants
    )
    return "ready" if reviewer_live and implementer_live else "blocked"


def _runtime_gate_summary(
    reviewer_mode: str,
    participants: tuple[CollaborationParticipantState, ...],
) -> str:
    if reviewer_mode != "active_dual_agent":
        return f"Reviewer mode `{reviewer_mode}` does not require live dual-agent conductors."
    live_roles = sorted(
        participant.role
        for participant in participants
        if participant.live
    )
    if len(live_roles) >= 2:
        return "Live reviewer and implementer conductor sessions are present."
    return "Active dual-agent mode still requires live reviewer and implementer conductor sessions."


def _review_gate_status(bridge_liveness: Mapping[str, object]) -> str:
    if bridge_liveness.get("review_needed") or bridge_liveness.get("reviewed_hash_current") is False:
        return "blocked"
    return "ready"


def _review_gate_summary(bridge_liveness: Mapping[str, object]) -> str:
    if bridge_liveness.get("review_needed"):
        return "Reviewer follow-up is still required for the current worktree."
    if bridge_liveness.get("reviewed_hash_current") is False:
        return "The reviewed worktree hash is stale against the current tree."
    return "Reviewer truth is current for the visible worktree."


def _implementer_gate_status(current_session: ReviewCurrentSessionState) -> str:
    if not current_session.current_instruction:
        return "not_required"
    if current_session.implementer_ack_state == "current":
        return "ready"
    if current_session.implementer_ack_state in {"stale", "missing"}:
        return "blocked"
    return "pending"


def _implementer_gate_summary(current_session: ReviewCurrentSessionState) -> str:
    if not current_session.current_instruction:
        return "No active implementer instruction is present."
    if current_session.implementer_ack_state == "current":
        return "Implementer state matches the current instruction revision."
    return (
        "Implementer state has not acknowledged the current instruction revision yet."
    )


def _delegated_gate_status(
    session_records: tuple[ConductorSessionRecord, ...],
    delegated_work: tuple[DelegatedWorkReceiptState, ...],
) -> str:
    requested_budget = sum(max(record.requested_worker_budget or 0, 0) for record in session_records)
    if requested_budget <= 0:
        return "not_requested"
    if delegated_work:
        return "planned"
    return "pending"


def _delegated_gate_summary(
    session_records: tuple[ConductorSessionRecord, ...],
    delegated_work: tuple[DelegatedWorkReceiptState, ...],
) -> str:
    requested_budget = sum(max(record.requested_worker_budget or 0, 0) for record in session_records)
    if requested_budget <= 0:
        return "No worker fanout was requested for the current conductor sessions."
    if delegated_work:
        return f"{len(delegated_work)} delegated lane receipt(s) were recorded by conductor session metadata."
    return "Worker fanout was requested but no delegated lane receipts are available yet."


def _collaboration_status(
    *,
    participants: tuple[CollaborationParticipantState, ...],
    delegated_work: tuple[DelegatedWorkReceiptState, ...],
    current_session: ReviewCurrentSessionState,
) -> str:
    if any(participant.live for participant in participants):
        return "live"
    if participants or delegated_work:
        return "resumable"
    if current_session.current_instruction or current_session.open_findings:
        return "handoff_only"
    return "inactive"


def _operator_mode(attention: Mapping[str, object] | None) -> str:
    if not isinstance(attention, Mapping):
        return "manual"
    if _text(attention.get("owner")) == "operator":
        return "attention_required"
    return "manual"


def _agent_for_role(
    assignments: tuple[CollaborationRoleAssignmentState, ...],
    role_id: str,
) -> str:
    return next(
        (assignment.agent_id for assignment in assignments if assignment.role_id == role_id),
        "",
    )


def _provider_for_role(
    session_records: tuple[ConductorSessionRecord, ...],
    role: TandemRole,
) -> str | None:
    for record in session_records:
        if role_for_provider(record.provider) == role:
            return record.provider
    return None


def _providers_for_role(
    session_records: tuple[ConductorSessionRecord, ...],
    role: TandemRole,
) -> tuple[str, ...]:
    return tuple(
        record.provider
        for record in session_records
        if role_for_provider(record.provider) == role
    )


def _text(value: object) -> str:
    return str(value or "").strip()
