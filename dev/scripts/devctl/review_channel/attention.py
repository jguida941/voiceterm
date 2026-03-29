"""Attention-state policy for bridge-backed review-channel projections.

Routing logic lives here; all payload fields (owner, summary, recovery,
recommended_command) are looked up from the canonical ``STALE_PEER_RECOVERY``
contract in ``peer_liveness``.
"""

from __future__ import annotations

_NON_REVIEWER_CONTRACT_ERROR_PREFIXES = (
    "Live `Claude Ack` must include `instruction-rev:",
    "Live `Claude Ack` revision does not match the current reviewer instruction revision.",
    "Claude Status/Ack show implementer completion-stall language while ",
)
_RESETTABLE_IMPLEMENTER_ERROR_PREFIXES = (
    "Live `Claude Ack` must include `instruction-rev:",
    "Live `Claude Ack` revision does not match the current reviewer instruction revision.",
    "Claude Status/Ack show implementer completion-stall language while ",
    "Reviewer mode is `active_dual_agent` but no live repo-owned Codex or Claude conductor sessions are present.",
    "Repo-owned Codex conductor sessions are present, but the latest reviewer poll still comes from automation-only heartbeat refresh",
)
_RESETTABLE_IMPLEMENTER_SESSION_STATES = frozenset(
    {"interrupt_prompt", "waiting_for_user_input"}
)

from .peer_liveness import (
    CODEX_POLL_OVERDUE_AFTER_SECONDS,
    STALE_PEER_RECOVERY,
    AttentionStatus,
    CodexPollState,
    OverallLivenessState,
    ReviewerFreshness,
    reviewer_mode_is_active,
)


