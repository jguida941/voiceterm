"""Builder for typed remote-control attachment state."""

from __future__ import annotations

from typing import NamedTuple

from .remote_control_attachment_models import (
    RemoteControlAttachmentState,
    int_or_default,
    session_id_from_url,
    slugify_timestamp,
)
from .remote_control_attachment_status import (
    ACTIVE_REMOTE_CONTROL_ATTACHMENT_STATUSES,
    DEFAULT_REMOTE_CONTROL_HEARTBEAT_TTL_SECONDS,
)

TRUSTED_PHYSICAL_CONFIRMATION_METHODS = frozenset(
    {"claude_hook_transcript", "claude_session_state_bridge"}
)


class RemoteControlAttachmentBuildInput(NamedTuple):
    now_utc: str
    provider: str
    role: str = "operator"
    status: str = "attached"
    session_name: str = ""
    remote_session_id: str = ""
    session_url: str = ""
    metadata_path: str = ""
    launcher_source: str = ""
    host_pid: int | None = None
    host_session_label: str = ""
    heartbeat_ttl_seconds: int | None = None
    previous_operator_mode: str = ""
    entrypoint: str = ""
    physical_remote_control_confirmed: bool = False
    physical_confirmation_method: str = "none"
    source_hook_event_name: str = ""
    source_hook_prompt: str = ""
    source_hook_command_name: str = ""
    source_hook_session_id: str = ""
    source_hook_transcript_path: str = ""
    source_hook_dedupe_key: str = ""
    source_proof_channel: str = ""
    source_proof_observed_at_utc: str = ""
    existing: RemoteControlAttachmentState | None = None
    refresh_existing_identity: bool = False


class _AttachmentFields(NamedTuple):
    provider: str
    role: str
    status: str
    session_name: str
    remote_session_id: str
    session_url: str
    metadata_path: str
    launcher_source: str
    host_pid: int | None
    host_session_label: str
    previous_operator_mode: str
    entrypoint: str
    physical_remote_control_confirmed: bool
    physical_confirmation_method: str
    source_hook_event_name: str
    source_hook_prompt: str
    source_hook_command_name: str
    source_hook_session_id: str
    source_hook_transcript_path: str
    source_hook_dedupe_key: str
    source_proof_channel: str
    source_proof_observed_at_utc: str


def build_remote_control_attachment_state(
    spec: RemoteControlAttachmentBuildInput,
) -> RemoteControlAttachmentState:
    """Canonical builder for ``RemoteControlAttachmentState`` upserts."""
    fields = _initial_fields(spec)
    same_attachment = _same_attachment(spec, fields)
    fields = _merge_existing_fields(spec, fields, same_attachment=same_attachment)
    fields = _clear_inactive_physical_state(fields)
    attachment_id, attached_at_utc = _attachment_identity(
        spec,
        same_attachment=same_attachment,
    )
    resolved_ttl = _resolved_ttl(spec)
    return RemoteControlAttachmentState(
        provider=fields.provider,
        role=fields.role,
        attachment_id=attachment_id,
        session_name=fields.session_name,
        remote_session_id=fields.remote_session_id,
        session_url=fields.session_url,
        status=fields.status,
        transport="review_channel_artifact",
        attached_at_utc=attached_at_utc,
        last_seen_utc=spec.now_utc,
        metadata_path=fields.metadata_path,
        launcher_source=fields.launcher_source,
        host_pid=fields.host_pid,
        host_session_label=fields.host_session_label,
        heartbeat_ttl_seconds=max(0, resolved_ttl),
        previous_operator_mode=fields.previous_operator_mode,
        entrypoint=fields.entrypoint,
        physical_remote_control_confirmed=fields.physical_remote_control_confirmed,
        physical_confirmation_method=fields.physical_confirmation_method,
        source_hook_event_name=fields.source_hook_event_name,
        source_hook_prompt=fields.source_hook_prompt,
        source_hook_command_name=fields.source_hook_command_name,
        source_hook_session_id=fields.source_hook_session_id,
        source_hook_transcript_path=fields.source_hook_transcript_path,
        source_hook_dedupe_key=fields.source_hook_dedupe_key,
        source_proof_channel=fields.source_proof_channel,
        source_proof_observed_at_utc=fields.source_proof_observed_at_utc,
    )


