"""Session-owner helpers for the typed reviewer-runtime contract."""

from __future__ import annotations

from pathlib import Path

from ..runtime.review_state_models import CollaborationSessionState
from ..runtime.reviewer_runtime_models import ReviewerSessionOwnerState
from .collaboration_provider import collaboration_provider
from .session_probe import load_conductor_sessions


def resolve_reviewer_session_owner(
    *,
    collaboration: CollaborationSessionState | None,
    session_output_root: Path | None,
) -> ReviewerSessionOwnerState:
    """Resolve repo-owned reviewer session ownership from collaboration/runtime state."""
    reviewer_provider = collaboration_provider(
        collaboration,
        role_id="review_agent",
        default="codex",
    )
    if not isinstance(session_output_root, Path):
        return ReviewerSessionOwnerState(provider=reviewer_provider)
    sessions = load_conductor_sessions(session_output_root=session_output_root)
    if not sessions:
        return ReviewerSessionOwnerState(provider=reviewer_provider)
    matching = [
        session
        for session in sessions
        if session.provider == reviewer_provider
        and session.role in {"reviewer", "review_agent", ""}
    ]
    if not matching:
        matching = [session for session in sessions if session.provider == reviewer_provider]
    if not matching:
        return ReviewerSessionOwnerState(provider=reviewer_provider)
    matching.sort(
        key=lambda session: (
            not session.live,
            session.age_seconds is None,
            session.age_seconds or 0,
        )
    )
    selected = matching[0]
    return ReviewerSessionOwnerState(
        provider=selected.provider,
        session_name=selected.session_name,
        session_pid=selected.session_pid,
        terminal_window_id=selected.terminal_window_id,
        script_path=selected.script_path,
    )
