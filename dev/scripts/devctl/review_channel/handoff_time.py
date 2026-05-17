"""Timestamp and poll-age helpers extracted from handoff.py."""

from __future__ import annotations

from datetime import datetime, timezone


def _parse_utc_z(raw_value: str | None) -> datetime | None:
    if not raw_value:
        return None
    normalized = raw_value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _timestamp_age_seconds(
    raw_value: str | None,
    *,
    now_utc: datetime | None,
) -> int | None:
    parsed = _parse_utc_z(raw_value)
    if parsed is None:
        return None
    current = now_utc or datetime.now(timezone.utc)
    age_seconds = int((current - parsed).total_seconds())
    return max(age_seconds, 0)


def _codex_poll_advanced(
    *,
    previous_poll_utc: str | None,
    current_poll_utc: str | None,
) -> bool:
    current = _parse_utc_z(current_poll_utc)
    if current is None:
        return False
    previous = _parse_utc_z(previous_poll_utc)
    if previous is None:
        return True
    return current > previous
