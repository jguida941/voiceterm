"""Bridge/event fallback helpers for current-session projection."""

from __future__ import annotations

from dataclasses import replace

from .current_session_support import compute_implementer_state_hash
from .handoff_constants import _is_substantive_text
from .reviewer_state_normalize import normalize_instruction_body
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


def merge_event_session_bridge_ack(
    *,
    event_session: ReviewCurrentSessionState | None,
    bridge_session: ReviewCurrentSessionState,
) -> ReviewCurrentSessionState | None:
    """Preserve a current bridge ACK when event state owns the instruction.

    Reviewer-checkpoint events carry reviewer-owned instruction/open-finding
    truth, but the live implementer ACK still lives in the bridge section until
    it is emitted as its own typed event. When both sources agree on the same
    instruction revision, keeping the bridge ACK prevents metadata-only
    reviewer checkpoints from falsely resetting the implementer to pending.
    """
    if event_session is None:
        return None
    if str(event_session.implementer_ack_state or "").strip() == "current":
        return event_session
    if str(bridge_session.implementer_ack_state or "").strip() != "current":
        return event_session
    if not _same_instruction_revision(event_session, bridge_session):
        return event_session
    bridge_ack = clean_section(bridge_session.implementer_ack)
    if not _is_substantive_text(bridge_ack):
        return event_session
    bridge_status = clean_section(bridge_session.implementer_status)
    return replace(
        event_session,
        implementer_status=(
            bridge_status
            if _is_substantive_text(bridge_status)
            else event_session.implementer_status
        ),
        implementer_ack=bridge_ack,
        implementer_ack_revision=bridge_session.implementer_ack_revision,
        implementer_ack_state="current",
        implementer_state_hash=bridge_session.implementer_state_hash,
        implementer_session_state=(
            event_session.implementer_session_state
            or bridge_session.implementer_session_state
        ),
        implementer_session_hint=(
            event_session.implementer_session_hint
            or bridge_session.implementer_session_hint
        ),
    )


def _same_instruction_revision(
    left: ReviewCurrentSessionState,
    right: ReviewCurrentSessionState,
) -> bool:
    left_revision = str(left.current_instruction_revision or "").strip()
    right_revision = str(right.current_instruction_revision or "").strip()
    return (
        bool(left_revision)
        and left_revision == right_revision
        and normalize_instruction_body(left.current_instruction)
        == normalize_instruction_body(right.current_instruction)
    )


def _status_is_placeholder(value: str) -> bool:
    normalized = clean_section(value).strip().lower()
    if not normalized:
        return True
    return normalized.lstrip("- ").strip() in {
        "status unavailable",
        "status unavailable.",
    }
