"""Unified typed liveness signal per agent participant (MP377-P1-T08).

Replaces scattered liveness state across launch_truth, peer_liveness,
session_liveness, and lifecycle_state with one canonical signal that
all surfaces consume: dashboard, session-resume, startup-context,
follow-controller.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from ..time_utils import utc_timestamp

LivenessState = Literal["alive", "degraded", "detached_runtime_only", "dead"]


@dataclass(frozen=True, slots=True)
class ParticipantLivenessSignal:
    """One typed liveness signal for a single agent participant."""

    provider: str
    role: str
    state: LivenessState
    reason: str
    process_live: bool | None = None
    terminal_open: bool | None = None
    poll_age_seconds: int | None = None
    last_activity_utc: str | None = None
    timestamp_utc: str = field(default_factory=utc_timestamp)

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        payload["provider"] = self.provider
        payload["role"] = self.role
        payload["state"] = self.state
        payload["reason"] = self.reason
        if self.process_live is not None:
            payload["process_live"] = self.process_live
        if self.terminal_open is not None:
            payload["terminal_open"] = self.terminal_open
        if self.poll_age_seconds is not None:
            payload["poll_age_seconds"] = self.poll_age_seconds
        if self.last_activity_utc is not None:
            payload["last_activity_utc"] = self.last_activity_utc
        payload["timestamp_utc"] = self.timestamp_utc
        return payload


def classify_participant_liveness(
    *,
    provider: str,
    role: str,
    publisher_running: bool = False,
    reviewer_supervisor_running: bool = False,
    conductor_active: bool = False,
    poll_age_seconds: int | None = None,
    overdue_threshold_seconds: int = 900,
) -> ParticipantLivenessSignal:
    """Classify one participant into the canonical liveness family."""
    if conductor_active and (publisher_running or reviewer_supervisor_running):
        state: LivenessState = "alive"
        reason = "conductor and runtime daemons active"
    elif conductor_active:
        state = "degraded"
        reason = "conductor active but runtime daemons stopped"
    elif publisher_running or reviewer_supervisor_running:
        state = "detached_runtime_only"
        reason = "runtime daemons running without conductor"
    else:
        state = "dead"
        reason = "no conductor or runtime daemons"

    if poll_age_seconds is not None and poll_age_seconds > overdue_threshold_seconds:
        if state == "alive":
            state = "degraded"
            reason = f"poll overdue ({poll_age_seconds}s > {overdue_threshold_seconds}s)"

    return ParticipantLivenessSignal(
        provider=provider,
        role=role,
        state=state,
        reason=reason,
        process_live=conductor_active,
        poll_age_seconds=poll_age_seconds,
    )
