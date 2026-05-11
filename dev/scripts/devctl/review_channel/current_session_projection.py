"""Shared current-session helpers for review-channel projections."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

from .current_session_authority import prefer_bridge_current_session
from .current_session_bridge_state import (
    bridge_implementer_state_hash,
    build_bridge_current_session,
)
from .current_session_bridge_fallback import merge_bridge_session_event_fallback
from .current_session_event_state import (
    build_event_current_session,
    event_current_session_candidate,
    event_session_clears_packet_truth,
    event_session_has_active_instruction,
)
from .current_session_render import (
    append_current_session_markdown,
    current_focus_line,
)
from .current_session_support import (
    compute_implementer_state_hash,
    current_session_authority_drift_warning,
    event_agent_status,
    event_claude_ack,
    event_current_instruction,
    event_open_findings,
    instruction_revision_reuse_warning,
    prior_typed_current_session,
)
from .handoff import BridgeSnapshot
from ..runtime.review_state_models import ReviewCurrentSessionState


def resolve_current_session_authority(
    *,
    snapshot: BridgeSnapshot,
    bridge_liveness: Mapping[str, object],
    prior_review_state: Mapping[str, object] | None = None,
) -> ReviewCurrentSessionState:
    """Return the canonical current-session owner for bridge-backed status."""
    event_session = event_current_session_candidate(
        review_state=prior_review_state,
        bridge_liveness=bridge_liveness,
    )
    bridge_session = build_bridge_current_session(
        snapshot,
        bridge_liveness,
        prior_review_state=prior_review_state,
    )
    bridge_session = merge_bridge_session_event_fallback(
        bridge_session=bridge_session,
        event_session=event_session,
    )
    prior_session = prior_typed_current_session(prior_review_state)
    if prior_session is None:
        prior_session = event_session
    if prior_session is None:
        return bridge_session
    if event_session_clears_packet_truth(
        review_state=prior_review_state,
        event_session=event_session,
    ):
        return event_session
    if event_session_has_active_instruction(event_session):
        bridge_should_override_event = prefer_bridge_current_session(
            prior_session=event_session,
            bridge_session=bridge_session,
            bridge_liveness=bridge_liveness,
        )
        if not bridge_should_override_event:
            return event_session
    if prefer_bridge_current_session(
        prior_session=prior_session,
        bridge_session=bridge_session,
        bridge_liveness=bridge_liveness,
    ):
        return bridge_session
    return prior_session


def current_session_payload(
    state: ReviewCurrentSessionState,
) -> dict[str, object]:
    """Serialize typed current-session state for JSON projections."""
    return asdict(state)


def current_session_mapping(
    review_state: Mapping[str, object],
) -> Mapping[str, object]:
    """Return the projected current-session mapping when present."""
    return _mapping(review_state.get("current_session"))


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
