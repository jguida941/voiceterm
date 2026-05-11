"""Authority helpers for choosing the current-session owner."""

from __future__ import annotations

from collections.abc import Mapping

from .reviewer_state_normalize import (
    normalize_instruction_body as _normalize_instruction_body,
)
from .status_projection_helpers import clean_section
from ..runtime.review_state_models import ReviewCurrentSessionState

_BRIDGE_ROLLOVER_FALLBACK_MARKERS = (
    "stop at a safe boundary",
    "relaunch before compaction",
    "await reviewer instruction refresh",
)


def prefer_bridge_current_session(
    *,
    prior_session: ReviewCurrentSessionState,
    bridge_session: ReviewCurrentSessionState,
    bridge_liveness: Mapping[str, object] | None = None,
) -> bool:
    """Return whether live bridge-backed reviewer state should replace the cache."""
    if not _current_session_has_authority_signal(bridge_session):
        return False
    bridge_key = _current_session_authority_key(bridge_session)
    if _bridge_rollover_fallback_instruction(bridge_session.current_instruction):
        return False
    if (
        str((bridge_liveness or {}).get("last_checkpoint_action") or "").strip()
        == "reviewer-checkpoint"
    ):
        return bridge_key != _current_session_authority_key(prior_session)
    reviewer_freshness = str(
        (bridge_liveness or {}).get("reviewer_freshness") or ""
    ).strip()
    if reviewer_freshness in {"stale", "overdue", "missing", "offline"}:
        return _current_session_is_placeholder(
            prior_session
        ) and _current_session_has_authority_signal(bridge_session)
    return bridge_key != _current_session_authority_key(prior_session)


def _bridge_rollover_fallback_instruction(current_instruction: str) -> bool:
    """Return whether the bridge instruction is a rollover/relaunch placeholder."""
    normalized = _normalize_instruction_body(current_instruction).lower()
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


def _current_session_is_placeholder(
    session: ReviewCurrentSessionState,
) -> bool:
    return not any(
        (
            _meaningful_instruction(session.current_instruction),
            _meaningful_text(session.implementer_status),
            _meaningful_findings(session.open_findings),
        )
    )


def _current_session_has_authority_signal(
    session: ReviewCurrentSessionState,
) -> bool:
    return any(
        (
            _meaningful_instruction(session.current_instruction),
            _meaningful_text(session.implementer_status),
            _meaningful_findings(session.open_findings),
        )
    )


def _meaningful_instruction(current_instruction: str) -> str:
    text = _normalize_instruction_body(current_instruction)
    return "" if text == "(missing)" else text


def _meaningful_text(value: str) -> str:
    text = clean_section(value)
    return "" if text == "(missing)" else text


def _meaningful_findings(open_findings: str) -> str:
    text = _meaningful_text(open_findings)
    return "" if text in {"", "none"} else text
