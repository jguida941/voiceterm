"""Carry reducer-proven ACK state through event projection enrichment."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from ..runtime.review_state_models import ReviewCurrentSessionState
from .ack_freshness_authority import (
    current_session_from_mapping,
    is_implementer_ack_current,
)
from .current_session_support import compute_implementer_state_hash
from .implementer_ack_events import latest_implementer_ack_payload
from .status_projection_helpers import clean_section


def preserve_reducer_implementer_ack(
    current_session: ReviewCurrentSessionState,
    review_state: Mapping[str, object],
) -> ReviewCurrentSessionState:
    """Overlay reducer-proven ACK fields onto the enriched current session."""
    event_session = _event_implementer_ack_session(current_session, review_state)
    if event_session is not None:
        return event_session

    reduced_session = current_session_from_mapping(
        _mapping(review_state.get("current_session"))
    )

    if not is_implementer_ack_current(reduced_session):
        return current_session

    ack = clean_section(reduced_session.implementer_ack)
    revision = reduced_session.implementer_ack_revision.strip()
    if not ack or not revision:
        return current_session

    status = clean_section(reduced_session.implementer_status)
    status = status or current_session.implementer_status

    return replace(
        current_session,
        implementer_status=status,
        implementer_ack=ack,
        implementer_ack_revision=revision,
        implementer_ack_state="current",
        implementer_state_hash=compute_implementer_state_hash(
            implementer_status=status,
            implementer_ack=ack,
        ),
    )


def _event_implementer_ack_session(
    current_session: ReviewCurrentSessionState,
    review_state: Mapping[str, object],
) -> ReviewCurrentSessionState | None:
    revision = current_session.current_instruction_revision.strip()
    if not revision:
        return None
    events = review_state.get("_events")
    payload: Mapping[str, object] = {}
    if isinstance(events, (list, tuple)):
        payload = latest_implementer_ack_payload(
            tuple(event for event in events if isinstance(event, dict)),
            current_instruction_revision=revision,
        )
    if not payload:
        latest = _mapping(review_state.get("latest_implementer_ack"))
        if str(latest.get("current_instruction_revision") or "").strip() == revision:
            payload = latest
    ack = clean_section(payload.get("implementer_ack") if payload else "")
    if not ack:
        return None
    status = clean_section(current_session.implementer_status)
    return replace(
        current_session,
        implementer_status=status,
        implementer_ack=ack,
        implementer_ack_revision=revision,
        implementer_ack_state="current",
        implementer_state_hash=compute_implementer_state_hash(
            implementer_status=status,
            implementer_ack=ack,
        ),
    )


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


__all__ = ["preserve_reducer_implementer_ack"]
