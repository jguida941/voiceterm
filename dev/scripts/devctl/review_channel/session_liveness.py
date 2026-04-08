"""Typed liveness evidence for repo-owned conductor sessions."""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class SessionLivenessEvidence:
    """Typed evidence used to decide whether one conductor session is still live."""

    live: bool
    reason: str
    script_probe_state: str
    terminal_window_state: str


def build_session_liveness_evidence(
    *,
    process_running: bool | None,
    terminal_window_id: int | None,
    age_seconds: int | None,
    freshness_seconds: int,
    launch_authority_state: str = "",
    launch_authority_reason: str = "",
) -> SessionLivenessEvidence:
    """Resolve one session's liveness from process, Terminal, and log evidence."""
    script_probe_state = _script_probe_state(process_running)
    terminal_window_open = _probe_terminal_window_open(terminal_window_id)
    terminal_window_state = _terminal_window_state(
        terminal_window_id,
        terminal_window_open,
    )

    if process_running is True:
        return SessionLivenessEvidence(
            live=True,
            reason="existing conductor script process is still running",
            script_probe_state=script_probe_state,
            terminal_window_state=terminal_window_state,
        )

    if process_running is False and launch_authority_state == "stale":
        reason = launch_authority_reason or (
            "prepared launch authority is stale and the session is reclaimable"
        )
        if terminal_window_open is True and terminal_window_id is not None:
            reason = (
                f"Terminal window {terminal_window_id} is still open, but {reason}"
            )
        return SessionLivenessEvidence(
            live=False,
            reason=reason,
            script_probe_state=script_probe_state,
            terminal_window_state=terminal_window_state,
        )

    if terminal_window_open is True:
        if process_running is False:
            reason = (
                f"Terminal window {terminal_window_id} is still open even though the "
                "script process probe returned no match"
            )
        else:
            reason = (
                f"Terminal window {terminal_window_id} is still open while the script "
                "process could not be probed"
            )
        return SessionLivenessEvidence(
            live=True,
            reason=reason,
            script_probe_state=script_probe_state,
            terminal_window_state=terminal_window_state,
        )

    if age_seconds is not None and age_seconds <= freshness_seconds:
        probe_detail = (
            "returned no match"
            if process_running is False
            else "could not be probed"
        )
        return SessionLivenessEvidence(
            live=True,
            reason=(
                f"session trace was updated {age_seconds}s ago and the script process "
                f"{probe_detail}"
            ),
            script_probe_state=script_probe_state,
            terminal_window_state=terminal_window_state,
        )

    if process_running is False:
        reason = (
            "script process probe returned no match, no Terminal window remained "
            "open, and the session trace is stale"
        )
    else:
        reason = (
            "script process could not be probed, no Terminal window evidence was "
            "available, and the session trace is stale"
        )
    return SessionLivenessEvidence(
        live=False,
        reason=reason,
        script_probe_state=script_probe_state,
        terminal_window_state=terminal_window_state,
    )


def _script_probe_state(process_running: bool | None) -> str:
    if process_running is True:
        return "running"
    if process_running is False:
        return "not_found"
    return "unknown"


def _terminal_window_state(
    terminal_window_id: int | None,
    terminal_window_open: bool | None,
) -> str:
    if terminal_window_id is None:
        return "not_applicable"
    if terminal_window_open is True:
        return "open"
    if terminal_window_open is False:
        return "missing"
    return "unknown"


def _probe_terminal_window_open(terminal_window_id: int | None) -> bool | None:
    if terminal_window_id is None:
        return None
    if sys.platform != "darwin" or shutil.which("osascript") is None:
        return None
    try:
        result = subprocess.run(
            [
                "osascript",
                "-e",
                'tell application "Terminal"',
                "-e",
                f'if exists window id {int(terminal_window_id)} then return "open"',
                "-e",
                'return "missing"',
                "-e",
                "end tell",
            ],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    state = result.stdout.strip().lower()
    if state == "open":
        return True
    if state == "missing":
        return False
    return None
