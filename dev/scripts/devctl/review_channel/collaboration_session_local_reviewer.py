"""Local-reviewer liveness helpers for collaboration-session projection."""

from __future__ import annotations

import json
from collections import deque
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

from ..commands.rollout_tail.discovery import discover_latest_session
from .peer_liveness import (
    CODEX_POLL_STALE_AFTER_SECONDS,
    ReviewerFreshness,
    classify_reviewer_freshness,
)

_LOCAL_REVIEWER_EVENT_SCAN_LIMIT = 200
_LOCAL_REVIEWER_ACTIVITY_EVENT_TYPES = frozenset(
    {"packet_posted", "packet_acked", "packet_dismissed", "packet_applied"}
)


def local_reviewer_turn_is_live(
    *,
    bridge_liveness: Mapping[str, object],
    reviewer_mode: str,
    reviewer_provider: str,
    session_output_root: Path | None,
) -> bool:
    if reviewer_mode != "single_agent":
        return False
    freshness = text(bridge_liveness.get("reviewer_freshness"))
    if freshness in {"fresh", "poll_due"}:
        return True
    if text(bridge_liveness.get("reviewer_poll_state")) in {"fresh", "poll_due"}:
        return True
    if text(bridge_liveness.get("codex_poll_state")) in {"fresh", "poll_due"}:
        return True
    return local_reviewer_activity_is_fresh(
        reviewer_provider=reviewer_provider,
        session_output_root=session_output_root,
    )


def local_reviewer_activity_is_fresh(
    *,
    reviewer_provider: str,
    session_output_root: Path | None,
) -> bool:
    if provider_packet_activity_is_fresh(
        provider=reviewer_provider,
        session_output_root=session_output_root,
    ):
        return True
    return local_reviewer_rollout_is_fresh(reviewer_provider=reviewer_provider)


def provider_packet_activity_is_fresh(
    *,
    provider: str,
    session_output_root: Path | None,
) -> bool:
    event_log_path = resolve_event_log_path(session_output_root)
    if event_log_path is not None:
        latest_activity = latest_provider_packet_activity(
            event_log_path,
            provider=provider,
        )
        if latest_activity is not None:
            activity_age = age_seconds(str(latest_activity.get("timestamp_utc") or ""))
            freshness = classify_reviewer_freshness(activity_age)
            if freshness not in {ReviewerFreshness.MISSING, ReviewerFreshness.OVERDUE}:
                return True
    return False


def local_reviewer_rollout_is_fresh(*, reviewer_provider: str) -> bool:
    rollout_path = latest_local_reviewer_rollout_path(
        reviewer_provider=reviewer_provider
    )
    if rollout_path is None:
        return False
    try:
        modified_at = datetime.fromtimestamp(rollout_path.stat().st_mtime, tz=timezone.utc)
    except OSError:
        return False
    rollout_age_seconds = int(max((_utcnow() - modified_at).total_seconds(), 0.0))
    return rollout_age_seconds <= CODEX_POLL_STALE_AFTER_SECONDS


def latest_local_reviewer_rollout_path(*, reviewer_provider: str) -> Path | None:
    provider = text(reviewer_provider)
    if not provider:
        return None
    return discover_latest_session(provider)


def resolve_event_log_path(session_output_root: Path | None) -> Path | None:
    if session_output_root is None:
        return None
    candidates = (
        session_output_root / "events/trace.ndjson",
        session_output_root.parent / "events/trace.ndjson",
        session_output_root.parent.parent / "events/trace.ndjson",
    )
    for path in candidates:
        if path.is_file():
            return path
    return None


def latest_provider_packet_activity(
    event_log_path: Path,
    *,
    provider: str,
) -> dict[str, object] | None:
    for event in reversed(load_recent_event_rows(event_log_path)):
        if event_marks_provider_packet_activity(
            event,
            provider=provider,
        ):
            return event
    return None


def load_recent_event_rows(event_log_path: Path) -> list[dict[str, object]]:
    try:
        with event_log_path.open(encoding="utf-8") as handle:
            lines = list(deque(handle, maxlen=_LOCAL_REVIEWER_EVENT_SCAN_LIMIT))
    except OSError:
        return []
    events: list[dict[str, object]] = []
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


def event_marks_provider_packet_activity(
    event: Mapping[str, object],
    *,
    provider: str,
) -> bool:
    event_type = str(event.get("event_type") or "").strip()
    if event_type not in _LOCAL_REVIEWER_ACTIVITY_EVENT_TYPES:
        return False
    if event_type == "packet_posted":
        return text(event.get("from_agent")) == provider
    metadata = event.get("metadata")
    if not isinstance(metadata, Mapping):
        return False
    return text(metadata.get("actor")) == provider


def age_seconds(timestamp_utc: str) -> int | None:
    normalized_timestamp = timestamp_utc.strip()
    if not normalized_timestamp:
        return None
    normalized_timestamp = normalized_timestamp.replace("Z", "+00:00")
    try:
        observed = datetime.fromisoformat(normalized_timestamp)
    except ValueError:
        return None
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=timezone.utc)
    return int(max((_utcnow() - observed.astimezone(timezone.utc)).total_seconds(), 0.0))


def text(value: object) -> str:
    return str(value or "").strip()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)
