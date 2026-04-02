"""Heartbeat suppression helpers for reviewer follow loops."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from .peer_liveness import reviewer_mode_is_active
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
    """Refresh automation heartbeats only when no real review pass is pending."""
    if reason in _AUTOMATION_HEARTBEAT_REASONS and _review_follow_up_pending(
        repo_root=repo_root,
        bridge_path=bridge_path,
        requested_reviewer_mode=requested_reviewer_mode,
    ):
        return EnsureHeartbeatResult(
            refreshed=False,
            reviewer_mode="active_dual_agent",
            reason=reason,
            state_write=None,
            error=None,
            suppressed=True,
        )
    return ensure_reviewer_heartbeat_fn(
        repo_root=repo_root,
        bridge_path=bridge_path,
        reason=reason,
        requested_reviewer_mode=requested_reviewer_mode,
    )


def _review_follow_up_pending(
    *,
    repo_root: Path,
    bridge_path: Path,
    requested_reviewer_mode: str | None,
) -> bool:
    if requested_reviewer_mode and not reviewer_mode_is_active(requested_reviewer_mode):
        return False
    tick = check_review_needed(
        repo_root=repo_root,
        bridge_path=bridge_path,
    )
    if not reviewer_mode_is_active(tick.reviewer_mode):
        return False
    return tick.review_needed
