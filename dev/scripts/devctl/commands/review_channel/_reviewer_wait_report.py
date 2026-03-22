"""Report-building helpers for reviewer-side bounded wait actions."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from ...review_channel.peer_liveness import AttentionStatus

_IMPLEMENTER_UPDATE_MESSAGES = {
    AttentionStatus.CLAUDE_ACK_STALE: (
        "Claude ACK changed against the current reviewer instruction. "
        "Re-read the bridge and review the updated implementer state."
    ),
    AttentionStatus.REVIEW_FOLLOW_UP_REQUIRED: (
        "Implementer-owned state changed and reviewer follow-up is now required. "
        "Inspect the live diff and refresh the reviewer checkpoint."
    ),
}
_LOOP_UNHEALTHY_MESSAGES = {
    AttentionStatus.CHECKPOINT_REQUIRED: (
        "Reviewer wait stopped because the loop is paused on a checkpoint gate. "
        "Cut a checkpoint before continuing review work."
    ),
    AttentionStatus.RUNTIME_MISSING: (
        "Reviewer wait stopped because the repo-owned reviewer runtime is missing. "
        "Restore the follow runtime instead of waiting silently."
    ),
    AttentionStatus.PUBLISHER_MISSING: (
        "Reviewer wait stopped because the publisher is missing. "
        "Restore the repo-owned follow runtime before trusting status output."
    ),
    AttentionStatus.PUBLISHER_FAILED_START: (
        "Reviewer wait stopped because the publisher failed to start. "
        "Inspect the follow log before resuming review."
    ),
    AttentionStatus.PUBLISHER_DETACHED_EXIT: (
        "Reviewer wait stopped because the publisher exited unexpectedly. "
        "Restore the detached follow runtime before resuming review."
    ),
}
_TIMEOUT_MESSAGES = {
    AttentionStatus.CLAUDE_ACK_STALE: (
        "Timed out while Claude ACK remained stale against the current instruction revision. "
        "Repoll implementer state and confirm the latest ACK before continuing."
    ),
    AttentionStatus.REVIEW_FOLLOW_UP_REQUIRED: (
        "Timed out while reviewer follow-up remained required on the current tree. "
        "Refresh the review pass instead of treating the loop as idle."
    ),
}


@dataclass(frozen=True, slots=True)
class ReviewerWaitState:
    """Rendered reviewer wait-state payload."""

    mode: str
    stop_reason: str
    polls_observed: int
    wait_interval_seconds: int
    wait_timeout_seconds: int
    baseline_worktree_hash: str
    current_worktree_hash: str
    baseline_reviewed_hash: str
    baseline_implementer_ack_revision: str
    current_implementer_ack_revision: str
    baseline_attention_status: str
    current_attention_status: str
    baseline_attention_summary: str
    current_attention_summary: str
    implementer_update_observed: bool

    def to_report(self) -> dict[str, object]:
        """Return the stable report payload."""
        return asdict(self)


def build_reviewer_wait_report(
    *,
    baseline,
    current,
    args,
    outcome,
) -> dict[str, object]:
    """Build the stable reviewer-wait report payload."""
    report = dict(current.report)
    report["action"] = getattr(args, "action", "reviewer-wait")
    report["ok"] = outcome.exit_code == 0
    report["exit_ok"] = outcome.exit_code == 0
    report["exit_code"] = outcome.exit_code
    report["wait_state"] = ReviewerWaitState(
        mode="reviewer_wait",
        stop_reason=outcome.stop_reason,
        polls_observed=outcome.polls_observed,
        wait_interval_seconds=outcome.wait_interval_seconds,
        wait_timeout_seconds=outcome.wait_timeout_seconds,
        baseline_worktree_hash=baseline.worktree_hash,
        current_worktree_hash=current.worktree_hash,
        baseline_reviewed_hash=baseline.reviewed_hash,
        baseline_implementer_ack_revision=baseline.implementer_ack_revision,
        current_implementer_ack_revision=current.implementer_ack_revision,
        baseline_attention_status=baseline.attention_status,
        current_attention_status=current.attention_status,
        baseline_attention_summary=baseline.attention_summary,
        current_attention_summary=current.attention_summary,
        implementer_update_observed=outcome.stop_reason in {
            "implementer_update_observed",
            "implementer_update_ready",
        },
    ).to_report()
    report["wait_attention_status"] = current.attention_status
    report["wait_attention_summary"] = current.attention_summary
    report["wait_attention_recommended_action"] = (
        current.attention_recommended_action
    )

    payload = _message_payload(
        stop_reason=outcome.stop_reason,
        baseline=baseline,
        current=current,
    )
    if payload is not None:
        entries = report.setdefault(payload["field"], [])
        if isinstance(entries, list):
            entries.append(payload["text"])
    return report


def _message_payload(
    *,
    stop_reason: str,
    baseline,
    current,
) -> dict[str, str] | None:
    if stop_reason == "implementer_update_ready":
        return {
            "field": "warnings",
            "text": (
                "Implementer has already changed the worktree since last review. "
                "Review the current diff instead of waiting."
            ),
        }
    if stop_reason == "implementer_update_observed":
        typed_status = _attention_status(current.attention_status)
        return {
            "field": "warnings",
            "text": _IMPLEMENTER_UPDATE_MESSAGES.get(
                typed_status,
                current.attention_summary
                or (
                    "Implementer-owned state changed (worktree hash or typed ACK/status state). "
                    "Re-read the worktree diff and review the new work."
                ),
            ),
        }
    if stop_reason == "reviewer_loop_unhealthy":
        typed_status = _attention_status(current.attention_status)
        return {
            "field": "errors",
            "text": _LOOP_UNHEALTHY_MESSAGES.get(
                typed_status,
                "Reviewer wait stopped because the review loop is unhealthy. "
                "Check reviewer mode and runtime state.",
            ),
        }
    if stop_reason != "timed_out":
        return None

    typed_status = _attention_status(
        current.attention_status or baseline.attention_status
    )
    return {
        "field": "errors",
        "text": _TIMEOUT_MESSAGES.get(
            typed_status,
            "Timed out waiting for implementer-owned state change.",
        ),
    }


def _attention_status(raw_status: str) -> AttentionStatus | None:
    try:
        return AttentionStatus(raw_status)
    except ValueError:
        return None
