"""Small shared UTC timestamp helpers for devctl reports."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_timestamp() -> str:
    """Return a stable UTC ISO-8601 timestamp for command reports."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
