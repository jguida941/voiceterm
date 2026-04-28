"""Typed implementer-ACK freshness authority for review-channel consumers."""

from __future__ import annotations

from ..runtime.review_state_models import ReviewCurrentSessionState
from ..runtime.review_state_parser_rows import current_session_state_from_payload

_NON_CURRENT_ACK_STATES = frozenset({"missing", "pending", "unknown"})


def is_implementer_ack_current(cs: ReviewCurrentSessionState) -> bool:
    """Typed current-session ACK freshness predicate."""
    ack_state = _ack_state(cs)

    if ack_state == "current":
        return True

    if ack_state in _NON_CURRENT_ACK_STATES:
        return False

    return _ack_revision_matches_instruction(cs)


def current_session_from_mapping(
    value,
) -> ReviewCurrentSessionState:
    """Build a typed current-session row from a JSON-like mapping."""
    return current_session_state_from_payload(
        current_session=value if isinstance(value, dict) else {},
        bridge={},
        collaboration={},
    )


def _same_revision(left: object, right: object) -> bool:
    left_text = _text(left)
    right_text = _text(right)

    return bool(left_text and right_text and left_text == right_text)


def _ack_state(cs: ReviewCurrentSessionState) -> str:
    return _text(cs.implementer_ack_state).lower()


def _ack_revision_matches_instruction(cs: ReviewCurrentSessionState) -> bool:
    return _same_revision(
        cs.implementer_ack_revision,
        cs.current_instruction_revision,
    )


def _text(value: object) -> str:
    if value is None:
        return ""

    return str(value).strip()


__all__ = [
    "current_session_from_mapping",
    "is_implementer_ack_current",
]
