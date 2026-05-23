"""Timestamp parsing and recency-window helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone


def parse_timestamp(value: str, warnings: list[str]) -> datetime | None:
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        warnings.append(f"invalid timestamp skipped: {value}")
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def within_latest_window(
    snapshots: Sequence[Mapping[str, object]],
    window_hours: int,
    warnings: list[str],
) -> tuple[Mapping[str, object], ...]:
    dated: list[tuple[datetime, Mapping[str, object]]] = []
    for snapshot in snapshots:
        captured = parse_timestamp(str(snapshot.get("captured_at_utc", "")), warnings)
        if captured is None:
            continue
        dated.append((captured, snapshot))
    if not dated:
        return ()
    latest = max(captured for captured, _snapshot in dated)
    cutoff = latest - timedelta(hours=window_hours)
    return tuple(snapshot for captured, snapshot in dated if captured >= cutoff)
