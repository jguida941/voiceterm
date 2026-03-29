"""Typed startup advisory-decision helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .decision_explainability import rejected_rule_trace, rule_match_evidence
from .finding_contracts import RejectedRuleTraceRecord, RuleMatchEvidenceRecord

if TYPE_CHECKING:
    from .project_governance import ProjectGovernance
    from .project_governance_push import PushEnforcement
    from .startup_context import ReviewerGateState


@dataclass(frozen=True, slots=True)
class StartupAdvisoryDecision:
    """Typed answer for the next startup advisory action."""

    action: str
    reason: str
    rule_summary: str
    match_evidence: tuple[RuleMatchEvidenceRecord, ...]
    rejected_rule_traces: tuple[RejectedRuleTraceRecord, ...]


def derive_advisory_decision(
    governance: "ProjectGovernance",
    gate: "ReviewerGateState",
) -> StartupAdvisoryDecision:
    """Derive the advisory action from push enforcement and reviewer state."""
    push = governance.push_enforcement
    if push.checkpoint_required:
        return _checkpoint_required_decision(push)
    if not push.safe_to_continue_editing:
        return _budget_exceeded_decision(push)
    if gate.implementation_blocked:
        return _blocked_loop_decision(gate)
    if gate.bridge_active and not gate.review_accepted:
        return _pending_review_decision(
            bridge_active=gate.bridge_active,
            review_accepted=gate.review_accepted,
            worktree_clean=push.worktree_clean,
        )
    if push.worktree_clean and push.ahead_of_upstream_commits in (0, None):
        return _decision(
            "no_push_needed",
            "clean_worktree",
            (
                "Startup found no further governed push step because the branch "
                "already matches upstream."
            ),
            (
                rule_match_evidence(
                    "startup_advisory.no_push_needed",
                    "The worktree is clean and there is no remote delta left to publish.",
                    f"worktree_clean={push.worktree_clean}",
                    f"ahead_of_upstream_commits={push.ahead_of_upstream_commits}",
                ),
            ),
            (
                rejected_rule_trace(
                    "startup_advisory.push_allowed",
                    "Move straight to the governed push path.",
                    "There is no remote delta left to publish.",
                ),
            ),
        )
    if push.worktree_clean and gate.review_gate_allows_push:
        return _decision(
            "push_allowed",
            "worktree_clean_and_review_accepted",
            (
                "Startup allows the governed push path because the worktree is "
                "clean and the review gate is satisfied."
            ),
            (
                rule_match_evidence(
                    "startup_advisory.push_allowed",
                    "All startup prerequisites for governed push are satisfied.",
                    f"worktree_clean={push.worktree_clean}",
                    f"review_gate_allows_push={gate.review_gate_allows_push}",
                ),
            ),
            (
                rejected_rule_trace(
                    "startup_advisory.no_push_needed",
                    "Stop because nothing remains to push.",
                    "The branch still has work available for publication.",
                ),
            ),
        )
    if gate.checkpoint_permitted and push.worktree_dirty:
        return _decision(
            "checkpoint_allowed",
            "worktree_dirty_within_budget",
            (
                "Startup allows a checkpoint now because the worktree is dirty "
                "but still within the repo's continuation budget."
            ),
            (
                rule_match_evidence(
                    "startup_advisory.checkpoint_allowed",
                    "The worktree is dirty, but startup has room to checkpoint without forcing a hard stop.",
                    f"worktree_dirty={push.worktree_dirty}",
                    f"checkpoint_permitted={gate.checkpoint_permitted}",
                ),
            ),
            (
                rejected_rule_trace(
                    "startup_advisory.push_allowed",
                    "Move straight to the governed push path.",
                    "The worktree is not clean yet.",
                ),
            ),
        )
    return _decision(
        "continue_editing",
        "clean_worktree",
        (
            "Startup allows editing to continue because no checkpoint, review, "
            "or push gate requires a different action yet."
        ),
        (
            rule_match_evidence(
                "startup_advisory.continue_editing_default",
                "No stronger startup rule matched, so the repo stays in the default editing state.",
                f"worktree_clean={push.worktree_clean}",
                f"review_gate_allows_push={gate.review_gate_allows_push}",
            ),
        ),
        (
            rejected_rule_trace(
                "startup_advisory.push_allowed",
                "Move straight to the governed push path.",
                "Startup has not reached a clean, push-ready state yet.",
            ),
        ),
    )


def _pending_review_decision(
    *,
    bridge_active: bool,
    review_accepted: bool,
    worktree_clean: bool,
) -> StartupAdvisoryDecision:
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


def _checkpoint_required_decision(
    push: "PushEnforcement",
) -> StartupAdvisoryDecision:
    checkpoint_reason = push.checkpoint_reason
    checkpoint_required = push.checkpoint_required
    return _decision(
        "checkpoint_before_continue",
        checkpoint_reason,
        (
            "Startup blocks another implementation slice because the repo "
            "already requires a checkpoint."
        ),
        (
            rule_match_evidence(
                "startup_advisory.checkpoint_required",
                "The checkpoint gate fired before any edit or push path could continue.",
                f"checkpoint_required={checkpoint_required}",
                f"checkpoint_reason={checkpoint_reason}",
            ),
        ),
        (
            rejected_rule_trace(
                "startup_advisory.continue_editing",
                "Keep editing the current slice.",
                "The checkpoint gate is already red.",
            ),
            rejected_rule_trace(
                "startup_advisory.push_allowed",
                "Move straight to the governed push path.",
                "Startup will not skip the checkpoint prerequisite.",
            ),
        ),
    )


def _budget_exceeded_decision(
    push: "PushEnforcement",
) -> StartupAdvisoryDecision:
    safe_to_continue_editing = push.safe_to_continue_editing
    return _decision(
        "checkpoint_before_continue",
        "worktree_budget_exceeded",
        (
            "Startup blocks another implementation slice because the "
            "worktree has crossed the repo's continuation budget."
        ),
        (
            rule_match_evidence(
                "startup_advisory.worktree_budget_exceeded",
                "The continuation budget is exhausted even though the hard checkpoint flag is not set.",
                f"safe_to_continue_editing={safe_to_continue_editing}",
            ),
        ),
        (
            rejected_rule_trace(
                "startup_advisory.continue_editing",
                "Keep editing the current slice.",
                "The worktree budget is already exceeded.",
            ),
        ),
    )


def _blocked_loop_decision(gate: "ReviewerGateState") -> StartupAdvisoryDecision:
    block_reason = gate.implementation_block_reason or "reviewer_loop_blocked"
    return _decision(
        "checkpoint_before_continue",
        block_reason,
        (
            "Startup blocks another implementation slice because reviewer-owned "
            "state says the live loop must pause first."
        ),
        (
            rule_match_evidence(
                "startup_advisory.reviewer_loop_blocked",
                "Reviewer-owned state marked the current loop as blocked.",
                f"implementation_blocked={gate.implementation_blocked}",
                f"block_reason={block_reason}",
            ),
        ),
        (
            rejected_rule_trace(
                "startup_advisory.continue_editing",
                "Keep editing the current slice.",
                "Reviewer-owned state is blocked.",
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


__all__ = ["StartupAdvisoryDecision", "derive_advisory_decision"]
