"""Lifecycle denial checks for commit action-request authority."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone

from ...runtime.value_coercion import coerce_text as _text

_ACTIONABLE_PACKET_STATUSES = frozenset({"pending", "acked"})


def lifecycle_status_block(packet: Mapping[str, object]) -> str:
    """Return a denial reason for non-actionable action-request lifecycle state."""
    if _text(packet.get("kind")) != "action_request":
        return "action_request_kind_mismatch"
    if _text(packet.get("execution_failed_at_utc")):
        return "action_request_execution_failed"
    if _text(packet.get("apply_pending_after_execution_at_utc")):
        return "action_request_apply_pending_after_execution"
    if _text(packet.get("status")) not in _ACTIONABLE_PACKET_STATUSES:
        return "action_request_not_actionable"
    if _is_expired(packet):
        return "action_request_expired"
    return ""


def _is_expired(packet: Mapping[str, object]) -> bool:
    raw = _text(packet.get("expires_at_utc"))
    if not raw:
        return False
    try:
        expires_at = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return False
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at.astimezone(timezone.utc) <= datetime.now(timezone.utc)


__all__ = ["lifecycle_status_block"]
