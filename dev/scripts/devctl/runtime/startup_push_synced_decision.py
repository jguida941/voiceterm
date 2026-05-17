"""Synced-branch push decisions for startup push guidance."""

from __future__ import annotations

from .decision_explainability import rejected_rule_trace, rule_match_evidence
from .startup_push_models import (
    PushDecisionInputs,
    PushDecisionSpec,
    PushDecisionState,
    project_push_decision,
)


def synced_branch_decision(
    inputs: PushDecisionInputs,
    *,
    managed_projection_paths: tuple[str, ...],
) -> PushDecisionState:
    """Return a no-push decision for synced branches and projection-only dirt."""
    reason = (
        "managed_projection_drift_only"
        if managed_projection_paths
        else "branch_already_synced"
    )
    path_text = ", ".join(managed_projection_paths)
    next_step_summary = (
        "No governed push is required because only managed compatibility "
        f"projections are dirty: {path_text}."
        if managed_projection_paths
        else (
            "No governed push is required because the current branch already "
            "matches its upstream."
        )
    )
    rule_summary = (
        "No governed push is needed because the source worktree is clean, the "
        "branch already matches upstream, and remaining dirty paths are managed projections."
        if managed_projection_paths
        else (
            "No governed push is needed because the worktree is clean, the "
            "review gate is satisfied, and the branch already matches upstream."
        )
    )
    evidence_items = [
        "worktree_clean=True",
        "ahead_of_upstream_commits=0",
    ]
    if managed_projection_paths:
        evidence_items.append(f"managed_projection_dirty_paths={path_text}")
    else:
        evidence_items.append("review_gate_allows_push=True")
    return project_push_decision(
        inputs,
        PushDecisionSpec(
            action="no_push_needed",
            reason=reason,
            next_step_summary=next_step_summary,
            rule_summary=rule_summary,
            match_evidence=(
                rule_match_evidence(
                    "startup_push.managed_projection_drift_only"
                    if managed_projection_paths
                    else "startup_push.branch_already_synced",
                    "Startup detected no remote delta left to publish.",
                    *evidence_items,
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
