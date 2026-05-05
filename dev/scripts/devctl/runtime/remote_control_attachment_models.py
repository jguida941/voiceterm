"""Typed RemoteControlAttachmentState model + deserialization helpers.

Extracted from reviewer_runtime_models.py to keep that module under the
shape budget. Re-exported there for backward-compatible imports; new
consumers should import directly from this module.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlparse

from .remote_control_attachment_status import (
    ACTIVE_REMOTE_CONTROL_ATTACHMENT_STATUSES,
    DEFAULT_REMOTE_CONTROL_HEARTBEAT_TTL_SECONDS,
    remote_attachment_active,
)


@dataclass(frozen=True, slots=True)
class RemoteControlAttachmentState:
    provider: str = ""
    role: str = "operator"
    attachment_id: str = ""
    session_name: str = ""
    remote_session_id: str = ""
    session_url: str = ""
    status: str = "unknown"
    transport: str = "review_channel_artifact"
    attached_at_utc: str = ""
    last_seen_utc: str = ""
    metadata_path: str = ""
    launcher_source: str = ""
    host_pid: int | None = None
    host_session_label: str = ""
    heartbeat_ttl_seconds: int = DEFAULT_REMOTE_CONTROL_HEARTBEAT_TTL_SECONDS
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


_ACTIVE_REMOTE_CONTROL_ATTACHMENT_STATUSES = frozenset(
    ACTIVE_REMOTE_CONTROL_ATTACHMENT_STATUSES
)


def remote_control_attachment_from_mapping(
    value: object,
) -> RemoteControlAttachmentState | None:
    """Deserialize an optional remote-control attachment record."""
    if not isinstance(value, Mapping):
        return None
    attachment_id = str(value.get("attachment_id") or "").strip()
    session_name = str(value.get("session_name") or "").strip()
    remote_session_id = str(value.get("remote_session_id") or "").strip()
    session_url = str(value.get("session_url") or "").strip()
    if not any((attachment_id, session_name, remote_session_id, session_url)):
        return None
    return RemoteControlAttachmentState(
        provider=str(value.get("provider") or "").strip(),
        role=str(value.get("role") or "operator").strip() or "operator",
        attachment_id=attachment_id,
        session_name=session_name,
        remote_session_id=remote_session_id,
        session_url=session_url,
        status=str(value.get("status") or "unknown").strip() or "unknown",
        transport=(
            str(value.get("transport") or "review_channel_artifact").strip()
            or "review_channel_artifact"
        ),
        attached_at_utc=str(value.get("attached_at_utc") or "").strip(),
        last_seen_utc=str(value.get("last_seen_utc") or "").strip(),
        metadata_path=str(value.get("metadata_path") or "").strip(),
        launcher_source=str(value.get("launcher_source") or "").strip(),
        host_pid=int_or_none(value.get("host_pid")),
        host_session_label=str(value.get("host_session_label") or "").strip(),
        heartbeat_ttl_seconds=int_or_default(
            value.get("heartbeat_ttl_seconds"),
            DEFAULT_REMOTE_CONTROL_HEARTBEAT_TTL_SECONDS,
        ),
        previous_operator_mode=str(value.get("previous_operator_mode") or "").strip(),
        entrypoint=str(value.get("entrypoint") or "").strip(),
        physical_remote_control_confirmed=bool_or_false(
            value.get("physical_remote_control_confirmed")
        ),
        physical_confirmation_method=(
            str(value.get("physical_confirmation_method") or "none").strip()
            or "none"
        ),
        source_hook_event_name=str(value.get("source_hook_event_name") or "").strip(),
        source_hook_prompt=str(value.get("source_hook_prompt") or "").strip(),
        source_hook_command_name=str(value.get("source_hook_command_name") or "").strip(),
        source_hook_session_id=str(value.get("source_hook_session_id") or "").strip(),
        source_hook_transcript_path=str(
            value.get("source_hook_transcript_path") or ""
        ).strip(),
        source_hook_dedupe_key=str(value.get("source_hook_dedupe_key") or "").strip(),
        source_proof_channel=str(value.get("source_proof_channel") or "").strip(),
        source_proof_observed_at_utc=str(
            value.get("source_proof_observed_at_utc") or ""
        ).strip(),
    )


def has_active_remote_control_attachment(
    attachment: RemoteControlAttachmentState | None,
) -> bool:
    """Return True when the external remote-control session should drive mode."""
    return remote_attachment_active(attachment)


def session_id_from_url(session_url: str) -> str:
    """Extract the trailing ``session_<id>`` segment from a remote session URL.

    Query strings and fragments are stripped before tail extraction so URLs
    like ``https://claude.ai/code/session_abc?foo=1`` resolve correctly.
    Returns ``""`` when no session_id pattern is recognized.
    """
    trimmed = str(session_url or "").strip()
    if not trimmed:
        return ""
    path = urlparse(trimmed).path.rstrip("/")
    if not path:
        return ""
    tail = path.rsplit("/", 1)[-1]
    return tail if tail.startswith("session_") else ""


def slugify_timestamp(value: str) -> str:
    """Collapse an ISO-8601 timestamp into a filesystem-safe slug.

    Keeps the ``T`` and ``Z`` anchors so the resulting id is still readable
    (e.g. ``20260409T131415Z``) while stripping separators that are awkward
    in filenames and attachment ids.
    """
    return (
        str(value or "")
        .replace("-", "")
        .replace(":", "")
        .replace(".", "")
    )


def int_or_none(value: object) -> int | None:
    """Parse an int, returning ``None`` for missing/invalid input.

    Treats Python ``None`` and empty-string the same as missing. Per
    rev_pkt_2986 finding #5: numeric ``0`` is a legal integer and must NOT
    be coerced to None just because it is falsy.
    """
    if value is None:
        return None
    try:
        text = str(value).strip()
    except (TypeError, ValueError):
        return None
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def int_or_default(value: object, default: int) -> int:
    """Parse an int, returning ``default`` for missing/invalid input.

    Per rev_pkt_2986 finding #5: numeric ``0`` is a legal integer and must
    NOT be replaced by ``default`` just because it is falsy. Only ``None``,
    empty string, and unparseable values fall back to ``default``.
    """
    if value is None:
        return default
    try:
        text = str(value).strip()
    except (TypeError, ValueError):
        return default
    if not text:
        return default
    try:
        return int(text)
    except ValueError:
        return default


def bool_or_false(value: object) -> bool:
    """Parse a loose bool value from JSON/argparse-shaped payloads."""
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes", "on"}


def __getattr__(name: str) -> object:
    if name in {
        "RemoteControlAttachmentBuildInput",
        "build_remote_control_attachment_state",
    }:
        from . import remote_control_attachment_builder as builder

        return getattr(builder, name)
    raise AttributeError(name)


__all__ = [
    "RemoteControlAttachmentState",
    "RemoteControlAttachmentBuildInput",
    "remote_control_attachment_from_mapping",
    "has_active_remote_control_attachment",
    "session_id_from_url",
    "slugify_timestamp",
    "int_or_none",
    "int_or_default",
    "bool_or_false",
    "build_remote_control_attachment_state",
]
