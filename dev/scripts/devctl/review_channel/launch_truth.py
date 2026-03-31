"""Typed launch-truth classification for the active review loop."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.enum_compat import StrEnum
from .peer_liveness import ReviewerMode, normalize_reviewer_mode, reviewer_mode_is_active


class LaunchTruthState(StrEnum):
    """Validated launchability of the active review loop."""

    INACTIVE = "inactive"
    LIVE = "live"
    RUNTIME_MISSING = "runtime_missing"
    DETACHED_RUNTIME_ONLY = "detached_runtime_only"
    HYBRID_CLAUDE_ONLY = "hybrid_claude_only"
    AUTOMATION_ONLY = "automation_only"


def classify_launch_truth(bridge_liveness: dict[str, object]) -> LaunchTruthState:
    """Classify whether the declared dual-agent loop is actually launch-valid."""
    reviewer_mode = str(bridge_liveness.get("reviewer_mode") or "")
    if not reviewer_mode_is_active(reviewer_mode):
        return LaunchTruthState.INACTIVE
    if not (
        bool(bridge_liveness.get("publisher_running"))
        or bool(bridge_liveness.get("reviewer_supervisor_running"))
    ):
        return LaunchTruthState.RUNTIME_MISSING
    conductor_signal_present = any(
        key in bridge_liveness
        for key in (
            "active_conductor_providers",
            "codex_conductor_active",
            "claude_conductor_active",
        )
    )
    if not conductor_signal_present:
        return LaunchTruthState.LIVE
    codex_conductor_active = bool(bridge_liveness.get("codex_conductor_active"))
    claude_conductor_active = bool(bridge_liveness.get("claude_conductor_active"))
    if not codex_conductor_active and not claude_conductor_active:
        return LaunchTruthState.DETACHED_RUNTIME_ONLY
    if claude_conductor_active and not codex_conductor_active:
        return LaunchTruthState.HYBRID_CLAUDE_ONLY
    if codex_conductor_active and bool(bridge_liveness.get("poll_status_automation_only")):
        return LaunchTruthState.AUTOMATION_ONLY
    return LaunchTruthState.LIVE


def effective_reviewer_mode(bridge_liveness: Mapping[str, object]) -> str:
    """Return the validated reviewer mode for live-authority consumers."""

    reviewer_mode = normalize_reviewer_mode(
        str(bridge_liveness.get("reviewer_mode") or "")
    ).value
    if not reviewer_mode_is_active(reviewer_mode):
        return reviewer_mode

    launch_truth = str(
        bridge_liveness.get("launch_truth")
        or classify_launch_truth(dict(bridge_liveness)).value
    )
    if launch_truth == LaunchTruthState.LIVE.value:
        return reviewer_mode
    return ReviewerMode.TOOLS_ONLY.value
