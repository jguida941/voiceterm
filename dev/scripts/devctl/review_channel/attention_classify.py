"""Priority-ordered attention status classification for bridge liveness.

Extracted from ``attention.py`` to keep per-module size under the code-shape
soft limit while each classifier function stays focused on one concern.
"""

from __future__ import annotations

from dataclasses import dataclass

from .ack_contract import ACK_REVISION_REQUIREMENT_PREFIX
from .peer_liveness import (
    AttentionStatus,
    CODEX_POLL_OVERDUE_AFTER_SECONDS,
    CodexPollState,
    OverallLivenessState,
    ReviewerFreshness,
    reviewer_mode_is_active,
)

_NON_REVIEWER_CONTRACT_ERROR_PREFIXES = (
    ACK_REVISION_REQUIREMENT_PREFIX,
    "Live `Claude Ack` revision does not match the current reviewer instruction revision.",
    "Claude Status/Ack show implementer completion-stall language while ",
)
_RESETTABLE_IMPLEMENTER_ERROR_PREFIXES = (
    ACK_REVISION_REQUIREMENT_PREFIX,
    "Live `Claude Ack` revision does not match the current reviewer instruction revision.",
    "Claude Status/Ack show implementer completion-stall language while ",
    "Reviewer mode is `active_dual_agent` but no live repo-owned Codex or Claude conductor sessions are present.",
    "Repo-owned Codex conductor sessions are present, but the latest reviewer poll still comes from automation-only heartbeat refresh",
)
_RESETTABLE_IMPLEMENTER_SESSION_STATES = frozenset(
    {"interrupt_prompt", "waiting_for_user_input"}
)


@dataclass(frozen=True, slots=True)
class BridgeAttentionContext:
    """Pre-extracted fields from bridge_liveness used by status classification."""

    overall_state: str
    codex_poll_state: str
    claude_status_present: bool
    claude_ack_present: bool
    claude_ack_current: bool
    reviewed_hash_current: object
    reviewer_mode_active: bool
    review_needed: bool
    reviewer_supervisor_running: bool
    implementer_completion_stall: bool
    reviewer_freshness: str
    poll_age: object
    overdue_threshold: object
    checkpoint_required: bool
    safe_to_continue_editing: bool
    publisher_running: bool
    reviewer_runtime_running: bool
    resettable_error_seen: bool
    session_hint_state: str
    active_contract_errors: list[str] | None
    bridge_liveness: dict[str, object]


def _bridge_push_checkpoint_state(
    bridge_liveness: dict[str, object],
    *,
    push_state: dict[str, object] | None,
) -> tuple[bool, bool]:
    push_payload = push_state
    if push_payload is None:
        maybe_push = bridge_liveness.get("push_enforcement")
        push_payload = maybe_push if isinstance(maybe_push, dict) else None
    if push_payload is None:
        push_payload = bridge_liveness

    checkpoint_required = bool(push_payload.get("checkpoint_required"))
    safe_to_edit = push_payload.get("safe_to_continue_editing")
    if safe_to_edit is None:
        safe_to_edit = not checkpoint_required

    return checkpoint_required, bool(safe_to_edit)


def _substantive_contract_errors(
    contract_errors: list[str] | None,
) -> list[str]:
    return [
        error
        for error in (contract_errors or [])
        if not str(error).startswith(_NON_REVIEWER_CONTRACT_ERROR_PREFIXES)
    ]


def _active_contract_errors_for_mode(
    contract_errors: list[str] | None,
    *,
    reviewer_mode_active: bool,
) -> list[str] | None:
    if not reviewer_mode_active or not contract_errors:
        return None
    return _substantive_contract_errors(contract_errors)


def _is_resettable_implementer_error(error: str) -> bool:
    return str(error).startswith(_RESETTABLE_IMPLEMENTER_ERROR_PREFIXES)


def _claude_session_hint_state(bridge_liveness: dict[str, object]) -> str:
    hints = bridge_liveness.get("session_state_hints")
    if not isinstance(hints, dict):
        return ""

    claude_hint = hints.get("claude")
    if not isinstance(claude_hint, dict):
        return ""

    return str(claude_hint.get("state") or "")


def _reviewer_state_seeded(bridge_liveness: dict[str, object]) -> bool:
    return bool(bridge_liveness.get("current_instruction_revision")) and bool(
        bridge_liveness.get("last_reviewed_scope_present")
    )


