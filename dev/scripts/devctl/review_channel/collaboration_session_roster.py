"""Roster and role-assignment builders for collaboration-session state."""

from __future__ import annotations

from ..runtime.review_state_models import (
    CollaborationParticipantState,
    CollaborationRoleAssignmentState,
    DelegatedWorkReceiptState,
)
from ..runtime.reviewer_runtime_models import (
    RemoteControlAttachmentState,
    has_active_remote_control_attachment,
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
    *,
    remote_attachments: tuple[RemoteControlAttachmentState, ...] = (),
) -> tuple[CollaborationParticipantState, ...]:
    attachment_by_provider = _active_attachment_by_provider(remote_attachments)
    participants: list[CollaborationParticipantState] = []
    seen_providers: set[str] = set()
    for record in session_records:
        attachment = attachment_by_provider.pop(record.provider, None)
        participants.append(
            _participant_from_record(
                record,
                attachment=attachment,
            )
        )
        seen_providers.add(record.provider)
    for provider, attachment in attachment_by_provider.items():
        if provider in seen_providers:
            continue
        participants.append(_participant_from_attachment(attachment))
    return tuple(participants)


def _build_role_assignments(
    session_records: tuple[ConductorSessionRecord, ...],
    *,
    remote_attachments: tuple[RemoteControlAttachmentState, ...] = (),
) -> tuple[CollaborationRoleAssignmentState, ...]:
    active_attachments = _active_attachment_by_provider(remote_attachments)
    default_profile = build_default_tandem_profile()
    reviewer_provider = _provider_for_role(
        session_records,
        TandemRole.REVIEWER,
    ) or _provider_for_remote_role(
        active_attachments,
        TandemRole.REVIEWER,
    ) or default_profile.reviewer.provider
    implementer_providers = _providers_for_role(
        session_records,
        TandemRole.IMPLEMENTER,
    ) or _providers_for_remote_role(
        active_attachments,
        TandemRole.IMPLEMENTER,
    ) or tuple(item.provider for item in default_profile.implementers)
    operator_provider = _provider_for_role(
        session_records,
        TandemRole.OPERATOR,
    ) or _provider_for_remote_role(
        active_attachments,
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
            remote_attachments=tuple(active_attachments.values()),
        ),
        _role_assignment(
            "review_agent",
            profile.reviewer.provider,
            profile.reviewer.display_name,
            session_records,
            remote_attachments=tuple(active_attachments.values()),
        ),
        _role_assignment(
            "coding_agent",
            profile.implementers[0].provider,
            profile.implementers[0].display_name,
            session_records,
            remote_attachments=tuple(active_attachments.values()),
        ),
        _role_assignment(
            "operator_agent",
            profile.operator.provider,
            profile.operator.display_name,
            session_records,
            remote_attachments=tuple(active_attachments.values()),
        ),
    )


def _role_assignment(
    role_id: str,
    provider: str,
    display_name: str,
    session_records: tuple[ConductorSessionRecord, ...],
    *,
    remote_attachments: tuple[RemoteControlAttachmentState, ...] = (),
) -> CollaborationRoleAssignmentState:
    attachment = _active_attachment_by_provider(remote_attachments).get(provider)
    expected_role = _role_for_role_id(role_id)
    if attachment is not None and _attachment_matches_role(
        attachment,
        expected_role=expected_role,
    ):
        session_name = attachment.session_name or f"{provider}-remote-control"
        return CollaborationRoleAssignmentState(
            role_id=role_id,
            agent_id=provider,
            provider=provider,
            display_name=display_name,
            status="live",
            source="remote_control_attachment",
            session_name=session_name,
            live=True,
        )
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


def _primary_lane_fields(record: ConductorSessionRecord) -> tuple[str, str, str, str]:
    if not record.planned_lanes:
        return "", "", "", ""
    lane = record.planned_lanes[0]
    return (
        _text(lane.get("lane")),
        _text(lane.get("mp_scope")),
        _text(lane.get("worktree")),
        _text(lane.get("branch")),
    )


