"""Roster and role-assignment builders for collaboration-session state."""

from __future__ import annotations

from ..runtime.review_state_models import (
    CollaborationParticipantState,
    CollaborationRoleAssignmentState,
    DelegatedWorkReceiptState,
)
from ..runtime.role_profile import (
    TandemRole,
    build_default_tandem_profile,
    normalize_tandem_role,
    role_for_provider,
)
from .session_probe import ConductorSessionRecord


def _build_participants(
    session_records: tuple[ConductorSessionRecord, ...],
) -> tuple[CollaborationParticipantState, ...]:
    return tuple(
        CollaborationParticipantState(
            agent_id=record.provider,
            provider=record.provider,
            display_name=record.provider_name,
            role=record.role or role_for_provider(record.provider).value,
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
    reviewer_provider = _provider_for_role(
        session_records,
        TandemRole.REVIEWER,
    ) or default_profile.reviewer.provider
    implementer_providers = _providers_for_role(
        session_records,
        TandemRole.IMPLEMENTER,
    ) or tuple(item.provider for item in default_profile.implementers)
    operator_provider = _provider_for_role(
        session_records,
        TandemRole.OPERATOR,
    ) or default_profile.operator.provider
    profile = build_default_tandem_profile(
        reviewer_provider=reviewer_provider,
        implementer_providers=implementer_providers,
        operator_provider=operator_provider,
    )
    return (
        _role_assignment(
            "lead_agent",
            profile.reviewer.provider,
            profile.reviewer.display_name,
            session_records,
        ),
        _role_assignment(
            "review_agent",
            profile.reviewer.provider,
            profile.reviewer.display_name,
            session_records,
        ),
        _role_assignment(
            "coding_agent",
            profile.implementers[0].provider,
            profile.implementers[0].display_name,
            session_records,
        ),
        _role_assignment(
            "operator_agent",
            profile.operator.provider,
            profile.operator.display_name,
            session_records,
        ),
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
                    role=_planned_lane_role(lane, provider=provider).value,
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


def _provider_for_role(
    session_records: tuple[ConductorSessionRecord, ...],
    role: TandemRole,
) -> str | None:
    for record in session_records:
        if _record_role(record) == role:
            return record.provider
    return None


def _providers_for_role(
    session_records: tuple[ConductorSessionRecord, ...],
    role: TandemRole,
) -> tuple[str, ...]:
    return tuple(
        record.provider
        for record in session_records
        if _record_role(record) == role
    )


def _text(value: object) -> str:
    return str(value or "").strip()


def _record_role(record: ConductorSessionRecord) -> TandemRole:
    return normalize_tandem_role(record.role) or role_for_provider(record.provider)


def _planned_lane_role(lane: dict[str, object], *, provider: str) -> TandemRole:
    return normalize_tandem_role(_text(lane.get("role"))) or role_for_provider(provider)