def _requires_implementer_state_reset(
    *,
    bridge_liveness: dict[str, object],
    reviewer_mode_active: bool,
    review_needed: bool,
    implementer_state_invalid: bool,
    resettable_error_seen: bool,
    session_hint_state: str,
) -> bool:
    if not reviewer_mode_active or review_needed:
        return False
    if not _reviewer_state_seeded(bridge_liveness):
        return False
    if not implementer_state_invalid:
        return False
    if not resettable_error_seen:
        return False

    return (
        session_hint_state in _RESETTABLE_IMPLEMENTER_SESSION_STATES
        or bool(bridge_liveness.get("poll_status_automation_only"))
        or not bool(bridge_liveness.get("claude_conductor_active"))
    )


def extract_attention_context(
    bridge_liveness: dict[str, object],
    *,
    push_state: dict[str, object] | None,
    contract_errors: list[str] | None,
) -> BridgeAttentionContext:
    """Extract all fields needed for attention status classification."""
    reviewer_mode = str(bridge_liveness.get("reviewer_mode") or "")
    reviewer_mode_active = reviewer_mode_is_active(reviewer_mode)
    supervisor_running = bool(bridge_liveness.get("reviewer_supervisor_running"))
    publisher_running = bool(bridge_liveness.get("publisher_running"))
    raw_errors = [str(e) for e in (contract_errors or [])]

    checkpoint_required, safe_to_edit = _bridge_push_checkpoint_state(
        bridge_liveness, push_state=push_state,
    )

    return BridgeAttentionContext(
        overall_state=str(bridge_liveness.get("overall_state") or "unknown"),
        codex_poll_state=str(bridge_liveness.get("codex_poll_state") or "unknown"),
        claude_status_present=bool(bridge_liveness.get("claude_status_present")),
        claude_ack_present=bool(bridge_liveness.get("claude_ack_present")),
        claude_ack_current=bool(bridge_liveness.get("claude_ack_current")),
        reviewed_hash_current=bridge_liveness.get("reviewed_hash_current"),
        reviewer_mode_active=reviewer_mode_active,
        review_needed=bool(bridge_liveness.get("review_needed")),
        reviewer_supervisor_running=supervisor_running,
        implementer_completion_stall=bool(
            bridge_liveness.get("implementer_completion_stall")
        ),
        reviewer_freshness=str(bridge_liveness.get("reviewer_freshness") or ""),
        poll_age=bridge_liveness.get("last_codex_poll_age_seconds"),
        overdue_threshold=bridge_liveness.get(
            "reviewer_overdue_threshold_seconds", CODEX_POLL_OVERDUE_AFTER_SECONDS,
        ),
        checkpoint_required=checkpoint_required,
        safe_to_continue_editing=safe_to_edit,
        publisher_running=publisher_running,
        reviewer_runtime_running=supervisor_running or publisher_running,
        resettable_error_seen=any(
            _is_resettable_implementer_error(e) for e in raw_errors
        ),
        session_hint_state=_claude_session_hint_state(bridge_liveness),
        active_contract_errors=_active_contract_errors_for_mode(
            contract_errors, reviewer_mode_active=reviewer_mode_active,
        ),
        bridge_liveness=bridge_liveness,
    )


def _classify_reviewer_freshness(ctx: BridgeAttentionContext) -> str | None:
    """Check reviewer heartbeat freshness conditions."""
    if ctx.reviewer_freshness == ReviewerFreshness.MISSING or (
        not ctx.reviewer_freshness and ctx.codex_poll_state == CodexPollState.MISSING
    ):
        return AttentionStatus.REVIEWER_HEARTBEAT_MISSING

    if ctx.reviewer_freshness == ReviewerFreshness.OVERDUE or (
        not ctx.reviewer_freshness
        and ctx.overall_state == OverallLivenessState.STALE
        and isinstance(ctx.poll_age, (int, float))
        and isinstance(ctx.overdue_threshold, (int, float))
        and ctx.poll_age > ctx.overdue_threshold
    ):
        return AttentionStatus.REVIEWER_OVERDUE

    if ctx.reviewer_freshness == ReviewerFreshness.STALE or (
        not ctx.reviewer_freshness and ctx.overall_state == OverallLivenessState.STALE
    ):
        return AttentionStatus.REVIEWER_HEARTBEAT_STALE

    if ctx.reviewer_freshness == ReviewerFreshness.POLL_DUE or (
        not ctx.reviewer_freshness and ctx.codex_poll_state == CodexPollState.POLL_DUE
    ):
        return AttentionStatus.REVIEWER_POLL_DUE

    return None


