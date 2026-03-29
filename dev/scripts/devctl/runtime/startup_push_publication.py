"""Publication backlog helpers for startup push decision surfaces."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..governance.push_publication import (
    PublicationBacklogState,
    build_publication_backlog_state,
)
from .startup_push_recovery import artifact_records_current_head_publish

if TYPE_CHECKING:
    from .project_governance_push import PushEnforcement


def publication_backlog_from_push_enforcement(
    push_enforcement: "PushEnforcement",
) -> PublicationBacklogState:
    """Return the typed publication backlog state projected from push enforcement."""
    publication_backlog_state = str(
        getattr(push_enforcement, "publication_backlog_state", "") or ""
    )
    publication_backlog_summary = str(
        getattr(push_enforcement, "publication_backlog_summary", "") or ""
    )
    pending_publication_commits = getattr(
        push_enforcement, "pending_publication_commits", None
    )
    publication_backlog_recommended = bool(
        getattr(push_enforcement, "publication_backlog_recommended", False)
    )
    publication_backlog_urgent = bool(
        getattr(push_enforcement, "publication_backlog_urgent", False)
    )
    recommend_after_ahead_commits = (
        getattr(push_enforcement, "recommend_after_ahead_commits", 2) or 2
    )
    urgent_after_ahead_commits = (
        getattr(push_enforcement, "urgent_after_ahead_commits", 5) or 5
    )
    ahead_of_upstream_commits = int(
        getattr(push_enforcement, "ahead_of_upstream_commits", 0) or 0
    )
    upstream_ref = str(getattr(push_enforcement, "upstream_ref", "") or "")
    if (
        publication_backlog_state not in {"", "none"}
        or publication_backlog_summary
        or pending_publication_commits is not None
        or publication_backlog_recommended
        or publication_backlog_urgent
    ):
        return PublicationBacklogState(
            pending_publication_commits=pending_publication_commits,
            backlog_state=publication_backlog_state or "none",
            backlog_summary=publication_backlog_summary,
            backlog_recommended=publication_backlog_recommended,
            backlog_urgent=publication_backlog_urgent,
            recommend_after_ahead_commits=recommend_after_ahead_commits,
            urgent_after_ahead_commits=urgent_after_ahead_commits,
        )
    return build_publication_backlog_state(
        ahead_of_upstream_commits=ahead_of_upstream_commits,
        has_remote_work_to_push=not (
            artifact_records_current_head_publish(push_enforcement)
            or (upstream_ref and ahead_of_upstream_commits == 0)
        ),
        recommend_after_ahead_commits=recommend_after_ahead_commits,
        urgent_after_ahead_commits=urgent_after_ahead_commits,
    )
