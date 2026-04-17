"""Push- and checkpoint-oriented startup advisory decisions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .decision_explainability import rejected_rule_trace, rule_match_evidence
from .post_checkpoint_dirty_support import requires_commit_before_push
from .startup_advisory_support import StartupAdvisoryDecision, _decision

if TYPE_CHECKING:
    from .project_governance_push import PushEnforcement
    from .startup_context import ReviewerGateState


def checkpoint_progress_decision(
    push: "PushEnforcement",
) -> StartupAdvisoryDecision | None:
    """Return a checkpoint-oriented decision when one outranks steady state."""
    if push.checkpoint_required:
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
    if not push.safe_to_continue_editing:
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
                    f"safe_to_continue_editing={push.safe_to_continue_editing}",
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
    if requires_commit_before_push(push):
        return _decision(
            "checkpoint_before_continue",
            "dirty_after_local_checkpoint",
            (
                "Startup blocks launcher recovery because a local checkpoint already "
                "exists and the worktree is dirty again; checkpoint the newer delta "
                "before trying to relaunch the reviewer loop."
            ),
            (
                rule_match_evidence(
                    "startup_advisory.post_checkpoint_dirty_worktree",
                    "A local checkpoint is already recorded, but the repo has new dirty work that must be checkpointed before launch or push.",
                    f"ahead_of_upstream_commits={push.ahead_of_upstream_commits}",
                    f"worktree_dirty={push.worktree_dirty}",
                    f"recommended_action={push.recommended_action}",
                ),
            ),
            (
                rejected_rule_trace(
                    "startup_advisory.repair_reviewer_loop",
                    "Relaunch the reviewer loop immediately.",
                    "Dirty work after a local checkpoint is a stricter prerequisite than loop recovery.",
                ),
            ),
        )
    return None


def steady_state_decision(
    push: "PushEnforcement",
    gate: "ReviewerGateState",
) -> StartupAdvisoryDecision:
    """Return the remaining steady-state advisory decision once blockers clear."""
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


__all__ = ["checkpoint_progress_decision", "steady_state_decision"]
