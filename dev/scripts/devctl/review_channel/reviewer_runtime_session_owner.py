"""Session-owner helpers for the typed reviewer-runtime contract."""

from __future__ import annotations

from pathlib import Path

from ..runtime.review_state_models import CollaborationSessionState
from ..runtime.reviewer_runtime_models import (
    RemoteControlAttachmentState,
    ReviewerSessionOwnerState,
)
from .remote_control_attachment_artifact import load_remote_control_attachment
from .collaboration_provider import collaboration_provider
from .session_probe import load_conductor_sessions


def conductor_visibility(
    *,
    session_output_root: Path | None,
) -> str:
    """Summarize whether the live conductor set is visible, headless, or mixed."""
    if not isinstance(session_output_root, Path):
        return "unknown"
    sessions = load_conductor_sessions(session_output_root=session_output_root)
    live_sessions = [session for session in sessions if session.live]
    if not live_sessions:
        return "none"
    has_visible = any(session.terminal_window_id is not None for session in live_sessions)
    has_headless = any(session.terminal_window_id is None for session in live_sessions)
    if has_visible and has_headless:
        return "mixed"
    if has_headless:
        return "headless"
    return "visible"


def session_visibility(terminal_window_id: int | None) -> str:
    """Classify one conductor session as visible or headless."""
    return "visible" if terminal_window_id is not None else "headless"


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
        session_visibility=session_visibility(selected.terminal_window_id),
    )


def resolve_remote_control_attachment(
    *,
    session_output_root: Path | None,
) -> RemoteControlAttachmentState | None:
    """Return the current external remote-control attachment when present."""
    if not isinstance(session_output_root, Path):
        return None
    return load_remote_control_attachment(output_root=session_output_root)
