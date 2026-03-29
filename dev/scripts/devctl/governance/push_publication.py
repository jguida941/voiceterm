"""Typed publication-backlog helpers for governed push guidance."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PublicationBacklogState:
    """Typed summary of unpublished local branch work."""

    pending_publication_commits: int | None = None
    backlog_state: str = "none"
    backlog_summary: str = ""
    backlog_recommended: bool = False
    backlog_urgent: bool = False
    recommend_after_ahead_commits: int = 2
    urgent_after_ahead_commits: int = 5


def build_publication_backlog_state(
    *,
    ahead_of_upstream_commits: int | None,
    has_remote_work_to_push: bool,
    recommend_after_ahead_commits: int,
    urgent_after_ahead_commits: int,
) -> PublicationBacklogState:
    """Return a typed publication-backlog summary for push/startup surfaces."""
    if not has_remote_work_to_push:
        return PublicationBacklogState(
            pending_publication_commits=ahead_of_upstream_commits,
            recommend_after_ahead_commits=recommend_after_ahead_commits,
            urgent_after_ahead_commits=urgent_after_ahead_commits,
        )

    count = (
        ahead_of_upstream_commits
        if isinstance(ahead_of_upstream_commits, int) and ahead_of_upstream_commits > 0
        else None
    )
    if count is None:
        return PublicationBacklogState(
            pending_publication_commits=None,
            backlog_state="queued",
            backlog_summary="Local branch still has unpublished work waiting for governed push.",
            recommend_after_ahead_commits=recommend_after_ahead_commits,
            urgent_after_ahead_commits=urgent_after_ahead_commits,
        )

    if count >= urgent_after_ahead_commits:
        backlog_state = "urgent"
    elif count >= recommend_after_ahead_commits:
        backlog_state = "recommended"
    else:
        backlog_state = "queued"

    return PublicationBacklogState(
        pending_publication_commits=count,
        backlog_state=backlog_state,
        backlog_summary=f"{count} local commit(s) waiting for governed push.",
        backlog_recommended=backlog_state in {"recommended", "urgent"},
        backlog_urgent=backlog_state == "urgent",
        recommend_after_ahead_commits=recommend_after_ahead_commits,
        urgent_after_ahead_commits=urgent_after_ahead_commits,
    )


def publication_guidance_for_action(
    backlog: PublicationBacklogState,
    *,
    action: str,
    push_eligible_now: bool,
    next_step_command: str = "",
) -> str:
    """Return one contextualized publication guidance sentence."""
    subject = str(backlog.backlog_summary or "").strip().rstrip(".")
    if not subject:
        return ""
    if push_eligible_now:
        if next_step_command:
            return f"{subject}. Run `{next_step_command}` now."
        return f"{subject}. Push now via the governed push path."
    if action == "await_review":
        return f"{subject} once review is accepted."
    if action == "await_checkpoint":
        return f"{subject} once the current slice is checkpoint-clean."
    if action == "no_push_needed":
        return ""
    return f"{subject} after the current startup blocker clears."
