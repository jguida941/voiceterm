"""Typed AI-facing push-decision helpers for startup surfaces."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..governance.push_publication import (
    PublicationBacklogState,
    build_publication_backlog_state,
)
from .decision_explainability import rejected_rule_trace, rule_match_evidence
from .startup_push_publication import publication_backlog_from_push_enforcement
from .startup_push_models import (
    PushDecisionInputs,
    PushDecisionSpec,
    PushDecisionState,
    project_push_decision as _project_push_decision,
)
from .startup_push_recovery import (
    artifact_push_in_progress_for_current_head,
    artifact_publication_recovery_decision,
    artifact_records_current_head_publish,
    selected_push_report_source,
    selected_push_report_text,
)
from .startup_push_synced_decision import synced_branch_decision

if TYPE_CHECKING:
    from .project_governance_push import PushEnforcement

_REVIEW_STATUS_COMMAND = (
    "python3 dev/scripts/devctl.py review-channel --action status "
    "--terminal none --format json"
)
_DEVCTL_PUSH_EXECUTE_COMMAND = "python3 dev/scripts/devctl.py push --execute"

# Block reasons that represent detached-runtime-only review posture.
# Manual reviewer approval can publish a clean branch, but cannot authorize
# more coding.  When the block reason is one of these patterns AND the
# review gate has not independently allowed push, the push path should
# still fall through to publication checks instead of blocking.
_DETACHED_PUBLICATION_ONLY_REASONS: frozenset[str] = frozenset({
    "detached_runtime_only",
    "manual_reviewer_approval",
    "automation_only",
    "implementer_without_reviewer",
    "hybrid_claude_only",
})


def _is_detached_publication_only(block_reason: str) -> bool:
    """Return True when the implementation block is a detached-runtime pattern.

    These patterns mean the reviewer loop is not live for *coding* but a
    typed checkpoint acceptance already covers *publication*.
    """
    return block_reason in _DETACHED_PUBLICATION_ONLY_REASONS


def _in_progress_decision(
    inputs: PushDecisionInputs,
    push_enforcement: "PushEnforcement",
) -> PushDecisionState:
    current_reason = selected_push_report_text(push_enforcement, "reason")
    artifact_path = ""
    selected_source = selected_push_report_source(push_enforcement)
    latest_artifact_path = str(
        getattr(push_enforcement, "latest_push_report_path", "") or ""
    ).strip()
    if selected_source == "latest_artifact" or (
        not selected_source and latest_artifact_path
    ):
        artifact_path = latest_artifact_path
    artifact_hint = (
        f" Follow `{artifact_path}` or the live command output until the push finishes."
        if artifact_path
        else " Follow the live command output until the push finishes."
    )
    return _project_push_decision(
        inputs,
        PushDecisionSpec(
            action="no_push_needed",
            reason="governed_push_in_progress",
            next_step_summary=(
                "A governed push for the current HEAD is already running."
                f"{artifact_hint}"
            ),
            rule_summary=(
                "No second governed push should start while the latest push "
                "artifact for the current publication target is already in an "
                "active execution phase."
            ),
            match_evidence=(
                rule_match_evidence(
                    "startup_push.governed_push_in_progress",
                    "Startup detected an in-flight governed push receipt for the "
                    "current publication target.",
                    "worktree_clean=True",
                    f"review_gate_allows_push={inputs.review_gate_allows_push}",
                    f"selected_push_report_reason={current_reason or '(missing)'}",
                    "selected_push_report_matches_current_branch=True",
                    "selected_push_report_matches_current_head=True",
                    "selected_push_report_matches_current_approved_target=True",
                ),
            ),
            rejected_rule_traces=(
                rejected_rule_trace(
                    "startup_push.run_devctl_push",
                    "Run the governed push path immediately.",
                    "A governed push for the current HEAD is already running.",
                ),
            ),
        ),
    )


def derive_push_decision(
    push_enforcement: "PushEnforcement",
    *,
    review_gate_allows_push: bool,
    implementation_blocked: bool,
    implementation_block_reason: str = "",
) -> PushDecisionState:
    """Return the next governed push action for AI-facing startup surfaces."""
    pe = push_enforcement
    publication_authorized = bool(
        getattr(pe, "current_push_authorization_valid", False)
    )
    remote_publication_is_current = artifact_records_current_head_publish(pe)
    inputs = PushDecisionInputs(
        worktree_clean=bool(pe.worktree_clean),
        review_gate_allows_push=bool(review_gate_allows_push or publication_authorized),
        has_remote_work_to_push=not (
            remote_publication_is_current
            or (pe.upstream_ref and pe.ahead_of_upstream_commits == 0)
        ),
        publication_backlog=publication_backlog_from_push_enforcement(pe),
    )
    local_readiness = _local_readiness_decision(inputs, pe)
    if local_readiness is not None:
        return local_readiness
    if artifact_push_in_progress_for_current_head(pe):
        return _in_progress_decision(inputs, pe)
    managed_projection_paths = tuple(
        getattr(pe, "managed_projection_dirty_paths", ()) or ()
    )
    if managed_projection_paths and not inputs.has_remote_work_to_push:
        return synced_branch_decision(
            inputs,
            managed_projection_paths=managed_projection_paths,
        )
    review_decision = _review_state_decision(
        inputs,
        publication_authorized=publication_authorized,
        implementation_blocked=implementation_blocked,
        implementation_block_reason=implementation_block_reason,
    )
    if review_decision is not None:
        return review_decision
    artifact_recovery = artifact_publication_recovery_decision(inputs, pe)
    if artifact_recovery is not None:
        return artifact_recovery
    if not inputs.has_remote_work_to_push:
        return synced_branch_decision(inputs, managed_projection_paths=())
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
                "Use the governed push path now because the worktree is clean and "
                "either review is publish-clear or a persisted push authorization "
                "already covers the current HEAD."
            ),
            match_evidence=(
                rule_match_evidence(
                    "startup_push.run_devctl_push",
                    "All push prerequisites are green and the branch still has work to publish.",
                    "worktree_clean=True",
                    f"review_gate_allows_push={inputs.review_gate_allows_push}",
                    f"current_push_authorization_valid={publication_authorized}",
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
    staged_path_count = int(getattr(push_enforcement, "staged_path_count", 0) or 0)
    unstaged_path_count = int(getattr(push_enforcement, "unstaged_path_count", 0) or 0)
    if staged_path_count > 0 and unstaged_path_count > 0:
        reason = "staged_and_unstaged_worktree_present"
        next_step_summary = (
            "The repo has both a staged index and unstaged edits. Review the staged set, "
            "checkpoint or commit it intentionally, then rerun `startup-context` before "
            "any push attempt."
        )
    elif staged_path_count > 0:
        reason = "staged_index_present"
        next_step_summary = (
            "The repo already has staged work waiting in the index. Review and checkpoint "
            "or commit that staged set before deciding whether push is allowed."
        )
    else:
        reason = "worktree_dirty"
        next_step_summary = "Commit or checkpoint the current bounded slice, then rerun `startup-context` before deciding whether push is allowed."
    return _project_push_decision(
        inputs,
        PushDecisionSpec(
            action="await_checkpoint",
            reason=reason,
            next_step_summary=next_step_summary,
            rule_summary=(
                "Push is blocked until the current slice is checkpoint-clean "
                "because governed push only runs from a clean worktree."
            ),
            match_evidence=(
                rule_match_evidence(
                    "startup_push.worktree_must_be_clean",
                    "The worktree is still dirty, so startup cannot choose a push path yet.",
                    "worktree_clean=False",
                    f"staged_path_count={staged_path_count}",
                    f"unstaged_path_count={unstaged_path_count}",
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
    *,
    publication_authorized: bool,
    implementation_blocked: bool,
    implementation_block_reason: str,
) -> PushDecisionState | None:
    if publication_authorized:
        return None
    if implementation_blocked and not inputs.review_gate_allows_push:
        # Manual reviewer approval can publish a clean branch, but cannot
        # authorize more coding.  Skip the block for publication when the
        # reason is a detached-runtime-only pattern.
        if _is_detached_publication_only(implementation_block_reason):
            return None
        block_reason = implementation_block_reason or "reviewer_loop_blocked"
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
