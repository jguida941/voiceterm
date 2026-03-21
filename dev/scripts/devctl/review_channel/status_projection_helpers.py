"""Helpers extracted from status_projection to stay under code-shape limits."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from .daemon_reducer import DaemonSnapshot, empty_daemon_state
from ..governance.push_policy import load_push_policy
from ..governance.push_state import PushEnforcementSnapshot, detect_push_enforcement_state


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


def build_bridge_push_enforcement_state(repo_root: Path) -> dict[str, object]:
    """Load the repo-governance push/checkpoint state for bridge projections."""
    try:
        policy = load_push_policy(repo_root=repo_root)
        return detect_push_enforcement_state(policy, repo_root=repo_root)
    except (OSError, ValueError):
        return asdict(
            PushEnforcementSnapshot(
                default_remote="origin",
                development_branch="main",
                release_branch="main",
                pre_push_hook_path="",
                pre_push_hook_installed=False,
                raw_git_push_guarded=False,
                upstream_ref="",
                ahead_of_upstream_commits=None,
                dirty_path_count=0,
                untracked_path_count=0,
                max_dirty_paths_before_checkpoint=12,
                max_untracked_paths_before_checkpoint=6,
                checkpoint_required=False,
                safe_to_continue_editing=True,
                checkpoint_reason="clean_worktree",
                worktree_dirty=False,
                push_ready=False,
                recommended_action="use_devctl_push",
            )
        )


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
