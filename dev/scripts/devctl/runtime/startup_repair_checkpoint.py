"""Checkpoint repair promotion helpers for startup repair output."""

from __future__ import annotations

from .checkpoint_repair_authority import (
    CheckpointRepairAuthority,
    GOVERNED_CHECKPOINT_COMMIT,
    GOVERNED_CHECKPOINT_COMMIT_COMMAND,
    REPAIR_VERIFIED,
)
from .startup_repair_models import StartupRepairIssue


def checkpoint_repair_issue(
    authority: CheckpointRepairAuthority,
) -> StartupRepairIssue:
    """Return the startup repair issue for a verified checkpoint repair."""
    return StartupRepairIssue(
        issue_id=REPAIR_VERIFIED,
        issue_class="governance_lifecycle_promotion",
        source="remote_commit_pipeline",
        owner="system",
        summary=(
            "Scoped checkpoint repair has matching validation proof and may "
            "continue through the governed commit action."
        ),
        detail=(
            f"original_block_reason={authority.original_block_reason}; "
            f"pipeline_id={authority.pipeline_id}; "
            f"validation_receipt_id={authority.validation_receipt_id}"
        ),
        recommended_command=GOVERNED_CHECKPOINT_COMMIT_COMMAND,
        repairable=True,
        safe_to_apply_now=False,
        apply_action=GOVERNED_CHECKPOINT_COMMIT,
        changes_tracked_state=True,
        blocked_by_approval_boundary=False,
    )


def checkpoint_repair_next_step(
    issues: tuple[StartupRepairIssue, ...],
) -> tuple[str, str, str] | None:
    """Return the next step when verified repair authority is present."""
    repair_verified_issue = next(
        (issue for issue in issues if issue.issue_id == REPAIR_VERIFIED),
        None,
    )
    if repair_verified_issue is None:
        return None
    return (
        GOVERNED_CHECKPOINT_COMMIT,
        "Scoped repair proof is fresh; continue through the governed commit path.",
        repair_verified_issue.recommended_command,
    )


__all__ = [
    "checkpoint_repair_issue",
    "checkpoint_repair_next_step",
]
