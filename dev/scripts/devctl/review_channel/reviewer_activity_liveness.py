"""Typed reviewer-activity liveness projection helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .collaboration_session_local_reviewer import (
    age_seconds,
    latest_provider_packet_activity,
    resolve_event_log_path,
)
from .peer_liveness import (
    CodexPollState,
    ReviewerFreshness,
    classify_reviewer_freshness,
)

_LIVE_ACTIVITY_FRESHNESS = frozenset(
    {
        ReviewerFreshness.FRESH.value,
        ReviewerFreshness.POLL_DUE.value,
        ReviewerFreshness.STALE.value,
    }
)
_ACTIVE_ACTIVITY_FRESHNESS = frozenset(
    {
        ReviewerFreshness.FRESH.value,
        ReviewerFreshness.POLL_DUE.value,
    }
)


@dataclass(frozen=True)
class ReviewerActivityLiveness:
    """Latest typed packet activity that proves a reviewer turn happened."""

    provider: str
    observed_at_utc: str
    age_seconds: int
    freshness: str
    poll_state: str
    event_type: str
    source: str = "typed_packet_activity"


def latest_reviewer_activity_liveness(
    *,
    reviewer_provider: str,
    session_output_root: Path | None,
) -> ReviewerActivityLiveness | None:
    """Return the latest reviewer packet activity usable as liveness evidence."""
    provider = str(reviewer_provider or "").strip().lower()
    if not provider:
        return None
    event_log_path = resolve_event_log_path(session_output_root)
    if event_log_path is None:
        return None
    activity = latest_provider_packet_activity(event_log_path, provider=provider)
    if activity is None:
        return None
    observed_at_utc = str(activity.get("timestamp_utc") or "").strip()
    observed_age = age_seconds(observed_at_utc)
    freshness = classify_reviewer_freshness(observed_age)
    if observed_age is None or freshness.value not in _LIVE_ACTIVITY_FRESHNESS:
        return None
    return ReviewerActivityLiveness(
        provider=provider,
        observed_at_utc=observed_at_utc,
        age_seconds=observed_age,
        freshness=freshness.value,
        poll_state=_poll_state_for_freshness(freshness),
        event_type=str(activity.get("event_type") or "").strip(),
    )


def apply_reviewer_activity_liveness(
    *,
    bridge_liveness: dict[str, object],
    reviewer_provider: str,
    session_output_root: Path | None,
) -> ReviewerActivityLiveness | None:
    """Overlay typed reviewer packet activity onto bridge liveness fields."""
    activity = latest_reviewer_activity_liveness(
        reviewer_provider=reviewer_provider,
        session_output_root=session_output_root,
    )
    if activity is None:
        return None
    current_age = _current_poll_age(bridge_liveness)
    if current_age is not None and current_age <= activity.age_seconds:
        return None

    bridge_liveness["reviewer_activity_source"] = activity.source
    bridge_liveness["reviewer_activity_provider"] = activity.provider
    bridge_liveness["reviewer_activity_event_type"] = activity.event_type
    bridge_liveness["reviewer_activity_observed_at_utc"] = activity.observed_at_utc
    bridge_liveness["reviewer_activity_age_seconds"] = activity.age_seconds
    bridge_liveness["last_reviewer_poll_utc"] = activity.observed_at_utc
    bridge_liveness["last_codex_poll_utc"] = activity.observed_at_utc
    bridge_liveness["last_reviewer_poll_age_seconds"] = activity.age_seconds
    bridge_liveness["last_codex_poll_age_seconds"] = activity.age_seconds
    bridge_liveness["reviewer_poll_state"] = activity.poll_state
    bridge_liveness["codex_poll_state"] = activity.poll_state
    bridge_liveness["reviewer_freshness"] = activity.freshness
    bridge_liveness["reviewer_activity_active"] = (
        activity.freshness in _ACTIVE_ACTIVITY_FRESHNESS
    )
    return activity


def _current_poll_age(bridge_liveness: dict[str, object]) -> int | None:
    for key in ("last_reviewer_poll_age_seconds", "last_codex_poll_age_seconds"):
        value = bridge_liveness.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
    return None


def _poll_state_for_freshness(freshness: ReviewerFreshness) -> str:
    if freshness is ReviewerFreshness.FRESH:
        return CodexPollState.FRESH.value
    if freshness is ReviewerFreshness.POLL_DUE:
        return CodexPollState.POLL_DUE.value
    return CodexPollState.STALE.value
