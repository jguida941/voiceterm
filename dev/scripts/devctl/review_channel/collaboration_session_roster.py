"""Roster and role-assignment builders for collaboration-session state."""

from __future__ import annotations

from ..runtime.review_state_models import (
    CollaborationParticipantState,
    CollaborationRoleAssignmentState,
    DelegatedWorkReceiptState,
)
from ..runtime.reviewer_runtime_models import (
    RemoteControlAttachmentState,
)
from ..runtime.role_profile import (
    TandemRole,
    build_default_tandem_profile,
)
from .collaboration_session_roster_lookup import (
    active_attachment_by_provider as _active_attachment_by_provider,
    attachment_matches_role as _attachment_matches_role,
    has_active_remote_operator as _has_active_remote_operator,
    role_assignment as _role_assignment,
    text as _text,
)
from .collaboration_session_roster_projection import (
    participant_from_attachment as _participant_from_attachment,
    participant_from_record as _participant_from_record,
    planned_lane_role as _planned_lane_role,
)
from .collaboration_session_roster_resolution import (
    provider_for_remote_role as _provider_for_remote_role,
    provider_for_role as _provider_for_role,
    providers_for_remote_role as _providers_for_remote_role,
    providers_for_role as _providers_for_role,
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
    reviewer_mode: str = "",
) -> tuple[CollaborationRoleAssignmentState, ...]:
    active_attachments = _active_attachment_by_provider(remote_attachments)
    default_profile = build_default_tandem_profile()
    reviewer_provider = _provider_for_role(
        session_records,
        TandemRole.REVIEWER,
        live_only=True,
    ) or _provider_for_remote_role(
        active_attachments,
        TandemRole.REVIEWER,
    ) or _provider_for_role(
        session_records,
        TandemRole.REVIEWER,
    ) or default_profile.reviewer.provider
    live_implementer_providers = _providers_for_role(
        session_records,
        TandemRole.IMPLEMENTER,
        live_only=True,
    ) or _providers_for_remote_role(
        active_attachments,
        TandemRole.IMPLEMENTER,
    )
    if live_implementer_providers:
        implementer_providers = live_implementer_providers
    elif (
        reviewer_mode == "single_agent"
        and reviewer_provider
        and _has_active_remote_operator(active_attachments)
    ):
        implementer_providers = (reviewer_provider,)
    else:
        implementer_providers = _providers_for_role(
            session_records,
            TandemRole.IMPLEMENTER,
        ) or tuple(item.provider for item in default_profile.implementers)
    operator_provider = _provider_for_role(
        session_records,
        TandemRole.OPERATOR,
        live_only=True,
    ) or _provider_for_remote_role(
        active_attachments,
        TandemRole.OPERATOR,
    ) or _provider_for_role(
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
