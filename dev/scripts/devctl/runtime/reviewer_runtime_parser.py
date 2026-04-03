"""Reviewer-runtime payload normalization helpers."""

from __future__ import annotations

from collections.abc import Mapping

from .control_state import _int, _mapping, _string
from .review_state_parse_support import _bool
from .review_state_models import ReviewCurrentSessionState
from .reviewer_runtime_models import (
    ReviewerAcceptanceState,
    ReviewerLastPollState,
    ReviewerRolloverState,
    ReviewerRuntimeContract,
    ReviewerSessionOwnerState,
)


def reviewer_runtime_state_from_payload(
    *,
    reviewer_runtime: Mapping[str, object],
    bridge: Mapping[str, object],
    bridge_liveness: Mapping[str, object],
    current_session: ReviewCurrentSessionState,
    attention: Mapping[str, object],
) -> ReviewerRuntimeContract:
    """Build the typed reviewer-runtime state from review-state payload fields."""
    if reviewer_runtime:
        last_poll = _mapping(reviewer_runtime.get("last_poll"))
        rollover = _mapping(reviewer_runtime.get("rollover"))
        session_owner = _mapping(reviewer_runtime.get("session_owner"))
        review_acceptance = _mapping(reviewer_runtime.get("review_acceptance"))
        review_accepted = _bool(review_acceptance.get("review_accepted"))
        return ReviewerRuntimeContract(
            reviewer_mode=_string(reviewer_runtime.get("reviewer_mode"))
            or _string(bridge.get("reviewer_mode"))
            or "single_agent",
            effective_reviewer_mode=_string(
                reviewer_runtime.get("effective_reviewer_mode")
            )
            or _string(bridge.get("effective_reviewer_mode"))
            or _string(bridge.get("reviewer_mode"))
            or "single_agent",
            reviewer_freshness=_string(reviewer_runtime.get("reviewer_freshness"))
            or _string(bridge.get("reviewer_freshness"))
            or _string(bridge_liveness.get("reviewer_freshness"))
            or "unknown",
            stale_reason=_string(reviewer_runtime.get("stale_reason")),
            last_poll=ReviewerLastPollState(
                last_codex_poll_utc=_string(last_poll.get("last_codex_poll_utc"))
                or _string(bridge.get("last_codex_poll_utc")),
                last_codex_poll_age_seconds=_int(
                    last_poll.get("last_codex_poll_age_seconds")
                )
                or _int(bridge.get("last_codex_poll_age_seconds"))
                or _int(bridge_liveness.get("last_codex_poll_age_seconds")),
            ),
            rollover=ReviewerRolloverState(
                rollover_id=_string(rollover.get("rollover_id")),
                ack_pending=_bool(rollover.get("ack_pending")),
                trigger=_string(rollover.get("trigger")),
            ),
            session_owner=ReviewerSessionOwnerState(
                provider=_string(session_owner.get("provider")),
                session_name=_string(session_owner.get("session_name")),
                session_pid=_optional_int(session_owner.get("session_pid")),
                terminal_window_id=_optional_int(
                    session_owner.get("terminal_window_id")
                ),
                script_path=_string(session_owner.get("script_path")),
            ),
            recovery_action_allowed=_string(
                reviewer_runtime.get("recovery_action_allowed")
            ),
            review_acceptance=ReviewerAcceptanceState(
                current_verdict=_string(review_acceptance.get("current_verdict")),
                open_findings=_string(review_acceptance.get("open_findings"))
                or current_session.open_findings,
                review_accepted=review_accepted,
            ),
            publish_clear=(
                _bool(reviewer_runtime.get("publish_clear"))
                if "publish_clear" in reviewer_runtime
                else review_accepted
            ),
        )

    attention_status = _string(attention.get("status"))
    stale_reason = "" if attention_status in {"", "healthy"} else attention_status
    review_accepted = _bool(bridge.get("review_accepted"))
    return ReviewerRuntimeContract(
        reviewer_mode=_string(bridge.get("reviewer_mode")) or "single_agent",
        effective_reviewer_mode=_string(bridge.get("effective_reviewer_mode"))
        or _string(bridge.get("reviewer_mode"))
        or "single_agent",
        reviewer_freshness=_string(bridge.get("reviewer_freshness"))
        or _string(bridge_liveness.get("reviewer_freshness"))
        or "unknown",
        stale_reason=stale_reason,
        last_poll=ReviewerLastPollState(
            last_codex_poll_utc=_string(bridge.get("last_codex_poll_utc")),
            last_codex_poll_age_seconds=_int(
                bridge.get("last_codex_poll_age_seconds")
            )
            or _int(bridge_liveness.get("last_codex_poll_age_seconds")),
        ),
        recovery_action_allowed=_string(attention.get("recommended_command")),
        review_acceptance=ReviewerAcceptanceState(
            current_verdict="",
            open_findings=current_session.open_findings
            or _string(bridge.get("open_findings")),
            review_accepted=review_accepted,
        ),
        publish_clear=review_accepted,
    )


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return _int(value)