def _participant_from_record(
    record: ConductorSessionRecord,
    *,
    attachment: RemoteControlAttachmentState | None,
) -> CollaborationParticipantState:
    lane_title, mp_scope, worktree, branch = _primary_lane_fields(record)
    if attachment is None:
        return CollaborationParticipantState(
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
            lane=lane_title,
            mp_scope=mp_scope,
            worktree=worktree,
            branch=branch,
            workspace_root=record.workspace_root,
        )
    return CollaborationParticipantState(
        agent_id=record.provider,
        provider=record.provider,
        display_name=record.provider_name,
        role=attachment.role or record.role or role_for_provider(record.provider).value,
        session_name=attachment.session_name or record.session_name or f"{record.provider}-remote-control",
        live=True,
        status="live",
        capture_mode="remote-control",
        approval_mode=record.approval_mode,
        supervision_mode="remote-control",
        prepared_at=attachment.attached_at_utc or record.prepared_at,
        metadata_path=attachment.metadata_path or record.metadata_path,
        log_path=record.log_path,
        launch_command=attachment.session_url or record.launch_command,
        requested_worker_budget=record.requested_worker_budget,
        planned_lane_count=record.planned_lane_count,
        lane=lane_title,
        mp_scope=mp_scope,
        worktree=worktree,
        branch=branch,
        workspace_root=record.workspace_root,
    )


def _participant_from_attachment(
    attachment: RemoteControlAttachmentState,
) -> CollaborationParticipantState:
    provider = attachment.provider or "remote"
    return CollaborationParticipantState(
        agent_id=provider,
        provider=provider,
        display_name=provider.title(),
        role=attachment.role or role_for_provider(provider).value,
        session_name=attachment.session_name or f"{provider}-remote-control",
        live=True,
        status="live",
        capture_mode="remote-control",
        approval_mode="balanced",
        supervision_mode="remote-control",
        prepared_at=attachment.attached_at_utc,
        metadata_path=attachment.metadata_path,
        log_path="",
        launch_command=attachment.session_url,
        requested_worker_budget=0,
        planned_lane_count=0,
        workspace_root="",
    )


def _active_attachment_by_provider(
    remote_attachments: tuple[RemoteControlAttachmentState, ...],
) -> dict[str, RemoteControlAttachmentState]:
    attachments: dict[str, RemoteControlAttachmentState] = {}
    for attachment in remote_attachments:
        provider = _text(attachment.provider)
        if not provider or not has_active_remote_control_attachment(attachment):
            continue
        attachments[provider] = attachment
    return attachments


def _provider_for_remote_role(
    remote_attachments: dict[str, RemoteControlAttachmentState],
    role: TandemRole,
) -> tuple[str, ...] | str | None:
    providers = tuple(
        provider
        for provider, attachment in remote_attachments.items()
        if _attachment_matches_role(attachment, expected_role=role)
    )
    if role == TandemRole.IMPLEMENTER:
        return providers or None
    return providers[0] if providers else None


def _providers_for_remote_role(
    remote_attachments: dict[str, RemoteControlAttachmentState],
    role: TandemRole,
) -> tuple[str, ...]:
    providers = _provider_for_remote_role(remote_attachments, role)
    if isinstance(providers, tuple):
        return providers
    if isinstance(providers, str) and providers:
        return (providers,)
    return ()


def _attachment_matches_role(
    attachment: RemoteControlAttachmentState,
    *,
    expected_role: TandemRole,
) -> bool:
    normalized = normalize_tandem_role(attachment.role)
    return normalized == expected_role


def _role_for_role_id(role_id: str) -> TandemRole:
    if role_id in {"lead_agent", "review_agent"}:
        return TandemRole.REVIEWER
    if role_id == "coding_agent":
        return TandemRole.IMPLEMENTER
    if role_id == "operator_agent":
        return TandemRole.OPERATOR
    return TandemRole.IMPLEMENTER
