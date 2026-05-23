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
from ..runtime.role_profile import normalize_role_id, role_capability_classes
from .collaboration_session_roster_lookup import (
    active_attachment_by_provider as _active_attachment_by_provider,
    role_assignment as _role_assignment,
    text as _text,
)
from .collaboration_session_roster_projection import (
    participant_from_attachment as _participant_from_attachment,
    participant_from_record as _participant_from_record,
    planned_lane_role as _planned_lane_role,
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
    assignments: list[CollaborationRoleAssignmentState] = []
    seen: set[tuple[str, str]] = set()
    attachment_rows = tuple(active_attachments.values())

    def append_role(role_id: object, provider: object, display_name: object = "") -> None:
        normalized_role = _collaboration_role_id(role_id)
        normalized_provider = _text(provider).lower()
        if not normalized_role or not normalized_provider:
            return
        key = (normalized_role, normalized_provider)
        if key in seen:
            return
        seen.add(key)
        assignments.append(
            _role_assignment(
                normalized_role,
                normalized_provider,
                _text(display_name) or normalized_provider.title(),
                session_records,
                remote_attachments=attachment_rows,
            )
        )

    for record in session_records:
        append_role(record.role, record.provider, record.provider_name)
        if (
            reviewer_mode == "single_agent"
            and _collaboration_role_id(record.role) == "review_agent"
        ):
            append_role("coding_agent", record.provider, record.provider_name)
        for lane in record.planned_lanes:
            append_role(
                _planned_lane_role(lane, provider=record.provider),
                _text(lane.get("provider")) or record.provider,
                _text(lane.get("display_name")),
            )
    for provider, attachment in active_attachments.items():
        append_role(attachment.role, provider, provider.title())
    return tuple(assignments)


def _collaboration_role_id(role_id: object) -> str:
    normalized_role = normalize_role_id(role_id)
    capability_classes = set(role_capability_classes(normalized_role))
    if capability_classes & {"implementation", "mutation"}:
        return "coding_agent"
    if capability_classes & {
        "review",
        "architecture",
        "governance",
        "research",
        "test",
        "intake",
    }:
        return "review_agent"
    if capability_classes & {"control", "observe"}:
        return "operator_agent"
    return normalized_role


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
                    role=_planned_lane_role(lane, provider=provider),
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
