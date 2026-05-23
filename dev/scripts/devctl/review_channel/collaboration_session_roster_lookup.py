"""Lookup helpers for collaboration-session roster projection."""

from __future__ import annotations

from ..runtime.review_state_models import CollaborationRoleAssignmentState
from ..runtime.reviewer_runtime_models import (
    RemoteControlAttachmentState,
    has_active_remote_control_attachment,
)
from ..runtime.role_profile import normalize_role_id, role_capability_classes
from .session_probe import ConductorSessionRecord


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
    record = next((row for row in session_records if row.provider == provider), None)
    attachment = active_attachment_by_provider(remote_attachments).get(provider)
    normalized_role_id = normalize_role_id(role_id)
    if attachment is not None and attachment_matches_role(
        attachment,
        expected_role_id=normalized_role_id,
    ):
        session_name = attachment.session_name or f"{provider}-remote-control"
        return CollaborationRoleAssignmentState(
            role_id=normalized_role_id,
            agent_id=provider,
            provider=provider,
            display_name=display_name,
            status="live",
            source="remote_control_attachment",
            session_name=session_name,
            live=True,
        )
    if attachment is not None:
        return CollaborationRoleAssignmentState(
            role_id=normalized_role_id,
            agent_id=provider,
            provider=provider,
            display_name=display_name,
            status="configured",
            source="remote_control_attachment",
            session_name=attachment.session_name or f"{provider}-remote-control",
            live=False,
        )
    if record is not None and record_role(record) == normalized_role_id:
        return CollaborationRoleAssignmentState(
            role_id=normalized_role_id,
            agent_id=provider,
            provider=provider,
            display_name=display_name,
            status="live" if record.live else "configured",
            source="session_metadata",
            session_name=record.session_name,
            live=record.live,
        )
    if record is None:
        return CollaborationRoleAssignmentState(
            role_id=normalized_role_id,
            agent_id=provider,
            provider=provider,
            display_name=display_name,
            status="declared",
            source="typed_role_declaration",
        )
    return CollaborationRoleAssignmentState(
        role_id=normalized_role_id,
        agent_id=provider,
        provider=provider,
        display_name=display_name,
        status="configured",
        source="session_metadata",
        session_name=record.session_name,
        live=False,
    )


def text(value: object) -> str:
    return str(value or "").strip()


def record_role(record) -> str:
    return normalize_role_id(record.role)


def attachment_matches_role(
    attachment: RemoteControlAttachmentState,
    *,
    expected_role_id: str,
) -> bool:
    normalized = normalize_role_id(attachment.role)
    expected = normalize_role_id(expected_role_id)
    if not normalized or not expected:
        return False
    if normalized == expected:
        return True
    return bool(
        set(role_capability_classes(normalized))
        & set(role_capability_classes(expected))
    )
