"""Authority helpers for choosing the current-session owner."""

from __future__ import annotations

from .reviewer_state_normalize import (
    normalize_instruction_body as _normalize_instruction_body,
)
from .status_projection_helpers import clean_section
from ..runtime.review_state_models import ReviewCurrentSessionState

_BRIDGE_ROLLOVER_FALLBACK_MARKERS = (
    "stop at a safe boundary",
    "relaunch before compaction",
)


def prefer_bridge_current_session(
    *,
    prior_session: ReviewCurrentSessionState,
    bridge_session: ReviewCurrentSessionState,
) -> bool:
    """Return whether live bridge-backed reviewer state should replace the cache."""
    bridge_key = _current_session_authority_key(bridge_session)
    if not any(bridge_key):
        return False
    if _bridge_rollover_fallback_instruction(bridge_session.current_instruction):
        return False
    return bridge_key != _current_session_authority_key(prior_session)


def _bridge_rollover_fallback_instruction(current_instruction: str) -> bool:
    """Return whether the bridge instruction is a rollover/relaunch placeholder."""
    normalized = _normalize_instruction_body(current_instruction)
    return any(marker in normalized for marker in _BRIDGE_ROLLOVER_FALLBACK_MARKERS)


def _current_session_authority_key(
    session: ReviewCurrentSessionState,
) -> tuple[str, ...]:
    return (
        _normalize_instruction_body(session.current_instruction),
        str(session.current_instruction_revision or "").strip(),
        clean_section(session.implementer_status),
        clean_section(session.implementer_ack),
        str(session.implementer_ack_revision or "").strip(),
        str(session.implementer_ack_state or "").strip(),
        str(session.implementer_state_hash or "").strip(),
        str(session.implementer_session_state or "").strip(),
        clean_section(session.implementer_session_hint),
        clean_section(session.open_findings),
        clean_section(session.last_reviewed_scope),
    )