def derive_bridge_attention(
    bridge_liveness: dict[str, object],
    *,
    push_state: dict[str, object] | None = None,
    contract_errors: list[str] | None = None,
) -> dict[str, object]:
    """Translate bridge liveness into one compact operator-facing attention state."""
    overall_state = str(bridge_liveness.get("overall_state") or "unknown")
    codex_poll_state = str(bridge_liveness.get("codex_poll_state") or "unknown")
    claude_status_present = bool(bridge_liveness.get("claude_status_present"))
    claude_ack_present = bool(bridge_liveness.get("claude_ack_present"))
    claude_ack_current = bool(bridge_liveness.get("claude_ack_current"))

    reviewed_hash_current = bridge_liveness.get("reviewed_hash_current")
    reviewer_mode = str(bridge_liveness.get("reviewer_mode") or "")
    review_needed = bool(bridge_liveness.get("review_needed"))
    reviewer_supervisor_running = bool(
        bridge_liveness.get("reviewer_supervisor_running")
    )
    implementer_completion_stall = bool(
        bridge_liveness.get("implementer_completion_stall")
    )
    reviewer_freshness = str(bridge_liveness.get("reviewer_freshness") or "")
    poll_age = bridge_liveness.get("last_codex_poll_age_seconds")
    overdue_threshold = bridge_liveness.get(
        "reviewer_overdue_threshold_seconds",
        CODEX_POLL_OVERDUE_AFTER_SECONDS,
    )
    reviewer_mode_active = reviewer_mode_is_active(reviewer_mode)
    checkpoint_required, safe_to_continue_editing = _bridge_push_checkpoint_state(
        bridge_liveness,
        push_state=push_state,
    )
    publisher_running = bool(bridge_liveness.get("publisher_running"))
    reviewer_runtime_running = reviewer_supervisor_running or publisher_running
    raw_contract_errors = [str(error) for error in (contract_errors or [])]
    session_hint_state = _claude_session_hint_state(bridge_liveness)
    resettable_error_seen = any(
        _is_resettable_implementer_error(error) for error in raw_contract_errors
    )
    _active_contract_errors = _active_contract_errors_for_mode(
        contract_errors,
        reviewer_mode_active=reviewer_mode_active,
    )
    if not reviewer_mode_active:
        status = AttentionStatus.INACTIVE
    elif _requires_implementer_state_reset(
        bridge_liveness=bridge_liveness,
        reviewer_mode_active=reviewer_mode_active,
        review_needed=review_needed,
        implementer_state_invalid=(
            (not claude_ack_current)
            or implementer_completion_stall
            or session_hint_state in _RESETTABLE_IMPLEMENTER_SESSION_STATES
        ),
        resettable_error_seen=resettable_error_seen,
        session_hint_state=session_hint_state,
    ):
        status = AttentionStatus.IMPLEMENTER_STATE_RESET_REQUIRED
    elif (
        overall_state == OverallLivenessState.RUNTIME_MISSING
        or (reviewer_mode_active and not reviewer_runtime_running)
    ):
        status = AttentionStatus.RUNTIME_MISSING
    elif reviewer_freshness == ReviewerFreshness.MISSING or (
        not reviewer_freshness and codex_poll_state == CodexPollState.MISSING
    ):
        status = AttentionStatus.REVIEWER_HEARTBEAT_MISSING
    elif reviewer_freshness == ReviewerFreshness.OVERDUE or (
        not reviewer_freshness
        and overall_state == OverallLivenessState.STALE
        and isinstance(poll_age, (int, float))
        and isinstance(overdue_threshold, (int, float))
        and poll_age > overdue_threshold
    ):
        status = AttentionStatus.REVIEWER_OVERDUE
    elif reviewer_freshness == ReviewerFreshness.STALE or (
        not reviewer_freshness and overall_state == OverallLivenessState.STALE
    ):
        status = AttentionStatus.REVIEWER_HEARTBEAT_STALE
    elif reviewer_freshness == ReviewerFreshness.POLL_DUE or (
        not reviewer_freshness and codex_poll_state == CodexPollState.POLL_DUE
    ):
        status = AttentionStatus.REVIEWER_POLL_DUE
    elif _active_contract_errors:
        status = AttentionStatus.BRIDGE_CONTRACT_ERROR
    elif (
        reviewer_mode_active
        and review_needed
        and reviewer_supervisor_running
        and reviewed_hash_current is False
    ):
        status = AttentionStatus.REVIEW_FOLLOW_UP_REQUIRED
    elif (
        reviewer_mode_active
        and review_needed
        and not reviewer_supervisor_running
    ):
        status = AttentionStatus.REVIEWER_SUPERVISOR_REQUIRED
    elif checkpoint_required or not safe_to_continue_editing:
        status = AttentionStatus.CHECKPOINT_REQUIRED
    elif (
        reviewer_mode_active
        and codex_poll_state in {CodexPollState.FRESH, CodexPollState.POLL_DUE}
        and overall_state == OverallLivenessState.WAITING_ON_PEER
        and implementer_completion_stall
        and (not claude_ack_present or not claude_ack_current)
        and not review_needed
    ):
        status = AttentionStatus.IMPLEMENTER_RELAUNCH_REQUIRED
    elif (
        reviewer_mode_active
        and codex_poll_state in {CodexPollState.FRESH, CodexPollState.POLL_DUE}
        and implementer_completion_stall
        and claude_ack_current
        and not review_needed
    ):
        status = AttentionStatus.DUAL_AGENT_IDLE
    elif overall_state == OverallLivenessState.WAITING_ON_PEER and not claude_status_present:
        status = AttentionStatus.CLAUDE_STATUS_MISSING
    elif overall_state == OverallLivenessState.WAITING_ON_PEER and not claude_ack_present:
        status = AttentionStatus.CLAUDE_ACK_MISSING
    elif overall_state == OverallLivenessState.WAITING_ON_PEER and not claude_ack_current:
        if _active_contract_errors:
            status = AttentionStatus.BRIDGE_CONTRACT_ERROR
        else:
            status = AttentionStatus.CLAUDE_ACK_STALE
    elif _active_contract_errors:
        status = AttentionStatus.BRIDGE_CONTRACT_ERROR
    elif overall_state == OverallLivenessState.WAITING_ON_PEER:
        status = AttentionStatus.WAITING_ON_PEER
    elif reviewed_hash_current is False:
        status = AttentionStatus.REVIEWED_HASH_STALE
    elif implementer_completion_stall:
        status = AttentionStatus.IMPLEMENTER_COMPLETION_STALL
    elif (
        reviewer_mode_active
        and not publisher_running
    ):
        stop_reason = str(bridge_liveness.get("publisher_stop_reason") or "")
        if stop_reason == "failed_start":
            status = AttentionStatus.PUBLISHER_FAILED_START
        elif stop_reason == "detached_exit":
            status = AttentionStatus.PUBLISHER_DETACHED_EXIT
        else:
            status = AttentionStatus.PUBLISHER_MISSING
    else:
        status = AttentionStatus.HEALTHY

    return _attention_from_contract(status)


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
    safe_to_continue_editing = push_payload.get("safe_to_continue_editing")
    if safe_to_continue_editing is None:
        safe_to_continue_editing = not checkpoint_required
    return checkpoint_required, bool(safe_to_continue_editing)


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


def _reviewer_state_seeded(bridge_liveness: dict[str, object]) -> bool:
    return bool(bridge_liveness.get("current_instruction_revision")) and bool(
        bridge_liveness.get("last_reviewed_scope_present")
    )


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


def _attention_from_contract(status: str) -> dict[str, object]:
    """Build an attention payload from the canonical stale-peer recovery contract."""
    entry = STALE_PEER_RECOVERY.get(status, STALE_PEER_RECOVERY[AttentionStatus.HEALTHY])
    return {
        "status": status,
        "owner": entry["owner"],
        "summary": entry["summary"],
        "recommended_action": entry["recovery"],
        "recommended_command": entry.get("recommended_command"),
    }
