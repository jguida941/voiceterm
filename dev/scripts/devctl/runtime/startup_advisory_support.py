"""Support helpers for review- and ownership-oriented startup advisory decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .decision_explainability import rejected_rule_trace, rule_match_evidence
from .finding_contracts import RejectedRuleTraceRecord, RuleMatchEvidenceRecord

if TYPE_CHECKING:
    from .project_governance_push import PushEnforcement
    from .startup_context import ReviewerGateState
    from .work_intake_models import (
        WorkIntakeCoordinationState,
        WorkIntakeOwnershipState,
    )


@dataclass(frozen=True, slots=True)
class StartupAdvisoryDecision:
    """Typed answer for the next startup advisory action."""

    action: str
    reason: str
    rule_summary: str
    match_evidence: tuple[RuleMatchEvidenceRecord, ...]
    rejected_rule_traces: tuple[RejectedRuleTraceRecord, ...]


def pending_review_decision(
    *,
    bridge_active: bool,
    review_accepted: bool,
    worktree_clean: bool,
) -> StartupAdvisoryDecision:
    """Return the advisory decision while review is still pending."""
    if worktree_clean:
        return StartupAdvisoryDecision(
            action="await_review",
            reason="review_pending_before_push",
            rule_summary=(
                "Startup waits for review because the worktree is clean but "
                "reviewer acceptance is still pending."
            ),
            match_evidence=(
                rule_match_evidence(
                    "startup_advisory.await_review_clean_pending",
                    "The bridge is active, review is still pending, and the local slice is already checkpoint-clean.",
                    f"bridge_active={bridge_active}",
                    f"review_accepted={review_accepted}",
                    f"worktree_clean={worktree_clean}",
                ),
            ),
            rejected_rule_traces=(
                rejected_rule_trace(
                    "startup_advisory.continue_editing",
                    "Keep editing the current slice.",
                    "The worktree is already clean, so startup should wait for review instead of widening the slice.",
                ),
                rejected_rule_trace(
                    "startup_advisory.push_allowed",
                    "Move straight to the governed push path.",
                    "Review acceptance is still pending.",
                ),
            ),
        )
    return StartupAdvisoryDecision(
        action="continue_editing",
        reason="review_pending",
        rule_summary=(
            "Startup allows editing to continue because review is pending but "
            "the current slice is not checkpoint-clean yet."
        ),
        match_evidence=(
            rule_match_evidence(
                "startup_advisory.continue_editing_pending_review",
                "Review is pending, but the local slice still has active work.",
                f"bridge_active={bridge_active}",
                f"review_accepted={review_accepted}",
                f"worktree_clean={worktree_clean}",
            ),
        ),
        rejected_rule_traces=(
            rejected_rule_trace(
                "startup_advisory.await_review",
                "Pause and wait for reviewer-owned state.",
                "The worktree is not clean yet, so startup keeps the slice local.",
            ),
        ),
    )


def detached_publication_decision(
    push: "PushEnforcement",
    gate: "ReviewerGateState",
) -> StartupAdvisoryDecision | None:
    """Surface governed push for detached-runtime blocks with accepted review."""
    if not (
        push.worktree_clean
        and gate.review_accepted
        and push.ahead_of_upstream_commits not in (0, None)
    ):
        return None
    reason = gate.implementation_block_reason
    return _decision(
        "push_allowed",
        "detached_publication_approved",
        "Startup allows governed push: worktree clean, reviewer checkpoint "
        "accepted this snapshot for publication, live loop is detached.",
        (
            rule_match_evidence(
                "startup_advisory.push_allowed_detached",
                "Detached-runtime block with fresh reviewer acceptance surfaces governed push.",
                f"worktree_clean={push.worktree_clean}",
                f"review_accepted={gate.review_accepted}",
                f"implementation_block_reason={reason}",
            ),
        ),
        (
            rejected_rule_trace(
                "startup_advisory.continue_editing",
                "Keep editing the current slice.",
                "Reviewer checkpoint already accepted this snapshot for publication.",
            ),
        ),
    )


def blocked_loop_decision(gate: "ReviewerGateState") -> StartupAdvisoryDecision:
    """Return the advisory decision for blocked reviewer-loop state."""
    block_reason = gate.implementation_block_reason or "reviewer_loop_blocked"
    return _decision(
        "repair_reviewer_loop",
        block_reason,
        (
            "Startup routes the next step to reviewer-loop repair because "
            "reviewer-owned state is blocking the live collaboration lane."
        ),
        (
            rule_match_evidence(
                "startup_advisory.repair_reviewer_loop",
                "Reviewer-owned state marked the current loop as blocked.",
                f"implementation_blocked={gate.implementation_blocked}",
                f"block_reason={block_reason}",
            ),
        ),
        (
            rejected_rule_trace(
                "startup_advisory.checkpoint_before_continue",
                "Cut a checkpoint before doing anything else.",
                "The continuation budget is still green; the blocked reviewer loop is the stricter next action.",
            ),
        ),
    )


def concurrent_writer_decision(
    ownership: "WorkIntakeOwnershipState",
) -> StartupAdvisoryDecision:
    """Return the advisory decision for outside-scope concurrent writes."""
    outside_paths = ", ".join(ownership.outside_scope_dirty_paths[:3]) or "unknown"
    live_agents = ", ".join(ownership.live_agents[:3]) or "unknown"
    return _decision(
        "checkpoint_before_continue",
        "concurrent_writer_activity",
        (
            "Startup blocks another local edit slice because dirty paths fall "
            "outside the claimed scope while typed peer activity is present."
        ),
        (
            rule_match_evidence(
                "startup_advisory.concurrent_writer_activity",
                "Outside-scope dirty paths overlapped with active peer ownership.",
                f"outside_scope_dirty_paths={outside_paths}",
                f"live_agents={live_agents}",
            ),
        ),
        (
            rejected_rule_trace(
                "startup_advisory.continue_editing",
                "Keep editing the current slice.",
                "Another typed agent or delegated lane still appears active on a divergent dirty path set.",
            ),
        ),
    )


def coordination_conflict_decision(
    coordination: "WorkIntakeCoordinationState",
) -> StartupAdvisoryDecision:
    """Return the advisory decision for overlapping delegated worktrees."""
    duplicate_worktrees = ", ".join(
        coordination.duplicate_delegated_worktrees[:3]
    ) or "unknown"
    delegated_agents = ", ".join(coordination.delegated_agents[:3]) or "unknown"
    return _decision(
        "checkpoint_before_continue",
        "concurrent_writer_activity",
        (
            "Startup blocks another local edit slice because delegated lanes "
            "still overlap on the same claimed worktree."
        ),
        (
            rule_match_evidence(
                "startup_advisory.concurrent_writer_assignment_conflict",
                "Delegated worker worktree assignments overlap before the next slice starts.",
                f"duplicate_delegated_worktrees={duplicate_worktrees}",
                f"delegated_agents={delegated_agents}",
            ),
        ),
        (
            rejected_rule_trace(
                "startup_advisory.continue_editing",
                "Keep editing the current slice.",
                "The typed worker topology still points multiple live lanes at the same worktree.",
            ),
        ),
    )


def _decision(
    action: str,
    reason: str,
    rule_summary: str,
    match_evidence: tuple[RuleMatchEvidenceRecord, ...],
    rejected_rule_traces: tuple[RejectedRuleTraceRecord, ...],
) -> StartupAdvisoryDecision:
    return StartupAdvisoryDecision(
        action=action,
        reason=reason,
        rule_summary=rule_summary,
        match_evidence=match_evidence,
        rejected_rule_traces=rejected_rule_traces,
    )


__all__ = [
    "StartupAdvisoryDecision",
    "blocked_loop_decision",
    "concurrent_writer_decision",
    "coordination_conflict_decision",
    "detached_publication_decision",
    "pending_review_decision",
]
