"""Timestamp helpers for session termination policy."""

from __future__ import annotations

from datetime import datetime, timezone


def expired(value: str) -> bool:
    stamp = parse_utc(value)
    return stamp is not None and stamp <= datetime.now(timezone.utc)


def parse_utc(value: object) -> datetime | None:
    text = _text(value)
    if not text:
        return None
    try:
        stamp = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        return stamp.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc)


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()
