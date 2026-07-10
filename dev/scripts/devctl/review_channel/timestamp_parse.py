"""Shared timestamp parsing for review-channel reduced rows."""

from __future__ import annotations

from datetime import datetime, timezone


def parse_utc_value(value: object) -> datetime | None:
    raw = "" if value is None else str(value).strip()
    if raw == "":
        return None
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        stamp = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    timezone_aware = stamp if stamp.tzinfo is not None else stamp.replace(
        tzinfo=timezone.utc
    )
    return timezone_aware.astimezone(timezone.utc)
