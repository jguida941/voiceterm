"""Action-request ordering helpers for packet control-loop selection."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone


def action_request_control_state(packet: Mapping[str, object]) -> str:
    """Classify the current live control posture of one action_request packet."""
    if str(packet.get("apply_pending_after_execution_at_utc") or "").strip():
        return "apply_pending_after_execution"
    if str(packet.get("execution_failed_at_utc") or "").strip():
        return "failed"
    if str(packet.get("execution_started_at_utc") or "").strip():
        return "in_progress"
    if str(packet.get("delivery_observed_at_utc") or "").strip():
        return "execution_pending"
    return "delivery_pending"


def action_request_priority_key(packet: Mapping[str, object]) -> tuple[object, ...]:
    """Return stable action-request ordering by lifecycle urgency."""
    state_rank = {
        "apply_pending_after_execution": 0,
        "execution_pending": 1,
        "delivery_pending": 2,
        "in_progress": 3,
        "failed": 4,
    }
    return (
        state_rank.get(action_request_control_state(packet), 9),
        parse_utc(packet.get("expires_at_utc")),
        parse_utc(packet.get("posted_at")),
        str(packet.get("packet_id") or "").strip(),
    )


def parse_utc(value: object) -> datetime:
    """Parse UTC-ish values for deterministic packet ordering."""
    text = str(value or "").strip()
    if not text:
        return datetime.max.replace(tzinfo=timezone.utc)
    try:
        observed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return datetime.max.replace(tzinfo=timezone.utc)
    if observed.tzinfo is None:
        return observed.replace(tzinfo=timezone.utc)
    return observed.astimezone(timezone.utc)
