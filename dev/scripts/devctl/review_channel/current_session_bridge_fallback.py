"""Bridge/event fallback helpers for current-session projection."""

from __future__ import annotations

from dataclasses import replace

from .current_session_support import compute_implementer_state_hash
from .handoff_constants import _is_substantive_text
from .status_projection_helpers import clean_section
from ..runtime.review_state_models import ReviewCurrentSessionState
from ..runtime.review_state_semantics import classify_implementer_ack_state


def merge_bridge_session_event_fallback(
    *,
    bridge_session: ReviewCurrentSessionState,
    event_session: ReviewCurrentSessionState | None,
) -> ReviewCurrentSessionState:
    """Fill bridge placeholders from event-backed implementer state."""
    if event_session is None or not _status_is_placeholder(
        bridge_session.implementer_status
    ):
        return bridge_session

    merged_ack = clean_section(bridge_session.implementer_ack) or event_session.implementer_ack
    merged_status = event_session.implementer_status
    merged_ack_revision = (
        str(bridge_session.implementer_ack_revision or "").strip()
        or event_session.implementer_ack_revision
    )
    ack_current = bool(merged_ack) and (
        not bridge_session.current_instruction_revision
        or merged_ack_revision == bridge_session.current_instruction_revision
    )
    return replace(
        bridge_session,
        implementer_status=merged_status,
        implementer_ack=merged_ack,
        implementer_ack_revision=merged_ack_revision,
        implementer_ack_state=classify_implementer_ack_state(
            implementer_status=merged_status,
            implementer_ack=merged_ack,
            ack_current=ack_current,
            stale_label="stale",
            is_substantive_text=_is_substantive_text,
        ),
        implementer_state_hash=compute_implementer_state_hash(
            implementer_status=merged_status,
            implementer_ack=merged_ack,
        ),
        implementer_session_state=(
            bridge_session.implementer_session_state
            or event_session.implementer_session_state
        ),
        implementer_session_hint=(
            bridge_session.implementer_session_hint
            or event_session.implementer_session_hint
        ),
    )


def _status_is_placeholder(value: str) -> bool:
    normalized = clean_section(value).strip().lower()
    if not normalized:
        return True
    return normalized.lstrip("- ").strip() in {
        "status unavailable",
        "status unavailable.",
    }
