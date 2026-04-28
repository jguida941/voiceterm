"""Canonical runtime liveness signal family for governed agent sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from ..time_utils import utc_timestamp

SessionLivenessState = Literal[
    "alive",
    "degraded",
    "detached_runtime_only",
    "dead",
]
LIVE_SESSION_LIVENESS_STATES = frozenset({"alive", "degraded"})
RUNTIME_PRESENT_LIVENESS_STATES = frozenset(
    {"alive", "degraded", "detached_runtime_only"}
)


@dataclass(frozen=True, slots=True)
class SessionLivenessSignal:
    """One typed liveness signal for a provider-owned runtime participant."""

    provider: str
    role: str
    state: SessionLivenessState
    reason: str
    process_live: bool | None = None
    terminal_open: bool | None = None
    poll_age_seconds: int | None = None
    last_activity_utc: str | None = None
    timestamp_utc: str = field(default_factory=utc_timestamp)
    contract_id: str = "SessionLivenessSignal"
    schema_version: int = 1

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        for field_name in _SERIALIZED_SIGNAL_FIELDS:
            value = getattr(self, field_name)
            if value is not None:
                payload[field_name] = value
        return payload


@dataclass(frozen=True, slots=True)
class SessionLivenessInputs:
    """Typed classifier inputs for one provider-owned runtime participant."""

    provider: str
    role: str
    publisher_running: bool = False
    reviewer_supervisor_running: bool = False
    conductor_active: bool = False
    runtime_activity_active: bool = False
    poll_age_seconds: int | None = None
    overdue_threshold_seconds: int = 900


_SERIALIZED_SIGNAL_FIELDS = (
    "contract_id",
    "schema_version",
    "provider",
    "role",
    "state",
    "reason",
    "process_live",
    "terminal_open",
    "poll_age_seconds",
    "last_activity_utc",
    "timestamp_utc",
)


def classify_session_liveness(
    inputs: SessionLivenessInputs,
) -> SessionLivenessSignal:
    """Classify one participant into the canonical liveness family."""
    state, reason = _base_liveness_state(
        conductor_active=inputs.conductor_active,
        runtime_active=(
            inputs.publisher_running
            or inputs.reviewer_supervisor_running
            or inputs.runtime_activity_active
        ),
        daemon_active=inputs.publisher_running or inputs.reviewer_supervisor_running,
    )
    state, reason = _degrade_for_overdue_poll(
        state=state,
        reason=reason,
        poll_age_seconds=inputs.poll_age_seconds,
        overdue_threshold_seconds=inputs.overdue_threshold_seconds,
    )

    return SessionLivenessSignal(
        provider=inputs.provider,
        role=inputs.role,
        state=state,
        reason=reason,
        process_live=inputs.conductor_active,
        poll_age_seconds=inputs.poll_age_seconds,
    )


def _base_liveness_state(
    *,
    conductor_active: bool,
    runtime_active: bool,
    daemon_active: bool,
) -> tuple[SessionLivenessState, str]:
    if conductor_active and daemon_active:
        return "alive", "conductor and runtime daemons active"
    if conductor_active:
        return "degraded", "conductor active but runtime daemons stopped"
    if runtime_active:
        return "detached_runtime_only", "runtime activity present without live conductor"
    return "dead", "no conductor or runtime activity"


def _degrade_for_overdue_poll(
    *,
    state: SessionLivenessState,
    reason: str,
    poll_age_seconds: int | None,
    overdue_threshold_seconds: int,
) -> tuple[SessionLivenessState, str]:
    if state != "alive" or poll_age_seconds is None:
        return state, reason
    if poll_age_seconds <= overdue_threshold_seconds:
        return state, reason
    return (
        "degraded",
        f"poll overdue ({poll_age_seconds}s > {overdue_threshold_seconds}s)",
    )

__all__ = [
    "LIVE_SESSION_LIVENESS_STATES",
    "RUNTIME_PRESENT_LIVENESS_STATES",
    "SessionLivenessInputs",
    "SessionLivenessSignal",
    "SessionLivenessState",
    "classify_session_liveness",
]
