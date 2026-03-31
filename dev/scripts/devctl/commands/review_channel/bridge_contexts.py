"""Typed contexts for bridge-backed review-channel actions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LaunchRefreshContext:
    """Grouped bridge-launch paths needed for post-launch refresh work."""

    repo_root: Path
    review_channel_path: Path
    bridge_path: Path
    status_dir: Path
    promotion_plan_path: Path | None
    artifact_paths: object


@dataclass(frozen=True)
class BridgeReportContext:
    """Grouped bridge-report inputs used by the final bridge-backed render path."""

    repo_root: Path
    review_channel_path: Path
    bridge_path: Path
    status_dir: Path
    status_snapshot: object
    codex_lanes: list
    claude_lanes: list
    terminal_profile_applied: str | None
    sessions: list[dict[str, object]]
    handoff_bundle: object
    launched: bool
    handoff_ack_required: bool
    handoff_ack_observed: dict[str, bool] | None
    promotion: object
    bridge_heartbeat_refresh: object
    reviewer_state_write: object
