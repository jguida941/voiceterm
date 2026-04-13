"""Lookup helpers for collaboration-session roster projection."""

from __future__ import annotations

from ..runtime.review_state_models import CollaborationRoleAssignmentState
from ..runtime.reviewer_runtime_models import (
    RemoteControlAttachmentState,
    has_active_remote_control_attachment,
)
from ..runtime.role_profile import (
    TandemRole,
    normalize_tandem_role,
    role_for_provider,
)
def active_attachment_by_provider(
    remote_attachments: tuple[RemoteControlAttachmentState, ...],
) -> dict[str, RemoteControlAttachmentState]:
    attachments: dict[str, RemoteControlAttachmentState] = {}
    for attachment in remote_attachments:
        provider = text(attachment.provider)
        if not provider or not has_active_remote_control_attachment(attachment):
            continue
        attachments[provider] = attachment
    return attachments


def role_assignment(
    role_id: str,
    provider: str,
    display_name: str,
    session_records: tuple[ConductorSessionRecord, ...],
    *,
    remote_attachments: tuple[RemoteControlAttachmentState, ...] = (),
) -> CollaborationRoleAssignmentState:
    attachment = active_attachment_by_provider(remote_attachments).get(provider)
    expected_role = role_for_role_id(role_id)
    if attachment is not None and attachment_matches_role(
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


def text(value: object) -> str:
    return str(value or "").strip()


def record_role(record) -> TandemRole:
    return normalize_tandem_role(record.role) or role_for_provider(record.provider)


def attachment_matches_role(
    attachment: RemoteControlAttachmentState,
    *,
    expected_role: TandemRole,
) -> bool:
    normalized = normalize_tandem_role(attachment.role)
    return normalized == expected_role


def has_active_remote_operator(
    remote_attachments: dict[str, RemoteControlAttachmentState],
) -> bool:
    return any(
        attachment_matches_role(attachment, expected_role=TandemRole.OPERATOR)
        for attachment in remote_attachments.values()
    )


def role_for_role_id(role_id: str) -> TandemRole:
    if role_id in {"lead_agent", "review_agent"}:
        return TandemRole.REVIEWER
    if role_id == "coding_agent":
        return TandemRole.IMPLEMENTER
    if role_id == "operator_agent":
        return TandemRole.OPERATOR
    return TandemRole.IMPLEMENTER
