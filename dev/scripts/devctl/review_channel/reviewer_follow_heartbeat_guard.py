"""Heartbeat suppression helpers for reviewer follow loops."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from .reviewer_state import ensure_reviewer_heartbeat
from .reviewer_state_support import EnsureHeartbeatResult
from .reviewer_worker import check_review_needed

_AUTOMATION_HEARTBEAT_REASONS = frozenset({"ensure-follow", "reviewer-follow"})


def maybe_refresh_automation_reviewer_heartbeat(
    *,
    repo_root: Path,
    bridge_path: Path,
    reason: str,
    requested_reviewer_mode: str | None = None,
    ensure_reviewer_heartbeat_fn: Callable[..., EnsureHeartbeatResult] = ensure_reviewer_heartbeat,
) -> EnsureHeartbeatResult:
    """Suppress automation-only follow heartbeats from tracked bridge writes."""
    if reason in _AUTOMATION_HEARTBEAT_REASONS:
        return _suppressed_automation_heartbeat_result(
            repo_root=repo_root,
            bridge_path=bridge_path,
            reason=reason,
            requested_reviewer_mode=requested_reviewer_mode,
        )
    return ensure_reviewer_heartbeat_fn(
        repo_root=repo_root,
        bridge_path=bridge_path,
        reason=reason,
        requested_reviewer_mode=requested_reviewer_mode,
    )


def _suppressed_automation_heartbeat_result(
    *,
    repo_root: Path,
    bridge_path: Path,
    reason: str,
    requested_reviewer_mode: str | None,
) -> EnsureHeartbeatResult:
    return EnsureHeartbeatResult(
        refreshed=False,
        reviewer_mode=_automation_reviewer_mode(
            repo_root=repo_root,
            bridge_path=bridge_path,
            requested_reviewer_mode=requested_reviewer_mode,
        ),
        reason=reason,
        state_write=None,
        error=None,
        suppressed=True,
    )


def _automation_reviewer_mode(
    *,
    repo_root: Path,
    bridge_path: Path,
    requested_reviewer_mode: str | None,
) -> str:
    requested = str(requested_reviewer_mode or "").strip()
    if requested:
        return requested
    try:
        tick = check_review_needed(repo_root=repo_root, bridge_path=bridge_path)
    except (OSError, ValueError):
        return "active_dual_agent"
    mode = str(tick.reviewer_mode or "").strip()
    return mode or "active_dual_agent"
