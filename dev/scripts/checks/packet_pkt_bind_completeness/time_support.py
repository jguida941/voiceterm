"""Time and path helpers for packet PKT-BIND completeness."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path


def parse_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def format_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def age_minutes(started_at: datetime, now_utc: datetime) -> int:
    delta = now_utc.astimezone(UTC) - started_at.astimezone(UTC)
    return max(0, int(delta.total_seconds() // 60))


def display_path(path: Path, *, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def text(value: object) -> str:
    return str(value or "").strip()
