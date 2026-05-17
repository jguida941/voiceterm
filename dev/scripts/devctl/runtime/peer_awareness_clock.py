"""Clock and cadence helpers for peer-awareness policy."""

from __future__ import annotations

from datetime import datetime, timezone


def peer_poll_due(
    *,
    policy: object,
    boundary_at_utc: str,
    last_peer_poll_at_utc: str,
    pending_packet_count: int,
    agent_message_boundary: str,
    long_running_work_classes: frozenset[str],
) -> bool:
    """Return whether the current boundary requires fresh peer awareness."""
    boundary_events = tuple(getattr(policy, "boundary_events", ()) or ())
    if agent_message_boundary not in boundary_events:
        return False
    if pending_packet_count > 0 and not _text(last_peer_poll_at_utc):
        return True
    boundary_at = _text(boundary_at_utc)
    last_poll = _text(last_peer_poll_at_utc)
    work_class = _text(getattr(policy, "work_class", ""))
    if not last_poll:
        return work_class in long_running_work_classes
    if pending_packet_count > 0 and boundary_at and last_poll < boundary_at:
        return True
    if boundary_at and last_poll < boundary_at and work_class in long_running_work_classes:
        elapsed_seconds = _elapsed_seconds(last_poll, boundary_at)
        if elapsed_seconds is None:
            return True
        return elapsed_seconds >= int(getattr(policy, "cadence_seconds", 0) or 0)
    return False


def long_running_cadence(role: str) -> int:
    if role in {"dashboard", "observer", "reviewer"}:
        return 300
    return 300


def _elapsed_seconds(start_utc: str, end_utc: str) -> float | None:
    start = _parse_utc(start_utc)
    end = _parse_utc(end_utc)
    if start is None or end is None:
        return None
    return (end - start).total_seconds()


def _parse_utc(value: str) -> datetime | None:
    raw = _text(value)
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = f"{raw[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["long_running_cadence", "peer_poll_due"]
