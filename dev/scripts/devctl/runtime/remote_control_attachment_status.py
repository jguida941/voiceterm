"""Status and TTL helpers for remote-control attachment records."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone

from .typed_string_field import read_string_field as _field

DEFAULT_REMOTE_CONTROL_HEARTBEAT_TTL_SECONDS = 900
SYNTHETIC_REMOTE_SESSION_ID_PREFIXES = ("claude-code:",)
# Per rev_pkt_3000 + rev_pkt_3003 #1: only ``attached`` is genuinely
# active. ``unknown``/``evidence_missing``/``detached`` must NEVER promote
# operator_interaction_mode=remote_control. ``unknown`` was previously a
# transitional pre-heartbeat state that fail-opened, which is exactly the
# bug rev_pkt_3001 surfaced (UI says Remote Control active, typed surface
# says local_terminal). Identity-bound attached evidence is the only proof
# of life.
ACTIVE_REMOTE_CONTROL_ATTACHMENT_STATUSES = frozenset({"attached"})


def remote_attachment_active(value: object | None) -> bool:
    """Return true when an attachment proves live remote-control presence.

    Per rev_pkt_3023 P0 #2: an attachment must be IDENTITY-BOUND to count
    as active. Status=attached + fresh TTL alone is not sufficient — a
    malformed or legacy row with no ``remote_session_id`` and no
    ``session_url`` cannot prove a live remote-control session, so it
    must not promote operator_interaction_mode=remote_control. Likewise,
    local provider transcript ids such as ``claude-code:<session>`` only
    prove that a Claude Code session exists, not that the phone/dashboard
    remote-control transport is active. The active predicate now requires:

      1. status in ACTIVE_REMOTE_CONTROL_ATTACHMENT_STATUSES (only
         "attached" today),
      2. not expired (TTL fresh),
      3. AT LEAST ONE physical remote-control identity field: a session URL
         or a remote-session id that is not a local provider transcript id.
    """
    if value is None:
        return False
    if remote_attachment_status(value) not in ACTIVE_REMOTE_CONTROL_ATTACHMENT_STATUSES:
        return False
    if remote_attachment_expired(value):
        return False
    return remote_attachment_has_physical_identity(value)


def remote_attachment_has_physical_identity(value: object | None) -> bool:
    """Return true when the attachment carries physical remote-control identity."""
    if value is None:
        return False
    if _field(value, "session_url"):
        return True
    remote_session_id = _field(value, "remote_session_id")
    if not remote_session_id:
        return False
    return not remote_session_id.startswith(SYNTHETIC_REMOTE_SESSION_ID_PREFIXES)


def remote_attachment_expired(value: object | None) -> bool:
    """Return true when an active-status attachment is older than its TTL."""
    if value is None:
        return False
    if remote_attachment_status(value) not in ACTIVE_REMOTE_CONTROL_ATTACHMENT_STATUSES:
        return False
    ttl_seconds = remote_attachment_ttl_seconds(value)
    if ttl_seconds < 0:
        return False
    age_seconds = remote_attachment_age_seconds(value)
    if age_seconds is None:
        return True
    return age_seconds > ttl_seconds


def remote_attachment_age_seconds(value: object | None) -> int | None:
    """Return attachment heartbeat age in seconds, or ``None`` when unknown."""
    timestamp = remote_attachment_last_seen(value)
    if not timestamp:
        return None
    parsed = _parse_utc_timestamp(timestamp)
    if parsed is None:
        return None
    return max(0, int((datetime.now(timezone.utc) - parsed).total_seconds()))


def remote_attachment_status(value: object | None) -> str:
    status = _field(value, "status")
    return status.lower() or "unknown"


def remote_attachment_last_seen(value: object | None) -> str:
    return _field(value, "last_seen_utc") or _field(value, "attached_at_utc")


def remote_attachment_ttl_seconds(value: object | None) -> int:
    raw = _field(value, "heartbeat_ttl_seconds")
    if not raw:
        return DEFAULT_REMOTE_CONTROL_HEARTBEAT_TTL_SECONDS
    try:
        return int(raw)
    except ValueError:
        return DEFAULT_REMOTE_CONTROL_HEARTBEAT_TTL_SECONDS


def _parse_utc_timestamp(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


__all__ = [
    "ACTIVE_REMOTE_CONTROL_ATTACHMENT_STATUSES",
    "DEFAULT_REMOTE_CONTROL_HEARTBEAT_TTL_SECONDS",
    "remote_attachment_active",
    "remote_attachment_age_seconds",
    "remote_attachment_expired",
    "remote_attachment_has_physical_identity",
    "remote_attachment_last_seen",
    "remote_attachment_status",
    "remote_attachment_ttl_seconds",
]
