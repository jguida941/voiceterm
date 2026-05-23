"""Review-channel post kind to controller action mapping."""

from __future__ import annotations

from collections.abc import Sequence

_POST_ACTION_BY_KIND = (
    ("finding", "review-channel.post_finding"),
    ("action_request", "review-channel.post_action_request"),
    ("continuation_anchor", "review-channel.post_continuation_anchor"),
    ("stop_anchor", "review-channel.post_stop_anchor"),
    ("task_started", "review-channel.post_task_started"),
    ("task_produced", "review-channel.post_task_produced"),
    ("task_progress", "review-channel.post_task_progress"),
    ("task_produced:artifact", "review-channel.post_evidence"),
    ("task_blocked", "review-channel.post_task_blocked"),
    ("plan_gap_review", "review-channel.post_plan_gap_review"),
    ("plan_patch_review", "review-channel.post_plan_patch_review"),
    ("review_accepted", "review-channel.post_review_accepted"),
    ("review_failed", "review-channel.post_review_failed"),
)


def required_review_channel_post_action(
    argv: Sequence[str],
    *,
    kind: str,
) -> str:
    key = kind
    if kind == "task_produced" and _argv_option_value(argv, "--target-kind") == "artifact":
        key = "task_produced:artifact"
    return next(
        (action for action_kind, action in _POST_ACTION_BY_KIND if action_kind == key),
        "",
    )


def _argv_option_value(argv: Sequence[str], option: str) -> str:
    try:
        index = list(argv).index(option)
    except ValueError:
        return ""
    if index + 1 >= len(argv):
        return ""
    return str(argv[index + 1]).strip()


__all__ = ["required_review_channel_post_action"]
