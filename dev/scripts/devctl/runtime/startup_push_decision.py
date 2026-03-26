"""Typed AI-facing push-decision helpers for startup surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .project_governance import ProjectGovernance
    from .startup_context import ReviewerGateState

_REVIEW_STATUS_COMMAND = (
    "python3 dev/scripts/devctl.py review-channel --action status "
    "--terminal none --format json"
)
_DEVCTL_PUSH_EXECUTE_COMMAND = "python3 dev/scripts/devctl.py push --execute"


@dataclass(frozen=True, slots=True)
class PushDecisionState:
    """Typed answer for the next governed push step."""

    worktree_clean: bool = False
    review_gate_allows_push: bool = False
    has_remote_work_to_push: bool = False
    push_eligible_now: bool = False
    action: str = "await_checkpoint"
    reason: str = ""
    next_step_summary: str = ""
    next_step_command: str = ""


def derive_push_decision(
    governance: "ProjectGovernance",
    gate: "ReviewerGateState",
) -> PushDecisionState:
    """Return the next governed push action for AI-facing startup surfaces."""
    pe = governance.push_enforcement
    worktree_clean = bool(pe.worktree_clean)
    review_gate_allows_push = bool(gate.review_gate_allows_push)
    has_remote_work_to_push = not (
        pe.upstream_ref and pe.ahead_of_upstream_commits == 0
    )
    if pe.checkpoint_required or not pe.safe_to_continue_editing:
        return PushDecisionState(
            worktree_clean=worktree_clean,
            review_gate_allows_push=review_gate_allows_push,
            has_remote_work_to_push=has_remote_work_to_push,
            action="await_checkpoint",
            reason=pe.checkpoint_reason or "checkpoint_required",
            next_step_summary=(
                "Cut a bounded checkpoint before more edits or any push attempt, "
                "then rerun `startup-context`."
            ),
        )
    if not worktree_clean:
        return PushDecisionState(
            worktree_clean=False,
            review_gate_allows_push=review_gate_allows_push,
            has_remote_work_to_push=has_remote_work_to_push,
            action="await_checkpoint",
            reason="worktree_dirty",
            next_step_summary=(
                "Commit or checkpoint the current bounded slice, then rerun "
                "`startup-context` before deciding whether push is allowed."
            ),
        )
    if gate.implementation_blocked:
        return PushDecisionState(
            worktree_clean=True,
            review_gate_allows_push=review_gate_allows_push,
            has_remote_work_to_push=has_remote_work_to_push,
            action="await_review",
            reason=gate.implementation_block_reason or "reviewer_loop_blocked",
            next_step_summary=(
                "Pause implementation until reviewer-owned state is current, "
                "then rerun `startup-context` and follow the refreshed "
                "`push_decision`."
            ),
            next_step_command=_REVIEW_STATUS_COMMAND,
        )
    if not review_gate_allows_push:
        return PushDecisionState(
            worktree_clean=True,
            review_gate_allows_push=False,
            has_remote_work_to_push=has_remote_work_to_push,
            action="await_review",
            reason="review_pending_before_push",
            next_step_summary=(
                "Wait for review acceptance before push, then rerun "
                "`startup-context` and follow the refreshed `push_decision`."
            ),
            next_step_command=_REVIEW_STATUS_COMMAND,
        )
    if not has_remote_work_to_push:
        return PushDecisionState(
            worktree_clean=True,
            review_gate_allows_push=True,
            has_remote_work_to_push=False,
            action="no_push_needed",
            reason="branch_already_synced",
            next_step_summary=(
                "No governed push is required because the current branch already "
                "matches its upstream."
            ),
        )
    return PushDecisionState(
        worktree_clean=True,
        review_gate_allows_push=True,
        has_remote_work_to_push=True,
        push_eligible_now=True,
        action="run_devctl_push",
        reason="push_preconditions_satisfied",
        next_step_summary=(
            "Use the governed push path now; do not fall back to raw `git push`."
        ),
        next_step_command=_DEVCTL_PUSH_EXECUTE_COMMAND,
    )
