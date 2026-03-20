"""Helpers extracted from status_projection to stay under code-shape limits."""

from __future__ import annotations

from .daemon_reducer import DaemonSnapshot, build_runtime_state, empty_daemon_state


def build_bridge_runtime(
    bridge_liveness: dict[str, object],
    reduced_runtime: dict[str, object] | None,
) -> dict[str, object]:
    """Build the runtime section, preferring event-reduced state when available."""
    if reduced_runtime and reduced_runtime.get("last_daemon_event_utc"):
        return reduced_runtime

    publisher_running = bool(bridge_liveness.get("publisher_running"))
    pub = DaemonSnapshot()
    pub.reviewer_mode = str(bridge_liveness.get("reviewer_mode") or "")
    pub.stop_reason = str(bridge_liveness.get("publisher_stop_reason") or "")

    return {
        "daemons": {
            "publisher": (
                pub.to_dict()
                if not publisher_running
                else _running_bridge_publisher(bridge_liveness)
            ),
            "reviewer_supervisor": empty_daemon_state(),
        },
        "active_daemons": 1 if publisher_running else 0,
        "last_daemon_event_utc": "",
    }


def _running_bridge_publisher(
    bridge_liveness: dict[str, object],
) -> dict[str, object]:
    """Build a publisher daemon dict from bridge liveness when running."""
    pub = DaemonSnapshot()
    pub.pid = 1
    pub.started_at_utc = "(bridge-derived)"
    pub.last_heartbeat_utc = "(bridge-derived)"
    pub.reviewer_mode = str(bridge_liveness.get("reviewer_mode") or "")
    return pub.to_dict()


def clean_section(raw: str) -> str:
    return raw.strip() or "(missing)"
