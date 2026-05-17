"""Reviewer-duty proof builder."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ..runtime.review_state_collaboration_models import CollaborationSessionState
from ..runtime.reviewer_runtime_models import ReviewerDutyProof
from .reviewer_runtime_duty_context import (
    PacketReviewContext,
    SemanticReviewContext,
    build_packet_review_context,
    build_semantic_review_context,
)
from .reviewer_runtime_duty_identity import (
    ReviewConflict,
    ReviewIdentityPair,
    caller_identity_mismatch,
    classify_review_conflict,
    resolve_review_identities,
)


@dataclass(frozen=True, slots=True)
class DutyProofContext:
    packet: PacketReviewContext
    semantic: SemanticReviewContext
    identities: ReviewIdentityPair
    conflict: ReviewConflict
    stale_reason: str
    caller_mismatch: bool


def build_reviewer_duty_proof(
    *,
    bridge_liveness: Mapping[str, object],
    collaboration: CollaborationSessionState | None,
    agent_mind: Mapping[str, object] | None,
    stale_reason: str,
) -> ReviewerDutyProof:
    """Build typed proof that reviewer duty is complete for this session."""
    identities = resolve_review_identities(collaboration)
    context = DutyProofContext(
        packet=build_packet_review_context(bridge_liveness),
        semantic=build_semantic_review_context(agent_mind),
        identities=identities,
        conflict=classify_review_conflict(identities),
        stale_reason=stale_reason,
        caller_mismatch=caller_identity_mismatch(identities.reviewer),
    )
    semantic_claimed = (
        context.semantic.claimed if not context.caller_mismatch else False
    )
    stale_reasons = _stale_reasons(context, semantic_claimed)
    return ReviewerDutyProof(
        reviewer_actor_id=context.identities.reviewer.actor_id,
        reviewer_session_id=context.identities.reviewer.session_id,
        last_packet_event_id=context.packet.last_packet_event_id,
        last_packet_observed_at_utc=context.packet.last_packet_observed_at_utc,
        pending_packet_count=context.packet.pending_packet_count,
        current_head_sha=context.packet.current_head_sha,
        staged_tree_hash=context.packet.staged_tree_hash,
        worktree_hash=context.semantic.worktree_hash,
        changed_path_count=context.semantic.changed_path_count,
        reviewed_diff_hash=context.semantic.reviewed_diff_hash,
        reviewed_diff_base=context.semantic.reviewed_diff_base,
        reviewed_path_count=context.semantic.reviewed_path_count,
        last_diff_review_at_utc=context.semantic.last_diff_review_at_utc,
        semantic_review_source=context.semantic.source,
        semantic_review_claimed=semantic_claimed,
        review_conflict_class=context.conflict.classification,
        review_conflict_reasons=context.conflict.reasons,
        state=_proof_state(context, semantic_claimed, stale_reasons),
        stale_reasons=stale_reasons,
    )


def _stale_reasons(
    context: DutyProofContext,
    semantic_claimed: bool,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if context.packet.pending_packet_count > 0:
        reasons.append("pending_packet_inbox_not_consumed")
    if not semantic_claimed:
        reasons.append("semantic_review_not_claimed")
    elif not context.semantic.has_concrete_evidence:
        reasons.append("semantic_review_evidence_missing")
    elif context.semantic.source == "agent_mind_auxiliary":
        reasons.append("semantic_review_source_auxiliary")
    if context.stale_reason:
        reasons.append(f"stale_reason:{context.stale_reason}")
    if context.caller_mismatch:
        reasons.append("actor_session_mismatch")
    if context.conflict.classification == "self_attested":
        reasons.append("self_review_requires_independent_or_override")
    return tuple(_dedupe(reasons))


def _proof_state(
    context: DutyProofContext,
    semantic_claimed: bool,
    stale_reasons: tuple[str, ...],
) -> str:
    if context.caller_mismatch:
        return "actor_session_mismatch"
    if context.conflict.classification == "self_attested" and semantic_claimed:
        return "self_review_blocked"
    if not semantic_claimed:
        return "review_incomplete"
    if not context.semantic.has_concrete_evidence:
        return "review_incomplete"
    if _reviewed_diff_is_stale(context):
        return "reviewer_diff_stale"
    if context.packet.pending_packet_count > 0 or stale_reasons:
        return "review_incomplete"
    return "healthy"


def _reviewed_diff_is_stale(context: DutyProofContext) -> bool:
    return bool(
        context.packet.staged_tree_hash
        and context.semantic.reviewed_diff_hash
        and context.packet.staged_tree_hash != context.semantic.reviewed_diff_hash
    )


def _dedupe(values: list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


__all__ = ["build_reviewer_duty_proof"]
