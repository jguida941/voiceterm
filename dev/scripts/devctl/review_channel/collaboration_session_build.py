"""Small assembly helpers for collaboration-session state."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ..runtime.review_state_models import (
    CollaborationPeerReviewState,
    ReviewCurrentSessionState,
)
from ..runtime.reviewer_mode_authority_contract import (
    resolve_reviewer_mode_authority,
)
from .collaboration_session_roster_lookup import text as _text


@dataclass(frozen=True, slots=True)
class ReviewerModeSelection:
    reviewer_mode: str
    effective_mode: str


def reviewer_mode_selection(
    bridge_liveness: Mapping[str, object],
    *,
    timestamp: str,
) -> ReviewerModeSelection:
    reviewer_mode = _text(bridge_liveness.get("reviewer_mode")) or "tools_only"
    evidence_refs = tuple(
        ref
        for ref in (
            _text(bridge_liveness.get("reviewer_mode_authority_ref")),
            _text(bridge_liveness.get("reviewer_mode_transition_ref")),
            _text(bridge_liveness.get("handshake_ref")),
            _text(bridge_liveness.get("launch_authority_ref")),
        )
        if ref
    )
    authority = resolve_reviewer_mode_authority(
        reviewer_mode,
        _text(bridge_liveness.get("effective_reviewer_mode")) or reviewer_mode,
        evidence_refs=evidence_refs,
        observed_at_utc=timestamp,
    )
    return ReviewerModeSelection(
        reviewer_mode=reviewer_mode,
        effective_mode=authority.effective_mode.value,
    )


def peer_review_state(
    current_session: ReviewCurrentSessionState,
) -> CollaborationPeerReviewState:
    return CollaborationPeerReviewState(
        current_instruction=current_session.current_instruction,
        current_instruction_revision=current_session.current_instruction_revision,
        open_findings=current_session.open_findings,
        implementer_status=current_session.implementer_status,
        implementer_ack=current_session.implementer_ack,
        implementer_ack_state=current_session.implementer_ack_state,
        implementer_state_hash=current_session.implementer_state_hash,
        last_reviewed_scope=current_session.last_reviewed_scope,
    )


def current_slice_for_session(current_session: ReviewCurrentSessionState) -> str:
    return current_session.current_instruction or current_session.last_reviewed_scope
