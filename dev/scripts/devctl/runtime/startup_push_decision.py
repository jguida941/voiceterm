"""Typed AI-facing push-decision helpers for startup surfaces."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

from .decision_explainability import rejected_rule_trace, rule_match_evidence
from .finding_contracts import RejectedRuleTraceRecord, RuleMatchEvidenceRecord

if TYPE_CHECKING:
    from .project_governance import ProjectGovernance
    from .project_governance_push import PushEnforcement
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
    rule_summary: str = ""
    match_evidence: tuple[RuleMatchEvidenceRecord, ...] = ()
    rejected_rule_traces: tuple[RejectedRuleTraceRecord, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["match_evidence"] = [
            evidence.to_dict() for evidence in self.match_evidence
        ]
        payload["rejected_rule_traces"] = [
            trace.to_dict() for trace in self.rejected_rule_traces
        ]
        return payload


@dataclass(frozen=True, slots=True)
class PushDecisionInputs:
    """Derived inputs reused across push-decision branches."""

    worktree_clean: bool
    review_gate_allows_push: bool
    has_remote_work_to_push: bool


@dataclass(frozen=True, slots=True)
class PushDecisionSpec:
    """Branch-specific payload that gets projected into a push decision."""

    action: str
    reason: str
    next_step_summary: str
    rule_summary: str
    match_evidence: tuple[RuleMatchEvidenceRecord, ...]
    rejected_rule_traces: tuple[RejectedRuleTraceRecord, ...]
    next_step_command: str = ""
    push_eligible_now: bool = False


def derive_push_decision(
    governance: "ProjectGovernance",
    gate: "ReviewerGateState",
) -> PushDecisionState:
    """Return the next governed push action for AI-facing startup surfaces."""
    pe = governance.push_enforcement
    inputs = PushDecisionInputs(
        worktree_clean=bool(pe.worktree_clean),
        review_gate_allows_push=bool(gate.review_gate_allows_push),
        has_remote_work_to_push=not (
            pe.upstream_ref and pe.ahead_of_upstream_commits == 0
        ),
    )
    local_readiness = _local_readiness_decision(inputs, pe)
    if local_readiness is not None:
        return local_readiness
    review_decision = _review_state_decision(inputs, gate)
    if review_decision is not None:
        return review_decision
    if not inputs.has_remote_work_to_push:
        return _project_push_decision(
            inputs,
            PushDecisionSpec(
                action="no_push_needed",
                reason="branch_already_synced",
                next_step_summary=(
                    "No governed push is required because the current branch already "
                    "matches its upstream."
                ),
                rule_summary=(
                    "No governed push is needed because the worktree is clean, the "
                    "review gate is satisfied, and the branch already matches upstream."
                ),
                match_evidence=(
                    rule_match_evidence(
                        "startup_push.branch_already_synced",
                        "Startup detected no remote delta left to publish.",
                        "worktree_clean=True",
                        "review_gate_allows_push=True",
                        "ahead_of_upstream_commits=0",
                    ),
                ),
                rejected_rule_traces=(
                    rejected_rule_trace(
                        "startup_push.run_devctl_push",
                        "Run the governed push path immediately.",
                        "There is no remote delta left to publish.",
                    ),
                ),
            ),
        )
    return _project_push_decision(
        inputs,
        PushDecisionSpec(
            action="run_devctl_push",
            reason="push_preconditions_satisfied",
            next_step_summary=(
                "Use the governed push path now; do not fall back to raw `git push`."
            ),
            next_step_command=_DEVCTL_PUSH_EXECUTE_COMMAND,
            push_eligible_now=True,
            rule_summary=(
                "Use the governed push path now because the worktree is clean, "
                "review is accepted, and upstream still needs this branch."
            ),
            match_evidence=(
                rule_match_evidence(
                    "startup_push.run_devctl_push",
                    "All push prerequisites are green and the branch still has work to publish.",
                    "worktree_clean=True",
                    "review_gate_allows_push=True",
                    "has_remote_work_to_push=True",
                ),
            ),
            rejected_rule_traces=(
                rejected_rule_trace(
                    "startup_push.no_push_needed",
                    "Declare that no governed push is needed.",
                    "The current branch still has work to publish upstream.",
                ),
            ),
        ),
    )


def _local_readiness_decision(
    inputs: PushDecisionInputs,
    push_enforcement: "PushEnforcement",
) -> PushDecisionState | None:
    checkpoint_required = push_enforcement.checkpoint_required
    safe_to_continue_editing = push_enforcement.safe_to_continue_editing
    if checkpoint_required or not safe_to_continue_editing:
        checkpoint_reason = (
            push_enforcement.checkpoint_reason or "checkpoint_required"
        )
        return _project_push_decision(
            inputs,
            PushDecisionSpec(
                action="await_checkpoint",
                reason=checkpoint_reason,
                next_step_summary=(
                    "Cut a bounded checkpoint before more edits or any push attempt, "
                    "then rerun `startup-context`."
                ),
                rule_summary=(
                    "Push is blocked until the current slice is checkpointed because "
                    "the repo's continuation gate is not green."
                ),
                match_evidence=(
                    rule_match_evidence(
                        "startup_push.await_checkpoint_gate",
                        "The continuation gate fired before any push-specific rule could run.",
                        f"checkpoint_required={checkpoint_required}",
                        f"safe_to_continue_editing={safe_to_continue_editing}",
                        f"checkpoint_reason={checkpoint_reason}",
                    ),
                ),
                rejected_rule_traces=(
                    rejected_rule_trace(
                        "startup_push.await_review",
                        "Wait for reviewer-owned state before pushing.",
                        "Checkpoint readiness is a stricter prerequisite than review readiness.",
                    ),
                    rejected_rule_trace(
                        "startup_push.run_devctl_push",
                        "Run the governed push path immediately.",
                        "The worktree is not ready for remote action yet.",
                    ),
                ),
            ),
        )
    if inputs.worktree_clean:
        return None
    return _project_push_decision(
        inputs,
        PushDecisionSpec(
            action="await_checkpoint",
            reason="worktree_dirty",
            next_step_summary=(
                "Commit or checkpoint the current bounded slice, then rerun "
                "`startup-context` before deciding whether push is allowed."
            ),
            rule_summary=(
                "Push is blocked until the current slice is checkpoint-clean "
                "because governed push only runs from a clean worktree."
            ),
            match_evidence=(
                rule_match_evidence(
                    "startup_push.worktree_must_be_clean",
                    "The worktree is still dirty, so startup cannot choose a push path yet.",
                    "worktree_clean=False",
                    "current slice still has local edits",
                ),
            ),
            rejected_rule_traces=(
                rejected_rule_trace(
                    "startup_push.await_review",
                    "Wait for review acceptance before pushing.",
                    "Local checkpoint cleanliness is still missing.",
                ),
                rejected_rule_trace(
                    "startup_push.run_devctl_push",
                    "Run the governed push path immediately.",
                    "The worktree is still dirty.",
                ),
            ),
        ),
    )


def _review_state_decision(
    inputs: PushDecisionInputs,
    gate: "ReviewerGateState",
) -> PushDecisionState | None:
    if gate.implementation_blocked:
        block_reason = gate.implementation_block_reason or "reviewer_loop_blocked"
        return _project_push_decision(
            inputs,
            PushDecisionSpec(
                action="await_review",
                reason=block_reason,
                next_step_summary=(
                    "Pause implementation until reviewer-owned state is current, "
                    "then rerun `startup-context` and follow the refreshed "
                    "`push_decision`."
                ),
                next_step_command=_REVIEW_STATUS_COMMAND,
                rule_summary=(
                    "Push waits on reviewer-owned state because the active review "
                    "loop is blocked."
                ),
                match_evidence=(
                    rule_match_evidence(
                        "startup_push.await_review_blocked_loop",
                        "The worktree is clean, but reviewer-owned state is not current enough for push.",
                        "implementation_blocked=True",
                        f"block_reason={block_reason}",
                    ),
                ),
                rejected_rule_traces=(
                    rejected_rule_trace(
                        "startup_push.run_devctl_push",
                        "Run the governed push path immediately.",
                        "Reviewer-owned state is blocked, so startup must wait first.",
                    ),
                    rejected_rule_trace(
                        "startup_push.no_push_needed",
                        "Declare that no governed push is needed.",
                        "The branch may still need publication once the reviewer loop is current.",
                    ),
                ),
            ),
        )
    if inputs.review_gate_allows_push:
        return None
    return _project_push_decision(
        inputs,
        PushDecisionSpec(
            action="await_review",
            reason="review_pending_before_push",
            next_step_summary=(
                "Wait for review acceptance before push, then rerun "
                "`startup-context` and follow the refreshed `push_decision`."
            ),
            next_step_command=_REVIEW_STATUS_COMMAND,
            rule_summary=(
                "Push waits on review acceptance because the worktree is clean "
                "but the reviewer gate has not approved remote publication yet."
            ),
            match_evidence=(
                rule_match_evidence(
                    "startup_push.await_review_unaccepted",
                    "The worktree is clean but the review gate still denies push.",
                    f"worktree_clean={inputs.worktree_clean}",
                    f"review_gate_allows_push={inputs.review_gate_allows_push}",
                ),
            ),
            rejected_rule_traces=(
                rejected_rule_trace(
                    "startup_push.run_devctl_push",
                    "Run the governed push path immediately.",
                    "Review acceptance is still pending.",
                ),
                rejected_rule_trace(
                    "startup_push.no_push_needed",
                    "Declare that no governed push is needed.",
                    "The branch may still need publication once review is accepted.",
                ),
            ),
        ),
    )


def _project_push_decision(
    inputs: PushDecisionInputs,
    spec: PushDecisionSpec,
) -> PushDecisionState:
    return PushDecisionState(
        worktree_clean=inputs.worktree_clean,
        review_gate_allows_push=inputs.review_gate_allows_push,
        has_remote_work_to_push=inputs.has_remote_work_to_push,
        push_eligible_now=spec.push_eligible_now,
        action=spec.action,
        reason=spec.reason,
        next_step_summary=spec.next_step_summary,
        next_step_command=spec.next_step_command,
        rule_summary=spec.rule_summary,
        match_evidence=spec.match_evidence,
        rejected_rule_traces=spec.rejected_rule_traces,
    )
