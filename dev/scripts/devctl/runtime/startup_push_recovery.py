"""Push-recovery helpers for persisted publication artifacts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .decision_explainability import rejected_rule_trace, rule_match_evidence
from .startup_push_models import (
    PushDecisionInputs,
    PushDecisionSpec,
    PushDecisionState,
    project_push_decision,
)

if TYPE_CHECKING:
    from .project_governance import ProjectGovernance


def artifact_records_current_head_publish(governance: "ProjectGovernance") -> bool:
    """Return True when the latest push artifact already proves current-HEAD publication."""
    pe = governance.push_enforcement
    current_branch = governance.repo_identity.current_branch
    artifact_branch_matches = bool(pe.latest_push_report_matches_current_branch)
    if not artifact_branch_matches:
        artifact_branch_matches = bool(
            current_branch
            and pe.latest_push_report_branch
            and current_branch == pe.latest_push_report_branch
        )
    artifact_remote_matches = (
        not pe.latest_push_report_remote
        or pe.latest_push_report_remote == pe.default_remote
    )
    return bool(
        pe.latest_push_report_published_remote
        and pe.latest_push_report_matches_current_head
        and artifact_branch_matches
        and artifact_remote_matches
    )


def artifact_publication_recovery_decision(
    inputs: PushDecisionInputs,
    governance: "ProjectGovernance",
) -> PushDecisionState | None:
    """Return a recovery decision when persisted push truth already proves publication."""
    if not artifact_records_current_head_publish(governance):
        return None
    pe = governance.push_enforcement
    artifact_path = str(pe.latest_push_report_path or "").strip()
    artifact_hint = (
        f" Review the latest push artifact at `{artifact_path}` for the current HEAD."
        if artifact_path
        else ""
    )
    if not pe.latest_push_report_post_push_green:
        return project_push_decision(
            inputs,
            PushDecisionSpec(
                action="no_push_needed",
                reason="remote_publish_recorded_post_push_pending",
                next_step_summary=(
                    "Remote publication already succeeded for the current HEAD."
                    + artifact_hint
                    + " Repair the post-push follow-up instead of pushing again."
                ),
                rule_summary=(
                    "No governed push is needed because the latest persisted push "
                    "artifact already recorded remote publication for the current HEAD, "
                    "even if the local upstream divergence view is stale until the next "
                    "fetch."
                ),
                match_evidence=(
                    rule_match_evidence(
                        "startup_push.remote_publish_recorded_current_head",
                        "Startup recovered a persisted remote-published push result for "
                        "the current HEAD.",
                        "worktree_clean=True",
                        "review_gate_allows_push=True",
                        f"current_head_commit={pe.current_head_commit or '(missing)'}",
                        "latest_push_report_published_remote=True",
                        "latest_push_report_post_push_green=False",
                        "latest_push_report_matches_current_head=True",
                        "latest_push_report_matches_current_branch=True",
                    ),
                ),
                rejected_rule_traces=(
                    rejected_rule_trace(
                        "startup_push.run_devctl_push",
                        "Run the governed push path immediately.",
                        "The latest push artifact already recorded remote publication "
                        "for the current HEAD.",
                    ),
                ),
            ),
        )
    return project_push_decision(
        inputs,
        PushDecisionSpec(
            action="no_push_needed",
            reason="remote_publish_recorded_current_head",
            next_step_summary=(
                "No governed push is required because the latest persisted push artifact "
                "already records remote publication for the current HEAD."
                + artifact_hint
            ),
            rule_summary=(
                "No governed push is needed because the current HEAD already has a "
                "persisted remote-publication record, so local upstream divergence can "
                "be treated as stale until the next fetch."
            ),
            match_evidence=(
                rule_match_evidence(
                    "startup_push.remote_publish_recorded_current_head_green",
                    "Startup detected a persisted remote-publication record for the "
                    "current HEAD.",
                    "worktree_clean=True",
                    "review_gate_allows_push=True",
                    "latest_push_report_published_remote=True",
                    "latest_push_report_post_push_green=True",
                    "latest_push_report_matches_current_head=True",
                    "latest_push_report_matches_current_branch=True",
                ),
            ),
            rejected_rule_traces=(
                rejected_rule_trace(
                    "startup_push.run_devctl_push",
                    "Run the governed push path immediately.",
                    "The current HEAD is already recorded as published.",
                ),
            ),
        ),
    )
