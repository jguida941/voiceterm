"""Watcher lease projection for `/develop` reports."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ....review_channel.event_store import resolve_artifact_paths
from ....review_channel.watch_paths import watch_state_path
from ..models import DevelopmentWatcherLease
from .clock import stale_seconds as stored_stale_seconds
from .messages import watch_command, watcher_summary
from .runtime_rows import (
    last_seen_event_id,
    runtime_actor_idle_seconds,
    watched_actor,
)
from .state import load_state, state_text, watcher_status

_WATCHER_STALE_AFTER_SECONDS = 300
_PENDING_STATUS = "pending"


def watcher_lease_status(
    repo_root: Path,
    review_state: Mapping[str, object],
    *,
    actor: str,
) -> DevelopmentWatcherLease:
    """Return the typed watcher lease/status expected by `/develop`."""
    target_actor = watched_actor(review_state, actor=actor)
    artifact_root = Path(resolve_artifact_paths(repo_root=repo_root).artifact_root)
    state_path = watch_state_path(
        artifact_root=artifact_root,
        target=target_actor,
        status_filter=_PENDING_STATUS,
    )
    state = load_state(state_path)
    runtime_idle_seconds = runtime_actor_idle_seconds(review_state, target_actor)
    freshness = _watcher_freshness_seconds(
        state=state,
        runtime_idle_seconds=runtime_idle_seconds,
    )
    status = watcher_status(
        state,
        runtime_idle_seconds=runtime_idle_seconds,
        stale_seconds=freshness,
        stale_after_seconds=_WATCHER_STALE_AFTER_SECONDS,
    )
    return DevelopmentWatcherLease(
        lease_id=state_text(state.get("watch_key")) or f"watch_{target_actor}__pending",
        watcher_id=f"{target_actor}-pending-watcher",
        watched_actor=target_actor,
        watched_surfaces=(
            "review-channel inbox",
            "review-channel watch",
            "agent-mind",
            "develop status",
        ),
        status=status,
        last_seen_event_id=last_seen_event_id(review_state, target_actor),
        stale_after_seconds=_WATCHER_STALE_AFTER_SECONDS,
        stale_seconds=freshness,
        next_report_command=watch_command(target_actor),
        source_path=str(state_path),
        summary=watcher_summary(
            watched_actor=target_actor,
            status=status,
            stale_seconds=freshness,
            runtime_observed=(
                runtime_idle_seconds is not None
                and runtime_idle_seconds <= _WATCHER_STALE_AFTER_SECONDS
            ),
        ),
    )


def _watcher_freshness_seconds(
    *,
    state: Mapping[str, object],
    runtime_idle_seconds: int | None,
) -> int:
    stored_freshness = stored_stale_seconds(state)
    if state and not state_text(state.get("stop_reason")):
        candidates = [stored_freshness]
        if runtime_idle_seconds is not None:
            candidates.append(runtime_idle_seconds)
        return min(candidates)
    if runtime_idle_seconds is not None:
        return runtime_idle_seconds
    return stored_freshness


__all__ = ["watcher_lease_status"]
