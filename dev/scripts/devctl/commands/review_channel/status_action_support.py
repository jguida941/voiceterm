"""Small helpers for review-channel status action."""

from __future__ import annotations

from pathlib import Path

from ...review_channel.core import bridge_is_active
from ...review_channel.state_status_inputs import read_status_json_mapping
from .status_readiness import attach_runtime_readiness
from ..review_channel_command import RuntimePaths


def read_review_state_sync_payload(path: Path) -> dict[str, object] | None:
    return read_status_json_mapping(path)


def dry_run_stale_heartbeat_projection_sync_requested(args, snapshot) -> bool:
    if not bool(getattr(args, "dry_run", False)):
        return False
    if not bool(getattr(args, "refresh_bridge_heartbeat_if_stale", False)):
        return False
    return str(snapshot.bridge_liveness.get("codex_poll_state") or "").strip() in {
        "missing",
        "stale",
    }


def normalize_read_only_status_ok(report: dict[str, object]) -> None:
    """Keep read-only status command health separate from runtime attention."""
    if str(report.get("action") or "").strip() != "status":
        return
    if report.get("errors"):
        report["exit_ok"] = False
        attach_runtime_readiness(report)
        return
    report["exit_ok"] = True
    attach_runtime_readiness(report)


def auto_mode_prefers_markdown_bridge(paths: RuntimePaths) -> bool:
    """Prefer bridge-backed status when the transitional bridge is active."""
    bridge_path = paths.bridge_path
    review_channel_path = paths.review_channel_path
    if not isinstance(bridge_path, Path) or not isinstance(review_channel_path, Path):
        return False
    if not bridge_path.exists() or not review_channel_path.exists():
        return False
    try:
        return bridge_is_active(review_channel_path.read_text(encoding="utf-8"))
    except OSError:
        return False


__all__ = [
    "auto_mode_prefers_markdown_bridge",
    "dry_run_stale_heartbeat_projection_sync_requested",
    "normalize_read_only_status_ok",
    "read_review_state_sync_payload",
]
