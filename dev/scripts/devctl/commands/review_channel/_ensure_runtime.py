"""Runtime bindings for the review-channel ensure action."""

from __future__ import annotations

from collections.abc import Mapping
import time
from pathlib import Path

from ..review_channel_command import RuntimePaths
from . import ensure as _ensure_mod


def _build_ensure_action_deps() -> _ensure_mod.EnsureActionDeps:
    """Return command-layer callback bindings for ensure orchestration."""
    from . import _follow_runtime as compat_runtime

    return _ensure_mod.EnsureActionDeps(
        run_status_action_fn=compat_runtime._run_status_action,
        read_publisher_state_safe_fn=compat_runtime._read_publisher_state_safe,
        assess_publisher_lifecycle_fn=_ensure_mod.assess_publisher_lifecycle,
        spawn_follow_publisher_fn=compat_runtime._spawn_follow_publisher,
        verify_detached_start_fn=compat_runtime._verify_detached_start,
        refresh_bridge_heartbeat_fn=compat_runtime.refresh_bridge_heartbeat,
        reviewer_mode_is_active_fn=compat_runtime.reviewer_mode_is_active,
        run_ensure_follow_action_fn=compat_runtime.run_ensure_follow_action,
        spawn_reviewer_supervisor_fn=compat_runtime._spawn_reviewer_supervisor,
        verify_reviewer_supervisor_start_fn=(
            compat_runtime._verify_reviewer_supervisor_start
        ),
        sleep_fn=time.sleep,
    )


def run_ensure_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> tuple[dict, int]:
    """Run the reviewer-heartbeat ensure flow."""
    return _ensure_mod.run_ensure_action(
        args=args,
        repo_root=repo_root,
        paths=paths,
        deps=_build_ensure_action_deps(),
    )
