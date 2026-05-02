"""Time helpers for watcher lease freshness."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone


def stale_seconds(state: Mapping[str, object]) -> int:
    heartbeat = _parse_utc(_text(state.get("last_heartbeat_utc")))
    if heartbeat is None:
        return 0
    return max(int((datetime.now(timezone.utc) - heartbeat).total_seconds()), 0)


def _parse_utc(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["stale_seconds"]
