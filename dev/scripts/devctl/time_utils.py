"""Small shared UTC timestamp helpers for devctl reports."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_timestamp() -> str:
    """Return a stable UTC ISO-8601 timestamp for command reports."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_utc_timestamp(value: object) -> datetime | None:
    """Parse an ISO-8601 UTC-ish timestamp into an aware UTC datetime."""
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
