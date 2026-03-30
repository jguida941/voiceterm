"""Shared helper functions for bridge-attention classification."""

from __future__ import annotations

from .ack_contract import ACK_REVISION_REQUIREMENT_PREFIX

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
RESETTABLE_IMPLEMENTER_SESSION_STATES = frozenset(
    {"interrupt_prompt", "waiting_for_user_input"}
)


def active_contract_errors_for_mode(
    contract_errors: list[str] | None,
    *,
    reviewer_mode_active: bool,
) -> list[str] | None:
    """Return reviewer-owned contract errors that should block active mode."""
    if not reviewer_mode_active or not contract_errors:
        return None
    return [
        error
        for error in (contract_errors or [])
        if not str(error).startswith(_NON_REVIEWER_CONTRACT_ERROR_PREFIXES)
    ]


def blocking_contract_errors(
    active_contract_errors: list[str] | None,
    *,
    implementer_state_pending: bool,
) -> bool:
    """Return True when active contract errors should still block attention."""
    if not active_contract_errors:
        return False
    if not implementer_state_pending:
        return True
    return not all(
        is_resettable_implementer_error(error) for error in active_contract_errors
    )


def claude_session_hint_state(bridge_liveness: dict[str, object]) -> str:
    """Return the Claude session hint state when present."""
    hints = bridge_liveness.get("session_state_hints")
    if not isinstance(hints, dict):
        return ""

    claude_hint = hints.get("claude")
    if not isinstance(claude_hint, dict):
        return ""

    return str(claude_hint.get("state") or "")


def implementer_state_pending(bridge_liveness: dict[str, object]) -> bool:
    """Return True when typed bridge state already shows canonical pending reset."""
    return bool(bridge_liveness.get("implementer_state_pending"))


def is_resettable_implementer_error(error: str) -> bool:
    """Return True when one error qualifies for resettable implementer recovery."""
    return str(error).startswith(_RESETTABLE_IMPLEMENTER_ERROR_PREFIXES)
