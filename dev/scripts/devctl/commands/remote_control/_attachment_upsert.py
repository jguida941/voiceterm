"""Attachment-upsert helper for the remote-control lifecycle command.

Extracted from ``command.py`` to keep that module under the shape budget.
Owns the resolution of command-specific defaults (host_pid fallback,
host_session_label fallback chain, previous_operator_mode resolver) and
the ``refresh_existing_identity`` decision (rev_pkt_2996 finding #5).
The shared identity guard, session_url parsing, and TTL handling stay
in ``runtime.remote_control_attachment_models.build_remote_control_attachment_state``.
"""

from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path
from typing import Any

from ...review_channel.remote_control_attachment_artifact import (
    persist_remote_control_attachment,
)
from ...runtime.remote_control_attachment_builder import (
    RemoteControlAttachmentBuildInput,
    build_remote_control_attachment_state,
)
from ...runtime.remote_control_attachment_status import remote_attachment_active
from ...runtime.remote_control_attachment_status import (
    remote_attachment_has_physical_identity,
)
from ...runtime.reviewer_runtime_models import RemoteControlAttachmentState
from ...time_utils import utc_timestamp
from ._lifecycle_state_resolution import has_remote_identity
from ._lifecycle_state_resolution import has_proven_refresh_source


def persist_lifecycle_attachment(
    args: Any,
    *,
    status: str,
    status_dir: Path,
    existing: RemoteControlAttachmentState | None,
) -> tuple[RemoteControlAttachmentState, Path]:
    """Persist the upserted attachment artifact for one lifecycle action.

    Per rev_pkt_2986 finding #2 the identity guard / session_url parsing /
    fallback merge / TTL all live in the shared builder; this helper
    resolves command-specific defaults BEFORE delegation, then opts the
    builder into ``refresh_existing_identity`` when the lifecycle call is
    refreshing an already-bound active attachment without re-passing
    identity flags (rev_pkt_2996 finding #5).
    """
    now = utc_timestamp()
    current = existing
    resolved_host_pid = _resolve_host_pid(args, current)
    resolved_host_session_label = _resolve_host_session_label(args, current)
    resolved_previous_operator_mode = _resolve_previous_operator_mode(current)
    refresh_existing_identity = _should_refresh_existing_identity(
        args, current=current, status=status
    )

    attachment = build_remote_control_attachment_state(
        RemoteControlAttachmentBuildInput(
            now_utc=now,
            provider=str(getattr(args, "provider", "claude") or "claude"),
            role=str(getattr(args, "role", "operator") or "operator"),
            status=status,
            session_name=_field(args, "session_name"),
            remote_session_id=_field(args, "remote_session_id"),
            session_url=_field(args, "session_url"),
            metadata_path=_field(current, "metadata_path"),
            launcher_source=_field(args, "launcher_source"),
            host_pid=resolved_host_pid,
            host_session_label=resolved_host_session_label,
            heartbeat_ttl_seconds=getattr(args, "heartbeat_ttl_seconds", None),
            previous_operator_mode=resolved_previous_operator_mode,
            entrypoint=_field(args, "entrypoint"),
            physical_remote_control_confirmed=bool(
                getattr(args, "physical_remote_control_confirmed", False)
            ),
            physical_confirmation_method=(
                _field(args, "physical_confirmation_method")
                or (
                    "operator_assertion"
                    if bool(getattr(args, "physical_remote_control_confirmed", False))
                    else "none"
                )
            ),
            source_hook_event_name=_field(args, "source_hook_event_name"),
            source_hook_prompt=_field(args, "source_hook_prompt"),
            source_hook_command_name=_field(args, "source_hook_command_name"),
            source_hook_session_id=_field(args, "source_hook_session_id"),
            source_hook_transcript_path=_field(args, "source_hook_transcript_path"),
            source_hook_dedupe_key=_field(args, "source_hook_dedupe_key"),
            source_proof_channel=_field(args, "source_proof_channel"),
            source_proof_observed_at_utc=_field(args, "source_proof_observed_at_utc"),
            existing=current,
            refresh_existing_identity=refresh_existing_identity,
        ),
    )
    artifact_path = persist_remote_control_attachment(
        attachment,
        output_root=status_dir,
    )
    return replace(attachment, metadata_path=str(artifact_path)), artifact_path


def _resolve_host_pid(
    args: Any, current: RemoteControlAttachmentState | None
) -> int | None:
    arg_host_pid = getattr(args, "host_pid", None)
    if arg_host_pid is not None:
        return arg_host_pid
    if current is not None and current.host_pid is not None:
        return current.host_pid
    return os.getpid()


def _resolve_host_session_label(
    args: Any, current: RemoteControlAttachmentState | None
) -> str:
    return (
        _field(args, "host_session_label")
        or _field(args, "session_name")
        or _field(current, "host_session_label")
    )


def _resolve_previous_operator_mode(
    current: RemoteControlAttachmentState | None,
) -> str:
    fallback = (
        "remote_control"
        if current is not None and remote_attachment_active(current)
        else "local_terminal"
    )
    return _field(current, "previous_operator_mode") or fallback


def _should_refresh_existing_identity(
    args: Any,
    *,
    current: RemoteControlAttachmentState | None,
    status: str,
) -> bool:
    if current is None or has_remote_identity(args) or status not in {"attached", "detached"}:
        return False
    if not has_proven_refresh_source(args):
        return False
    return remote_attachment_has_physical_identity(current)


def _field(value: object | None, name: str) -> str:
    if value is None:
        return ""
    return str(getattr(value, name, "") or "").strip()


__all__ = ["persist_lifecycle_attachment"]
