"""Nested state-row builders for reviewer-runtime parser."""

from __future__ import annotations

from collections.abc import Mapping

from .control_state import _int, _string
from .reviewer_runtime_models import (
    ReviewerLastPollState,
    ReviewerRolloverState,
    ReviewerSessionOwnerState,
)


def typed_last_poll_state(
    *,
    last_poll: Mapping[str, object],
    bridge: Mapping[str, object],
    bridge_liveness: Mapping[str, object],
) -> ReviewerLastPollState:
    """Build last-poll state from typed runtime payload plus bridge fallback."""
    return ReviewerLastPollState(
        last_codex_poll_utc=_string(last_poll.get("last_codex_poll_utc"))
        or _string(bridge.get("last_codex_poll_utc")),
        last_codex_poll_age_seconds=_int(
            last_poll.get("last_codex_poll_age_seconds")
        )
        or _int(bridge.get("last_codex_poll_age_seconds"))
        or _int(bridge_liveness.get("last_codex_poll_age_seconds")),
        last_reviewer_poll_utc=_string(last_poll.get("last_reviewer_poll_utc"))
        or _string(last_poll.get("last_codex_poll_utc"))
        or _string(bridge.get("last_reviewer_poll_utc"))
        or _string(bridge.get("last_codex_poll_utc")),
        last_reviewer_poll_age_seconds=_int(
            last_poll.get("last_reviewer_poll_age_seconds")
        )
        or _int(last_poll.get("last_codex_poll_age_seconds"))
        or _int(bridge.get("last_reviewer_poll_age_seconds"))
        or _int(bridge.get("last_codex_poll_age_seconds"))
        or _int(bridge_liveness.get("last_reviewer_poll_age_seconds"))
        or _int(bridge_liveness.get("last_codex_poll_age_seconds")),
    )


def bridge_last_poll_state(
    *,
    bridge: Mapping[str, object],
    bridge_liveness: Mapping[str, object],
) -> ReviewerLastPollState:
    """Build last-poll state from bridge fields."""
    return ReviewerLastPollState(
        last_codex_poll_utc=_string(bridge.get("last_codex_poll_utc")),
        last_codex_poll_age_seconds=_int(bridge.get("last_codex_poll_age_seconds"))
        or _int(bridge_liveness.get("last_codex_poll_age_seconds")),
        last_reviewer_poll_utc=_string(bridge.get("last_reviewer_poll_utc"))
        or _string(bridge.get("last_codex_poll_utc")),
        last_reviewer_poll_age_seconds=_int(
            bridge.get("last_reviewer_poll_age_seconds")
        )
        or _int(bridge.get("last_codex_poll_age_seconds"))
        or _int(bridge_liveness.get("last_reviewer_poll_age_seconds"))
        or _int(bridge_liveness.get("last_codex_poll_age_seconds")),
    )


def rollover_state(rollover: Mapping[str, object]) -> ReviewerRolloverState:
    """Build reviewer rollover state."""
    return ReviewerRolloverState(
        rollover_id=_string(rollover.get("rollover_id")),
        ack_pending=_bool(rollover.get("ack_pending")),
        trigger=_string(rollover.get("trigger")),
    )


def session_owner_state(
    session_owner: Mapping[str, object],
) -> ReviewerSessionOwnerState:
    """Build session-owner state from typed payload."""
    return ReviewerSessionOwnerState(
        provider=_string(session_owner.get("provider")),
        session_name=_string(session_owner.get("session_name")),
        session_pid=_optional_int(session_owner.get("session_pid")),
        terminal_window_id=_optional_int(session_owner.get("terminal_window_id")),
        script_path=_string(session_owner.get("script_path")),
        session_visibility=_string(session_owner.get("session_visibility"))
        or "unknown",
    )


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return _int(value)


def _bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


__all__ = [
    "bridge_last_poll_state",
    "rollover_state",
    "session_owner_state",
    "typed_last_poll_state",
]
