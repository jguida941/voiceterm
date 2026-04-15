"""Health/liveness builders for the DashboardSnapshot."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ..review_channel.runtime_counts import build_runtime_counts
from ..review_channel.session_probe import load_conductor_sessions
from .dashboard_utils import (
    _age_seconds,
    _format_age,
    _paths,
    _read_json,
)


def _read_heartbeat(path: Path) -> dict[str, Any]:
    """Read a daemon heartbeat file and derive running state from OS liveness."""
    data = _read_json(path)
    if data is None:
        return {
            "running": False, "pid": 0, "last_heartbeat": "n/a",
            "last_heartbeat_age": "--", "snapshots": 0,
        }
    stopped = data.get("stopped_at_utc", "")
    pid = data.get("pid", 0)
    running = (
        not bool(stopped)
        and isinstance(pid, int)
        and pid > 0
        and _pid_is_alive(pid)
    )
    hb_utc = data.get("last_heartbeat_utc", "n/a")
    return {
        "running": running,
        "pid": pid,
        "last_heartbeat": hb_utc,
        "last_heartbeat_age": _format_age(_age_seconds(hb_utc)),
        "snapshots": data.get("snapshots_emitted", 0),
    }


def _pid_is_alive(pid: int) -> bool:
    """Check whether a process with the given PID is currently running."""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, OSError):
        return False


def _read_conductor_liveness(path: Path) -> dict[str, Any]:
    """Read conductor liveness through the shared repo-owned session probe."""
    data = _read_json(path)
    if data is None:
        return {"pid": None, "alive": False}

    provider = str(data.get("provider") or path.stem.removesuffix("-conductor")).strip()
    session_output_root = path.parent.parent
    for record in load_conductor_sessions(session_output_root=session_output_root):
        if record.provider != provider:
            continue
        if record.session_pid is None and not record.live:
            break
        return {"pid": record.session_pid, "alive": record.live}

    pid = data.get("session_pid")
    if pid is None or not isinstance(pid, int) or pid <= 0:
        return {"pid": None, "alive": False}
    return {"pid": pid, "alive": _pid_is_alive(pid)}


def build_health_section(
    repo_root: Path,
    compact: dict[str, Any] | None,
    *,
    runtime_counts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the HEALTH section from daemon heartbeats, conductors, and attention."""
    p = _paths()
    publisher = _read_heartbeat(repo_root / p["publisher_hb"])
    supervisor = _read_heartbeat(repo_root / p["supervisor_hb"])

    codex_conductor = _read_conductor_liveness(repo_root / p["codex_conductor_session"])
    claude_conductor = _read_conductor_liveness(repo_root / p["claude_conductor_session"])

    full_data = _read_json(repo_root / p["full_json"])
    attention = (full_data or {}).get("attention", {})
    attention_status = attention.get("status", "n/a")
    attention_summary = attention.get("summary", "n/a")

    active_daemons = sum(1 for d in (publisher, supervisor) if d["running"])
    agent_counts = runtime_counts or build_runtime_counts(
        publisher_running=publisher["running"],
        reviewer_supervisor_running=supervisor["running"],
        bridge_liveness={
            "codex_conductor_active": codex_conductor["alive"],
            "claude_conductor_active": claude_conductor["alive"],
            "publisher_running": publisher["running"],
            "reviewer_supervisor_running": supervisor["running"],
        },
    )

    health: dict[str, Any] = {
        "publisher": publisher,
        "supervisor": supervisor,
        "codex_conductor": codex_conductor,
        "claude_conductor": claude_conductor,
    }
    health["attention_status"] = attention_status
    health["attention_summary"] = attention_summary
    health["active_daemons"] = active_daemons
    health["agent_counts"] = agent_counts
    return health
