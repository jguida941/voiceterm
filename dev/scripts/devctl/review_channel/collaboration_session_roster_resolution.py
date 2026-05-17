"""Role-resolution helpers for collaboration-session roster."""

from __future__ import annotations

from ..runtime.reviewer_runtime_models import RemoteControlAttachmentState
from ..runtime.role_profile import TandemRole
from .collaboration_session_roster_lookup import attachment_matches_role, record_role
from .session_probe import ConductorSessionRecord


def provider_for_role(
    session_records: tuple[ConductorSessionRecord, ...],
    role: TandemRole,
    *,
    live_only: bool = False,
) -> str | None:
    for record in session_records:
        if live_only and not record.live:
            continue
        if record_role(record) == role:
            return record.provider
    return None


def providers_for_role(
    session_records: tuple[ConductorSessionRecord, ...],
    role: TandemRole,
    *,
    live_only: bool = False,
) -> tuple[str, ...]:
    return tuple(
        record.provider
        for record in session_records
        if (record.live or not live_only)
        if record_role(record) == role
    )


def provider_for_remote_role(
    remote_attachments: dict[str, RemoteControlAttachmentState],
    role: TandemRole,
) -> tuple[str, ...] | str | None:
    providers = tuple(
        provider
        for provider, attachment in remote_attachments.items()
        if attachment_matches_role(attachment, expected_role=role)
    )
    if role == TandemRole.IMPLEMENTER:
        return providers or None
    return providers[0] if providers else None


def providers_for_remote_role(
    remote_attachments: dict[str, RemoteControlAttachmentState],
    role: TandemRole,
) -> tuple[str, ...]:
    providers = provider_for_remote_role(remote_attachments, role)
    if isinstance(providers, tuple):
        return providers
    if isinstance(providers, str) and providers:
        return (providers,)
    return ()