def _initial_fields(spec: RemoteControlAttachmentBuildInput) -> _AttachmentFields:
    remote_session_id = (spec.remote_session_id or "").strip()
    session_url = (spec.session_url or "").strip()
    if not remote_session_id:
        remote_session_id = session_id_from_url(session_url)
    method = (spec.physical_confirmation_method or "none").strip() or "none"
    return _AttachmentFields(
        provider=(spec.provider or "").strip(),
        role=(spec.role or "operator").strip(),
        status=(spec.status or "attached").strip(),
        session_name=(spec.session_name or "").strip(),
        remote_session_id=remote_session_id,
        session_url=session_url,
        metadata_path=(spec.metadata_path or "").strip(),
        launcher_source=(spec.launcher_source or "").strip(),
        host_pid=spec.host_pid,
        host_session_label=(spec.host_session_label or "").strip(),
        previous_operator_mode=(spec.previous_operator_mode or "").strip(),
        entrypoint=(spec.entrypoint or "").strip(),
        physical_remote_control_confirmed=(
            bool(spec.physical_remote_control_confirmed)
            and method in TRUSTED_PHYSICAL_CONFIRMATION_METHODS
        ),
        physical_confirmation_method=method,
        source_hook_event_name=(spec.source_hook_event_name or "").strip(),
        source_hook_prompt=(spec.source_hook_prompt or "").strip(),
        source_hook_command_name=(spec.source_hook_command_name or "").strip(),
        source_hook_session_id=(spec.source_hook_session_id or "").strip(),
        source_hook_transcript_path=(spec.source_hook_transcript_path or "").strip(),
        source_hook_dedupe_key=(spec.source_hook_dedupe_key or "").strip(),
        source_proof_channel=(spec.source_proof_channel or "").strip(),
        source_proof_observed_at_utc=(
            spec.source_proof_observed_at_utc or ""
        ).strip(),
    )


def _same_attachment(
    spec: RemoteControlAttachmentBuildInput,
    fields: _AttachmentFields,
) -> bool:
    existing = spec.existing
    if existing is None or existing.provider != fields.provider:
        return False
    return bool(
        (
            fields.remote_session_id
            and existing.remote_session_id == fields.remote_session_id
        )
        or (fields.session_url and existing.session_url == fields.session_url)
    )


