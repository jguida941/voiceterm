"""Report-only diagnostic projection for governed push reports."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .push_report import PushStageTruth


def build_push_diagnostic(
    *,
    execute: bool,
    push_stages: "PushStageTruth",
    reason: str,
    errors: list[str],
    push_step: dict[str, Any] | None,
    post_push_steps: list[dict[str, Any]],
) -> dict[str, str]:
    """Return report-only push progress state for operator surfaces."""
    validation_state = "passed" if push_stages.validation_ready else "blocked"
    publication_state = _publication_state(
        execute=execute,
        reason=reason,
        errors=errors,
        push_stages=push_stages,
    )
    git_push_state = _git_push_state(
        push_stages=push_stages,
        reason=reason,
        push_step=push_step,
    )
    post_push_state = _post_push_state(
        push_stages=push_stages,
        reason=reason,
        post_push_steps=post_push_steps,
    )
    return _diagnostic_payload(
        validation_state=validation_state,
        publication_state=publication_state,
        git_push_state=git_push_state,
        post_push_state=post_push_state,
    )


def _diagnostic_payload(
    *,
    validation_state: str,
    publication_state: str,
    git_push_state: str,
    post_push_state: str,
) -> dict[str, str]:
    payload: dict[str, str] = {}
    payload["summary"] = _push_diagnostic_summary(
        publication_state=publication_state,
        git_push_state=git_push_state,
        post_push_state=post_push_state,
    )
    payload["validation_state"] = validation_state
    payload["publication_state"] = publication_state
    payload["git_push_state"] = git_push_state
    payload["post_push_state"] = post_push_state
    return payload


def _publication_state(
    *,
    execute: bool,
    reason: str,
    errors: list[str],
    push_stages: "PushStageTruth",
) -> str:
    if reason == "branch_already_pushed":
        return "already_published"
    if push_stages.published_remote:
        return "published"
    if any(error.startswith("Publication authorization blocks") for error in errors):
        return "awaiting_review"
    if push_stages.validation_ready and not execute:
        return "awaiting_execute"
    if reason == "git_push_failed":
        return "blocked_by_git_push"
    if push_stages.validation_ready:
        return "pending"
    return "blocked_before_publication"


def _git_push_state(
    *,
    push_stages: "PushStageTruth",
    reason: str,
    push_step: dict[str, Any] | None,
) -> str:
    if reason == "branch_already_pushed":
        return "not_required"
    if (
        push_stages.published_remote
        and push_step
        and _returncode(push_step.get("returncode")) == 0
    ):
        return "landed"
    if push_stages.published_remote:
        return "unproven"
    if push_step and _returncode(push_step.get("returncode")) != 0:
        return "failed"
    if push_stages.validation_ready:
        return "not_attempted"
    return "blocked"


def _post_push_state(
    *,
    push_stages: "PushStageTruth",
    reason: str,
    post_push_steps: list[dict[str, Any]],
) -> str:
    if push_stages.post_push_green:
        return "green"
    if push_stages.published_remote and reason == "post_push_skipped_by_policy":
        return "skipped"
    if push_stages.published_remote and reason == "post_push_bundle_failed":
        return "failed"
    if push_stages.published_remote:
        return "pending"
    if post_push_steps:
        return "failed"
    return "not_started"


def _push_diagnostic_summary(
    *,
    publication_state: str,
    git_push_state: str,
    post_push_state: str,
) -> str:
    if publication_state == "awaiting_review":
        return "publication_awaiting_review"
    if git_push_state == "failed":
        return "git_push_failed"
    if publication_state == "awaiting_execute":
        return "validation_ready_execute_required"
    if publication_state == "already_published":
        return "remote_already_published_post_push_pending"
    if publication_state == "published" and post_push_state != "green":
        return "remote_published_post_push_pending"
    if publication_state == "published":
        return "published_post_push_green"
    return "blocked_before_publication"


def _returncode(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 1


__all__ = ["build_push_diagnostic"]