def _classify_peer_waiting(ctx: BridgeAttentionContext) -> str | None:
    """Check peer-waiting conditions when overall_state is WAITING_ON_PEER."""
    if ctx.overall_state != OverallLivenessState.WAITING_ON_PEER:
        return None

    if not ctx.claude_status_present:
        return AttentionStatus.CLAUDE_STATUS_MISSING

    if not ctx.claude_ack_present:
        return AttentionStatus.CLAUDE_ACK_MISSING

    if not ctx.claude_ack_current:
        if ctx.active_contract_errors:
            return AttentionStatus.BRIDGE_CONTRACT_ERROR
        return AttentionStatus.CLAUDE_ACK_STALE

    return AttentionStatus.WAITING_ON_PEER


def _classify_publisher_state(ctx: BridgeAttentionContext) -> str | None:
    """Check stopped-publisher conditions."""
    if not ctx.reviewer_mode_active or ctx.publisher_running:
        return None

    stop_reason = str(ctx.bridge_liveness.get("publisher_stop_reason") or "")

    if stop_reason == "failed_start":
        return AttentionStatus.PUBLISHER_FAILED_START
    if stop_reason == "detached_exit":
        return AttentionStatus.PUBLISHER_DETACHED_EXIT

    return AttentionStatus.PUBLISHER_MISSING


def classify_attention_status(
    ctx: BridgeAttentionContext,
) -> str:
    """Priority-ordered attention status classification."""
    if not ctx.reviewer_mode_active:
        return AttentionStatus.INACTIVE

    if _requires_implementer_state_reset(
        bridge_liveness=ctx.bridge_liveness,
        reviewer_mode_active=ctx.reviewer_mode_active,
        review_needed=ctx.review_needed,
        implementer_state_invalid=(
            (not ctx.claude_ack_current)
            or ctx.implementer_completion_stall
            or ctx.session_hint_state in _RESETTABLE_IMPLEMENTER_SESSION_STATES
        ),
        resettable_error_seen=ctx.resettable_error_seen,
        session_hint_state=ctx.session_hint_state,
    ):
        return AttentionStatus.IMPLEMENTER_STATE_RESET_REQUIRED

    if (
        ctx.overall_state == OverallLivenessState.RUNTIME_MISSING
        or not ctx.reviewer_runtime_running
    ):
        return AttentionStatus.RUNTIME_MISSING

    freshness = _classify_reviewer_freshness(ctx)
    if freshness is not None:
        return freshness

    if ctx.active_contract_errors:
        return AttentionStatus.BRIDGE_CONTRACT_ERROR

    if ctx.review_needed and ctx.reviewer_supervisor_running and ctx.reviewed_hash_current is False:
        return AttentionStatus.REVIEW_FOLLOW_UP_REQUIRED

    if ctx.review_needed and not ctx.reviewer_supervisor_running:
        return AttentionStatus.REVIEWER_SUPERVISOR_REQUIRED

    if ctx.checkpoint_required or not ctx.safe_to_continue_editing:
        return AttentionStatus.CHECKPOINT_REQUIRED

    fresh_poll = ctx.codex_poll_state in {CodexPollState.FRESH, CodexPollState.POLL_DUE}

    if (
        fresh_poll
        and ctx.overall_state == OverallLivenessState.WAITING_ON_PEER
        and ctx.implementer_completion_stall
        and (not ctx.claude_ack_present or not ctx.claude_ack_current)
        and not ctx.review_needed
    ):
        return AttentionStatus.IMPLEMENTER_RELAUNCH_REQUIRED

    if (
        fresh_poll
        and ctx.implementer_completion_stall
        and ctx.claude_ack_current
        and not ctx.review_needed
    ):
        return AttentionStatus.DUAL_AGENT_IDLE

    peer_status = _classify_peer_waiting(ctx)
    if peer_status is not None:
        return peer_status

    if ctx.active_contract_errors:
        return AttentionStatus.BRIDGE_CONTRACT_ERROR

    if ctx.reviewed_hash_current is False:
        return AttentionStatus.REVIEWED_HASH_STALE

    if ctx.implementer_completion_stall:
        return AttentionStatus.IMPLEMENTER_COMPLETION_STALL

    publisher_status = _classify_publisher_state(ctx)
    if publisher_status is not None:
        return publisher_status

    return AttentionStatus.HEALTHY