def _merge_existing_fields(
    spec: RemoteControlAttachmentBuildInput,
    fields: _AttachmentFields,
    *,
    same_attachment: bool,
) -> _AttachmentFields:
    existing = spec.existing
    if existing is None:
        return fields
    remote_session_id = fields.remote_session_id
    session_url = fields.session_url
    identity_refresh_allowed = same_attachment or spec.refresh_existing_identity
    if identity_refresh_allowed:
        remote_session_id = remote_session_id or existing.remote_session_id
        session_url = session_url or existing.session_url
    physical_confirmed = fields.physical_remote_control_confirmed
    physical_method = fields.physical_confirmation_method
    if not physical_confirmed and identity_refresh_allowed:
        physical_confirmed = existing.physical_remote_control_confirmed
        physical_method = existing.physical_confirmation_method
    hook_event_name = fields.source_hook_event_name
    hook_prompt = fields.source_hook_prompt
    hook_command_name = fields.source_hook_command_name
    hook_session_id = fields.source_hook_session_id
    hook_transcript_path = fields.source_hook_transcript_path
    hook_dedupe_key = fields.source_hook_dedupe_key
    proof_channel = fields.source_proof_channel
    proof_observed_at = fields.source_proof_observed_at_utc
    if identity_refresh_allowed:
        hook_event_name = hook_event_name or existing.source_hook_event_name
        hook_prompt = hook_prompt or existing.source_hook_prompt
        hook_command_name = hook_command_name or existing.source_hook_command_name
        hook_session_id = hook_session_id or existing.source_hook_session_id
        hook_transcript_path = (
            hook_transcript_path or existing.source_hook_transcript_path
        )
        hook_dedupe_key = hook_dedupe_key or existing.source_hook_dedupe_key
        proof_channel = proof_channel or existing.source_proof_channel
        proof_observed_at = proof_observed_at or existing.source_proof_observed_at_utc
    return _AttachmentFields(
        provider=fields.provider,
        role=fields.role,
        status=fields.status,
        session_name=fields.session_name or existing.session_name,
        remote_session_id=remote_session_id,
        session_url=session_url,
        metadata_path=fields.metadata_path or existing.metadata_path,
        launcher_source=fields.launcher_source or existing.launcher_source,
        host_pid=fields.host_pid if fields.host_pid is not None else existing.host_pid,
        host_session_label=(
            fields.host_session_label or existing.host_session_label
        ),
        previous_operator_mode=(
            fields.previous_operator_mode or existing.previous_operator_mode
        ),
        entrypoint=fields.entrypoint or existing.entrypoint,
        physical_remote_control_confirmed=physical_confirmed,
        physical_confirmation_method=physical_method,
        source_hook_event_name=hook_event_name,
        source_hook_prompt=hook_prompt,
        source_hook_command_name=hook_command_name,
        source_hook_session_id=hook_session_id,
        source_hook_transcript_path=hook_transcript_path,
        source_hook_dedupe_key=hook_dedupe_key,
        source_proof_channel=proof_channel,
        source_proof_observed_at_utc=proof_observed_at,
    )


def _clear_inactive_physical_state(fields: _AttachmentFields) -> _AttachmentFields:
    if fields.status in ACTIVE_REMOTE_CONTROL_ATTACHMENT_STATUSES:
        return fields
    return _AttachmentFields(
        provider=fields.provider,
        role=fields.role,
        status=fields.status,
        session_name=fields.session_name,
        remote_session_id=fields.remote_session_id,
        session_url=fields.session_url,
        metadata_path=fields.metadata_path,
        launcher_source=fields.launcher_source,
        host_pid=fields.host_pid,
        host_session_label=fields.host_session_label,
        previous_operator_mode=fields.previous_operator_mode,
        entrypoint=fields.entrypoint,
        physical_remote_control_confirmed=False,
        physical_confirmation_method="none",
        source_hook_event_name="",
        source_hook_prompt="",
        source_hook_command_name="",
        source_hook_session_id="",
        source_hook_transcript_path="",
        source_hook_dedupe_key="",
        source_proof_channel="",
        source_proof_observed_at_utc="",
    )


def _attachment_identity(
    spec: RemoteControlAttachmentBuildInput,
    *,
    same_attachment: bool,
) -> tuple[str, str]:
    attachment_id = f"remote-attach-{slugify_timestamp(spec.now_utc)}"
    attached_at_utc = spec.now_utc
    if spec.existing is not None and (same_attachment or spec.refresh_existing_identity):
        attachment_id = spec.existing.attachment_id or attachment_id
        attached_at_utc = spec.existing.attached_at_utc or spec.now_utc
    return attachment_id, attached_at_utc


def _resolved_ttl(spec: RemoteControlAttachmentBuildInput) -> int:
    if spec.heartbeat_ttl_seconds is None:
        return DEFAULT_REMOTE_CONTROL_HEARTBEAT_TTL_SECONDS
    return int_or_default(
        spec.heartbeat_ttl_seconds,
        DEFAULT_REMOTE_CONTROL_HEARTBEAT_TTL_SECONDS,
    )


__all__ = [
    "RemoteControlAttachmentBuildInput",
    "build_remote_control_attachment_state",
]
