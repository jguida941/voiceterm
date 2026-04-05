"""Runtime bindings for the review-channel ensure-follow publisher."""

from __future__ import annotations

from collections.abc import Mapping
import time
from pathlib import Path

from ...review_channel.follow_controller import (
    EnsureFollowDeps,
    run_ensure_follow_action as _run_ensure_follow_action_impl,
)
from ...runtime.governance_scan import scan_repo_governance_safely
from ..review_channel_command import RuntimePaths, _coerce_runtime_paths


def _resolve_operator_interaction_mode(
    *,
    repo_root: Path,
    args_fallback: str = "",
) -> str:
    """Read operator interaction mode from ProjectGovernance typed state.

    Falls back to the CLI args value only when governance state is unavailable,
    so the follow loop does not depend on a launch-time flag surviving across
    daemon restarts.
    """
    governance = scan_repo_governance_safely(repo_root)
    if governance is not None:
        mode = (governance.bridge_config.operator_interaction_mode or "").strip()
        if mode:
            return mode
    return args_fallback.strip() or ""


def _build_ensure_follow_deps(
    *,
    operator_interaction_mode: str = "",
) -> EnsureFollowDeps:
    """Return late-bound follow deps so tests can patch the compat surface.

    When ``operator_interaction_mode`` is ``remote_control``, the publisher
    uses the auto-poll cadence for unprompted surface refreshes instead of
    waiting for an operator at the keyboard.
    """
    from . import _follow_runtime as compat_runtime

    return EnsureFollowDeps(
        ensure_reviewer_heartbeat_fn=compat_runtime.ensure_reviewer_heartbeat,
        reviewer_state_write_to_dict_fn=compat_runtime.reviewer_state_write_to_dict,
        run_status_action_fn=compat_runtime._run_status_action,
        attach_reviewer_worker_fn=compat_runtime._attach_reviewer_worker,
        ensure_reviewer_supervisor_running_fn=(
            compat_runtime._ensure_reviewer_supervisor_running
        ),
        emit_follow_ndjson_frame_fn=compat_runtime.emit_follow_ndjson_frame,
        reset_follow_output_fn=compat_runtime.reset_follow_output,
        build_follow_completion_report_fn=(
            compat_runtime.build_follow_completion_report
        ),
        build_follow_output_error_report_fn=(
            compat_runtime.build_follow_output_error_report
        ),
        write_publisher_heartbeat_fn=compat_runtime.write_publisher_heartbeat,
        read_publisher_state_fn=compat_runtime.read_publisher_state,
        utc_timestamp_fn=compat_runtime.utc_timestamp,
        sleep_fn=time.sleep,
        operator_interaction_mode=operator_interaction_mode,
    )


def run_ensure_follow_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> tuple[dict, int]:
    """Run the persistent ensure-follow publisher.

    Resolves operator interaction mode from governance typed state first,
    falling back to the CLI launch flag. The resolved value is propagated
    onto ``args`` so downstream recovery/rollover helpers also use it.
    """
    runtime_paths = _coerce_runtime_paths(paths)
    args_fallback = str(
        getattr(args, "operator_interaction_mode", "") or ""
    ).strip()
    interaction_mode = _resolve_operator_interaction_mode(
        repo_root=repo_root,
        args_fallback=args_fallback,
    )
    # Propagate governance-resolved mode onto args so downstream recovery
    # and rollover helpers read the typed value instead of a stale CLI flag.
    try:
        args.operator_interaction_mode = interaction_mode
    except (AttributeError, TypeError):
        pass
    return _run_ensure_follow_action_impl(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        deps=_build_ensure_follow_deps(
            operator_interaction_mode=interaction_mode,
        ),
    )
