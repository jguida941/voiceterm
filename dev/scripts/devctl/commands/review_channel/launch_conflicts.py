"""Typed launch-conflict handling for visible review-channel launches."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from ...review_channel.core import (
    detect_active_session_conflicts,
    summarize_active_session_conflicts,
)
from ...review_channel.session_probe import load_conductor_sessions
from ...review_channel.terminal_app import cleanup_terminal_session


def validate_live_launch_conflicts(
    *,
    args,
    status_dir: Path,
    detect_active_session_conflicts_fn: Callable[..., object] | None = None,
    summarize_active_session_conflicts_fn: Callable[..., str] | None = None,
    load_conductor_sessions_fn: Callable[..., tuple] | None = None,
    cleanup_terminal_session_fn: Callable[..., list[str]] | None = None,
) -> None:
    """Reject duplicate live launches and reclaim stale visible sessions first."""
    if detect_active_session_conflicts_fn is None:
        detect_active_session_conflicts_fn = detect_active_session_conflicts
    if summarize_active_session_conflicts_fn is None:
        summarize_active_session_conflicts_fn = summarize_active_session_conflicts
    if load_conductor_sessions_fn is None:
        load_conductor_sessions_fn = load_conductor_sessions
    if cleanup_terminal_session_fn is None:
        cleanup_terminal_session_fn = cleanup_terminal_session
    if args.action != "launch" or args.terminal != "terminal-app" or args.dry_run:
        return

    reclaimable_sessions = _reclaimable_launch_sessions(
        load_conductor_sessions_fn(session_output_root=status_dir),
    )
    for session in reclaimable_sessions:
        cleanup_terminal_session_fn(session)

    stubborn_reclaimable_sessions = _reclaimable_launch_sessions(
        load_conductor_sessions_fn(session_output_root=status_dir),
    )
    if stubborn_reclaimable_sessions:
        raise ValueError(
            "Live review-channel launch refused because stale Terminal session "
            "windows could not be reclaimed before relaunch. Close the stale "
            "conductor windows and retry: "
            + _summarize_reclaimable_launch_sessions(stubborn_reclaimable_sessions)
        )

    active_session_conflicts = detect_active_session_conflicts_fn(
        session_output_root=status_dir,
    )
    if active_session_conflicts:
        raise ValueError(
            "Live review-channel launch refused because existing session "
            "artifacts still look active. Close the current conductor "
            "windows or wait for the session traces to go stale before "
            "launching again: "
            + summarize_active_session_conflicts_fn(active_session_conflicts)
        )


def _reclaimable_launch_sessions(sessions: tuple) -> tuple:
    reclaimable = []
    for session in sessions:
        if getattr(session, "launch_authority_state", "") != "stale":
            continue
        if getattr(session, "script_probe_state", "") != "not_found":
            continue
        if getattr(session, "terminal_window_state", "") != "open":
            continue
        reclaimable.append(session)
    return tuple(reclaimable)


def _summarize_reclaimable_launch_sessions(sessions: tuple) -> str:
    details = []
    for session in sessions:
        reason = (
            getattr(session, "launch_authority_reason", "")
            or getattr(session, "live_reason", "")
            or "stale prepared launch authority"
        )
        details.append(f"{session.provider}: {reason}")
    return "; ".join(details)
