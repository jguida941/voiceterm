"""Daemon and conductor liveness helpers for control-plane resolution."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def resolve_daemon_state(sources: dict[str, Any]) -> dict[str, Any]:
    """Derive publisher/supervisor/conductor liveness from heartbeats."""
    pub_running = _is_daemon_running(sources.get("publisher_hb"))
    sup_running = _is_daemon_running(sources.get("supervisor_hb"))
    codex_alive = _is_conductor_alive(sources.get("codex_conductor"))
    claude_alive = _is_conductor_alive(sources.get("claude_conductor"))
    return {
        "publisher_running": pub_running,
        "supervisor_running": sup_running,
        "codex_conductor_alive": codex_alive,
        "claude_conductor_alive": claude_alive,
    }


def load_conductor_sources(paths: dict[str, Path]) -> dict[str, dict[str, Any]]:
    from ..review_channel.session_probe import load_conductor_sessions

    session_output_root = paths["codex_conductor"].parent.parent
    records = load_conductor_sessions(session_output_root=session_output_root)
    sources: dict[str, dict[str, Any]] = {}
    for record in records:
        if record.session_pid is None and not record.live:
            continue
        sources[record.provider] = {
            "provider": record.provider,
            "session_pid": record.session_pid,
            "live": record.live,
            "script_path": record.script_path,
        }
    return sources


def _is_daemon_running(data: dict[str, Any] | None) -> bool:
    if data is None:
        return False
    return not bool(data.get("stopped_at_utc", ""))


def _is_conductor_alive(data: dict[str, Any] | None) -> bool:
    if data is None:
        return False
    live = data.get("live")
    if isinstance(live, bool):
        return live
    pid = data.get("session_pid")
    if not isinstance(pid, int) or pid <= 0:
        return False
    return pid_is_alive(pid)


def pid_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, OSError):
        return False
