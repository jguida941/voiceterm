"""Shared semantics for typed review-state placeholder and pending values."""

from __future__ import annotations

from collections.abc import Callable


def is_pending_placeholder(text: str | None) -> bool:
    """Return True when text is the canonical pending placeholder."""
    if not text:
        return False
    return text.strip().lstrip("-").strip().lower() == "pending"


def is_pending_implementer_state(
    *,
    implementer_status: str | None,
    implementer_ack: str | None,
    implementer_ack_state: str | None = "",
) -> bool:
    """Return True when the implementer was freshly reset to pending."""
    if str(implementer_ack_state or "").strip().lower() == "pending":
        return True
    return is_pending_placeholder(implementer_status) and is_pending_placeholder(
        implementer_ack
    )


def classify_implementer_ack_state(
    *,
    implementer_status: str,
    implementer_ack: str,
    implementer_ack_state: str = "",
    ack_current: bool,
    stale_label: str,
    is_substantive_text: Callable[[str | None], bool],
) -> str:
    """Return the shared typed ACK-state label for current-session consumers."""
    if is_pending_implementer_state(
        implementer_status=implementer_status,
        implementer_ack=implementer_ack,
        implementer_ack_state=implementer_ack_state,
    ):
        return "pending"
    if not is_substantive_text(implementer_ack):
        return "missing"
    if ack_current:
        return "current"
    return stale_label
