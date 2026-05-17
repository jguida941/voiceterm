"""Live session trace helpers shared by Operator Console lane builders."""

from __future__ import annotations

from datetime import datetime, timezone

from ..sessions.session_trace_reader import SessionTraceSnapshot


def live_trace_status(
    live_trace: SessionTraceSnapshot | None,
    *,
    max_age_seconds: int = 300,
    active_age_seconds: int = 120,
) -> tuple[str, str] | None:
    if live_trace is None or live_trace.updated_at is None:
        return None
    age_seconds = timestamp_age_seconds(live_trace.updated_at)
    if age_seconds is None or age_seconds > max_age_seconds:
        return None
    if age_seconds <= active_age_seconds:
        return ("active", "live")
    return ("warning", "recent")


def live_trace_label(live_trace: SessionTraceSnapshot) -> str:
    freshness = live_trace_status(live_trace)
    freshness_label = freshness[1] if freshness is not None else "captured"
    return f"{live_trace.session_name} [{freshness_label}]"


def live_trace_raw_parts(live_trace: SessionTraceSnapshot | None) -> tuple[str, ...]:
    if live_trace is None:
        return ()
    return (
        f"Live session trace: {live_trace.session_name}",
        f"Live session updated: {live_trace.updated_at or '(unknown)'}",
        f"Live session log: {live_trace.log_path}",
    )


def timestamp_age_seconds(iso_timestamp: str) -> float | None:
    try:
        parsed = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return (datetime.now(tz=timezone.utc) - parsed).total_seconds()
