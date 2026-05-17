"""Default values for ControlPlaneReadModel deserialization fallback."""

from __future__ import annotations

from .auto_mode import AutoModePhase


def default_read_model_kwargs() -> dict[str, object]:
    """Return constructor kwargs for an empty control-plane read model."""
    return {
        "timestamp": "",
        "branch": "unknown",
        "head_sha": "unknown",
        "snapshot_id": "",
        "zref": "",
        "worktree_clean": True,
        "ahead_of_upstream": 0,
        "resolved_phase": AutoModePhase.IDLE.value,
        "push_eligible": False,
        "implementation_blocked": False,
        "top_blocker": "none",
        "next_action": "n/a",
        "next_command": "",
        "reviewer_mode": "single_agent",
        "operator_interaction_mode": "unresolved",
        "reviewer_freshness": "--",
        "review_accepted": False,
        "last_reviewed_sha": "",
        "attention_status": "n/a",
        "attention_summary": "n/a",
        "publisher_running": False,
        "supervisor_running": False,
        "codex_conductor_alive": False,
        "claude_conductor_alive": False,
        "pending_action_requests": 0,
        "last_guard_ok": True,
        "check_details": (),
        "loop_wake_mode": "unknown",
        "loop_wake_interval_seconds": 0,
        "loop_driver_agent": "",
        "loop_autonomy_ok": False,
        "loop_gap_summary": "",
        "remote_control_attachment": None,
        "session_posture": None,
        "coordination": None,
    }


__all__ = ["default_read_model_kwargs"]
