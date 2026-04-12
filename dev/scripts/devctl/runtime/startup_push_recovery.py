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
    from .project_governance_push import PushEnforcement

_CURRENT_HEAD_PUSH_IN_PROGRESS_REASONS = frozenset({
    "push_preflight_running",
    "push_pending",
    "post_push_bundle_pending",
})


def artifact_records_current_head_publish(push_enforcement: "PushEnforcement") -> bool:
    """Return True when the latest push artifact proves current approved-target publication."""
    latest_push_report_published_remote = bool(
        getattr(push_enforcement, "latest_push_report_published_remote", False)
    )
    return bool(
        latest_push_report_published_remote
        and _artifact_matches_current_publication_target(push_enforcement)
    )


def artifact_publication_truth(
    push_enforcement: "PushEnforcement",
) -> tuple[bool, bool]:
    """Return effective published/post-push truth for the current publication target."""
    published_remote = artifact_records_current_head_publish(push_enforcement)
    return (
        published_remote,
        bool(
            published_remote
            and getattr(push_enforcement, "latest_push_report_post_push_green", False)
        ),
    )


def artifact_push_in_progress_for_current_head(
    push_enforcement: "PushEnforcement",
) -> bool:
    """Return True when the latest push artifact represents a live push phase."""
    if not _artifact_matches_current_publication_target(push_enforcement):
        return False
    reason = str(getattr(push_enforcement, "latest_push_report_reason", "") or "").strip()
    return reason in _CURRENT_HEAD_PUSH_IN_PROGRESS_REASONS


def effective_publication_summary(published_remote: bool, post_push_green: bool) -> str:
    """Return a one-line human-readable summary of effective publication state."""
    if published_remote and post_push_green:
        return "Published to origin at HEAD"
    if published_remote:
        return "Published but post-push validation failed"
    return "Not yet published (push report is from different branch/commit)"


def artifact_publication_recovery_decision(
    inputs: PushDecisionInputs,
    push_enforcement: "PushEnforcement",
) -> PushDecisionState | None:
    """Return a recovery decision when persisted push truth already proves publication."""
    if not artifact_records_current_head_publish(push_enforcement):
        return None
    artifact_path = str(push_enforcement.latest_push_report_path or "").strip()
    artifact_hint = (
        f" Review the latest push artifact at `{artifact_path}` for the current HEAD."
        if artifact_path
        else ""
    )
    if not push_enforcement.latest_push_report_post_push_green:
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
                    "artifact already recorded remote publication for the current "
                    "approved reviewer target, even if the local upstream divergence "
                    "view is stale until the next fetch."
                ),
                match_evidence=(
                    rule_match_evidence(
                        "startup_push.remote_publish_recorded_current_head",
                        "Startup recovered a persisted remote-published push result for "
                        "the current HEAD.",
                        "worktree_clean=True",
                        "review_gate_allows_push=True",
                        "current_approved_target_identity="
                        f"{push_enforcement.current_approved_target_identity or '(missing)'}",
                        "latest_push_report_published_remote=True",
                        "latest_push_report_post_push_green=False",
                        "latest_push_report_matches_current_approved_target=True",
                        "latest_push_report_matches_current_branch=True",
                    ),
                ),
                rejected_rule_traces=(
                    rejected_rule_trace(
                        "startup_push.run_devctl_push",
                        "Run the governed push path immediately.",
                        "The latest push artifact already recorded remote publication "
                        "for the current approved reviewer target.",
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
                "already records remote publication for the current approved reviewer target."
                + artifact_hint
            ),
            rule_summary=(
                "No governed push is needed because the current approved reviewer "
                "target already has a persisted remote-publication record, so local "
                "upstream divergence can be treated as stale until the next fetch."
            ),
            match_evidence=(
                rule_match_evidence(
                    "startup_push.remote_publish_recorded_current_head_green",
                    "Startup detected a persisted remote-publication record for the "
                    "current approved reviewer target.",
                    "worktree_clean=True",
                    "review_gate_allows_push=True",
                    "latest_push_report_published_remote=True",
                    "latest_push_report_post_push_green=True",
                    "latest_push_report_matches_current_approved_target=True",
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


def _current_target_remote(push_enforcement: "PushEnforcement") -> str:
    upstream_ref = str(getattr(push_enforcement, "upstream_ref", "") or "")
    if "/" in upstream_ref:
        return upstream_ref.split("/", 1)[0]
    return str(getattr(push_enforcement, "default_remote", "") or "")


def _artifact_matches_current_publication_target(
    push_enforcement: "PushEnforcement",
) -> bool:
    latest_push_report_matches_current_branch = bool(
        getattr(push_enforcement, "latest_push_report_matches_current_branch", False)
    )
    latest_push_report_matches_current_head = bool(
        getattr(push_enforcement, "latest_push_report_matches_current_head", False)
    )
    latest_push_report_matches_current_approved_target = bool(
        getattr(
            push_enforcement,
            "latest_push_report_matches_current_approved_target",
            False,
        )
    )
    latest_push_report_matches_current_worktree = bool(
        getattr(
            push_enforcement,
            "latest_push_report_matches_current_worktree",
            False,
        )
    )
    current_branch = str(getattr(push_enforcement, "current_branch", "") or "")
    latest_push_report_branch = str(
        getattr(push_enforcement, "latest_push_report_branch", "") or ""
    )
    current_head_commit = str(getattr(push_enforcement, "current_head_commit", "") or "")
    latest_push_report_head_commit = str(
        getattr(push_enforcement, "latest_push_report_head_commit", "") or ""
    )
    latest_push_report_remote = str(
        getattr(push_enforcement, "latest_push_report_remote", "") or ""
    )
    artifact_branch_matches = latest_push_report_matches_current_branch
    if not artifact_branch_matches:
        artifact_branch_matches = bool(
            current_branch
            and latest_push_report_branch
            and current_branch == latest_push_report_branch
        )
    artifact_head_matches = latest_push_report_matches_current_head
    if not artifact_head_matches:
        artifact_head_matches = bool(
            current_head_commit
            and latest_push_report_head_commit
            and current_head_commit == latest_push_report_head_commit
        )
    artifact_remote_matches = not latest_push_report_remote or (
        latest_push_report_remote == _current_target_remote(push_enforcement)
    )
    return bool(
        latest_push_report_matches_current_approved_target
        and latest_push_report_matches_current_worktree
        and artifact_branch_matches
        and artifact_head_matches
        and artifact_remote_matches
    )
