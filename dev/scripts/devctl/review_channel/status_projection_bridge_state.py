"""Typed bridge-state helpers for review-state projection."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.review_state_semantics import is_pending_implementer_state
from ..runtime.review_state_models import (
    ReviewBridgeState,
    ReviewCurrentSessionState,
)
from .handoff import BridgeSnapshot


def build_typed_bridge_liveness(
    *,
    bridge_liveness: Mapping[str, object],
    current_session: ReviewCurrentSessionState,
) -> dict[str, object]:
    typed = dict(bridge_liveness)
    typed["current_instruction_revision"] = current_session.current_instruction_revision
    typed["claude_ack_revision"] = current_session.implementer_ack_revision
    typed["claude_ack_current"] = current_session.implementer_ack_state == "current"
    typed["implementer_ack_state"] = current_session.implementer_ack_state
    typed["implementer_state_hash"] = current_session.implementer_state_hash
    typed["implementer_state_pending"] = is_pending_implementer_state(
        implementer_status=current_session.implementer_status,
        implementer_ack=current_session.implementer_ack,
        implementer_ack_state=current_session.implementer_ack_state,
    )
    return typed


def build_review_bridge_state(
    *,
    snapshot: BridgeSnapshot,
    bridge_liveness: Mapping[str, object],
    overall_state: str,
    current_session: ReviewCurrentSessionState,
) -> ReviewBridgeState:
    reviewed_hash_current = bridge_liveness.get("reviewed_hash_current")
    review_needed = bridge_liveness.get("review_needed")
    return ReviewBridgeState(
        overall_state=overall_state,
        codex_poll_state=str(bridge_liveness.get("codex_poll_state") or "unknown"),
        reviewer_freshness=str(
            bridge_liveness.get("reviewer_freshness") or "unknown"
        ),
        reviewer_mode=str(
            bridge_liveness.get("reviewer_mode") or "active_dual_agent"
        ),
        last_codex_poll_utc=str(snapshot.metadata.get("last_codex_poll_utc") or ""),
        last_codex_poll_age_seconds=int(
            bridge_liveness.get("last_codex_poll_age_seconds") or 0
        ),
        last_worktree_hash=str(
            snapshot.metadata.get("last_non_audit_worktree_hash") or ""
        ),
        current_instruction=current_session.current_instruction,
        open_findings=current_session.open_findings,
        claude_status=current_session.implementer_status,
        claude_ack=current_session.implementer_ack,
        claude_ack_current=bool(bridge_liveness.get("claude_ack_current")),
        current_instruction_revision=current_session.current_instruction_revision,
        claude_ack_revision=current_session.implementer_ack_revision,
        last_reviewed_scope=current_session.last_reviewed_scope,
        implementer_state_hash=current_session.implementer_state_hash,
        reviewed_hash_current=(
            None if reviewed_hash_current is None else bool(reviewed_hash_current)
        ),
        review_needed=None if review_needed is None else bool(review_needed),
        review_accepted=_compute_review_accepted(snapshot),
        implementer_completion_stall=bool(
            bridge_liveness.get("implementer_completion_stall")
        ),
        publisher_running=bool(bridge_liveness.get("publisher_running")),
    )


def _compute_review_accepted(snapshot: BridgeSnapshot) -> bool:
    """Compute reviewer-owned acceptance using canonical bridge_review_accepted."""
    try:
        from .bridge_validation import bridge_review_accepted

        return bridge_review_accepted(snapshot)
    except (ImportError, ValueError):
        return False
