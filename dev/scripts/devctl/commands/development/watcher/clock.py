"""Time helpers for watcher lease freshness."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone

from ....time_utils import parse_utc_timestamp


def stale_seconds(state: Mapping[str, object]) -> int:
    heartbeat = parse_utc_timestamp(_text(state.get("last_heartbeat_utc")))
    if heartbeat is None:
        return 0
    return max(int((datetime.now(timezone.utc) - heartbeat).total_seconds()), 0)


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["stale_seconds"]
