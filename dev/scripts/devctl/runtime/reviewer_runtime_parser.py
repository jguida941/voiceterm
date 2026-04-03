"""Reviewer-runtime payload normalization helpers."""

from __future__ import annotations

from collections.abc import Mapping

from .control_state import _int, _mapping, _string
from .review_state_parse_support import _bool
from .review_state_models import ReviewCurrentSessionState
from .reviewer_gate_logic import ReviewerRuntimeBlockInputs, reviewer_runtime_block_state
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
    attention_status = _string(attention.get("status"))
    if reviewer_runtime:
        return _typed_reviewer_runtime_state(
            reviewer_runtime=reviewer_runtime,
            bridge=bridge,
            bridge_liveness=bridge_liveness,
            current_session=current_session,
            attention_status=attention_status,
        )
    return _bridge_reviewer_runtime_state(
        bridge=bridge,
        bridge_liveness=bridge_liveness,
        current_session=current_session,
        attention=attention,
        attention_status=attention_status,
    )


def _typed_reviewer_runtime_state(
    *,
    reviewer_runtime: Mapping[str, object],
    bridge: Mapping[str, object],
    bridge_liveness: Mapping[str, object],
    current_session: ReviewCurrentSessionState,
    attention_status: str,
) -> ReviewerRuntimeContract:
    last_poll = _mapping(reviewer_runtime.get("last_poll"))
    rollover = _mapping(reviewer_runtime.get("rollover"))
    session_owner = _mapping(reviewer_runtime.get("session_owner"))
    review_acceptance = _mapping(reviewer_runtime.get("review_acceptance"))
    review_accepted = _bool(review_acceptance.get("review_accepted"))
    reviewer_mode = (
        _string(reviewer_runtime.get("reviewer_mode"))
        or _string(bridge.get("reviewer_mode"))
        or "single_agent"
    )
    effective_reviewer_mode = (
        _string(reviewer_runtime.get("effective_reviewer_mode"))
        or _string(bridge.get("effective_reviewer_mode"))
        or _string(bridge.get("reviewer_mode"))
        or "single_agent"
    )
    stale_reason = _stale_reason(
        reviewer_runtime.get("stale_reason"), attention_status=attention_status
    )
    implementer_ack_current = _implementer_ack_current(
        reviewer_runtime=reviewer_runtime,
        bridge=bridge,
        current_session=current_session,
    )
    implementation_blocked, implementation_block_reason = _implementation_block_state(
        reviewer_runtime=reviewer_runtime,
        current_session=current_session,
        reviewer_mode=reviewer_mode,
        effective_reviewer_mode=effective_reviewer_mode,
        implementer_ack_current=implementer_ack_current,
        attention_status=stale_reason,
    )
    return ReviewerRuntimeContract(
        reviewer_mode=reviewer_mode,
        effective_reviewer_mode=effective_reviewer_mode,
        reviewer_freshness=(
            _string(reviewer_runtime.get("reviewer_freshness"))
            or _string(bridge.get("reviewer_freshness"))
            or _string(bridge_liveness.get("reviewer_freshness"))
            or "unknown"
        ),
        stale_reason=stale_reason,
        implementer_ack_current=implementer_ack_current,
        implementation_blocked=implementation_blocked,
        implementation_block_reason=implementation_block_reason,
        last_poll=ReviewerLastPollState(
            last_codex_poll_utc=_string(last_poll.get("last_codex_poll_utc"))
            or _string(bridge.get("last_codex_poll_utc")),
            last_codex_poll_age_seconds=_int(last_poll.get("last_codex_poll_age_seconds"))
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
            terminal_window_id=_optional_int(session_owner.get("terminal_window_id")),
            script_path=_string(session_owner.get("script_path")),
        ),
        recovery_action_allowed=_string(reviewer_runtime.get("recovery_action_allowed")),
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


def _bridge_reviewer_runtime_state(
    *,
    bridge: Mapping[str, object],
    bridge_liveness: Mapping[str, object],
    current_session: ReviewCurrentSessionState,
    attention: Mapping[str, object],
    attention_status: str,
) -> ReviewerRuntimeContract:
    reviewer_mode = _string(bridge.get("reviewer_mode")) or "single_agent"
    effective_reviewer_mode = _string(bridge.get("effective_reviewer_mode")) or reviewer_mode
    implementer_ack_current = _implementer_ack_current(
        reviewer_runtime={},
        bridge=bridge,
        current_session=current_session,
    )
    implementation_blocked, implementation_block_reason = _implementation_block_state(
        reviewer_runtime={},
        current_session=current_session,
        reviewer_mode=reviewer_mode,
        effective_reviewer_mode=effective_reviewer_mode,
        implementer_ack_current=implementer_ack_current,
        attention_status=_stale_reason("", attention_status=attention_status),
    )
    review_accepted = _bool(bridge.get("review_accepted"))
    return ReviewerRuntimeContract(
        reviewer_mode=reviewer_mode,
        effective_reviewer_mode=effective_reviewer_mode,
        reviewer_freshness=_string(bridge.get("reviewer_freshness"))
        or _string(bridge_liveness.get("reviewer_freshness"))
        or "unknown",
        stale_reason=_stale_reason("", attention_status=attention_status),
        implementer_ack_current=implementer_ack_current,
        implementation_blocked=implementation_blocked,
        implementation_block_reason=implementation_block_reason,
        last_poll=ReviewerLastPollState(
            last_codex_poll_utc=_string(bridge.get("last_codex_poll_utc")),
            last_codex_poll_age_seconds=_int(bridge.get("last_codex_poll_age_seconds"))
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


def _stale_reason(value: object, *, attention_status: str) -> str:
    stale_reason = _string(value)
    if stale_reason or attention_status in {"", "healthy"}:
        return stale_reason
    return attention_status


def _implementation_block_state(
    *,
    reviewer_runtime: Mapping[str, object],
    current_session: ReviewCurrentSessionState,
    reviewer_mode: str,
    effective_reviewer_mode: str,
    implementer_ack_current: bool,
    attention_status: str,
) -> tuple[bool, str]:
    derived_blocked, derived_block_reason = reviewer_runtime_block_state(
        ReviewerRuntimeBlockInputs(
            reviewer_mode=reviewer_mode,
            effective_reviewer_mode=effective_reviewer_mode,
            implementer_ack_current=implementer_ack_current,
            attention_status=attention_status,
            implementer_status=current_session.implementer_status,
            implementer_ack=current_session.implementer_ack,
            implementer_ack_state=current_session.implementer_ack_state,
        )
    )
    implementation_blocked = (
        _bool(reviewer_runtime.get("implementation_blocked"))
        if "implementation_blocked" in reviewer_runtime
        else derived_blocked
    )
    implementation_block_reason = (
        _string(reviewer_runtime.get("implementation_block_reason"))
        if "implementation_block_reason" in reviewer_runtime
        else derived_block_reason
    )
    if implementation_blocked and not implementation_block_reason:
        return True, derived_block_reason
    if not implementation_blocked:
        return False, ""
    return True, implementation_block_reason


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return _int(value)


def _implementer_ack_current(
    *,
    reviewer_runtime: Mapping[str, object],
    bridge: Mapping[str, object],
    current_session: ReviewCurrentSessionState,
) -> bool:
    if "implementer_ack_current" in reviewer_runtime:
        return _bool(reviewer_runtime.get("implementer_ack_current"))
    ack_state = current_session.implementer_ack_state
    if ack_state in {"current", "stale", "pending"}:
        return ack_state == "current"
    return _bool(bridge.get("claude_ack_current"))
