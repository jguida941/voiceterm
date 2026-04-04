"""Launch-time control helpers for bridge-backed review-channel actions."""

from __future__ import annotations

import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ...review_channel.core import (
    AUTO_DARK_TERMINAL_PROFILES,
    DEFAULT_TERMINAL_PROFILE,
)
from ...review_channel.handoff import (
    extract_bridge_snapshot,
    summarize_bridge_liveness,
    wait_for_codex_poll_refresh,
    wait_for_rollover_ack,
    write_handoff_bundle,
)
from ...review_channel.heartbeat import compute_non_audit_worktree_hash
from ...review_channel.launch_truth import build_launch_probe_state, classify_launch_truth
from ...review_channel.lifecycle_state import (
    read_publisher_state,
    read_reviewer_supervisor_state,
)
from ...review_channel.launch import launch_terminal_sessions
from ...review_channel.session_probe import active_conductor_providers
from ...review_channel.terminal_app import cleanup_terminal_session

if TYPE_CHECKING:
    from ...review_channel.session_probe import ConductorSessionRecord

_PUBLISHER_START_WAIT_POLLS = 10
_PUBLISHER_START_WAIT_SECONDS = 0.1


@dataclass(frozen=True)
class LaunchSessionRequest:
    """Typed launch inputs for the bridge-backed conductor start path."""

    args: object
    sessions: list[dict[str, object]]
    bridge_path: Path
    handoff_bundle: object
    terminal_profile_applied: str | None
    launch_terminal_sessions_fn: Callable[..., None] = launch_terminal_sessions
    retired_sessions: tuple["ConductorSessionRecord", ...] = ()
    cleanup_terminal_session_fn: Callable[..., list[str]] = cleanup_terminal_session
    observe_launch_state_fn: Callable[[], dict[str, object]] | None = None


def prepare_rollover_bundle(
    *,
    args,
    repo_root: Path,
    bridge_path: Path,
    review_channel_path: Path,
    rollover_dir: Path,
    lanes: list,
) -> tuple[object | None, list[str]]:
    """Write a rollover handoff bundle if the action is rollover."""
    if args.action != "rollover":
        return None, []
    rollover_bridge_rel = str(bridge_path.relative_to(repo_root))
    try:
        rollover_hash = compute_non_audit_worktree_hash(
            repo_root=repo_root,
            excluded_rel_paths=(rollover_bridge_rel,),
        )
    except (ValueError, OSError):
        rollover_hash = None
    handoff_bundle = write_handoff_bundle(
        repo_root=repo_root,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        output_root=rollover_dir,
        trigger=args.rollover_trigger,
        threshold_pct=args.rollover_threshold_pct,
        lane_assignments=[_lane_assignment_dict(lane) for lane in lanes],
        current_worktree_hash=rollover_hash,
    )
    return handoff_bundle, [
        "Planned rollover created a repo-visible handoff bundle. "
        "Fresh sessions should acknowledge it before the old sessions exit."
    ]


def launch_sessions_if_requested(
    request: LaunchSessionRequest,
) -> tuple[bool, bool, dict[str, bool] | None, list[str]]:
    """Launch conductor sessions via Terminal.app or headless subprocess."""
    args = request.args
    launched = False
    handoff_ack_required = False
    handoff_ack_observed = None
    cleanup_warnings: list[str] = []
    if args.action not in {"launch", "rollover"} or args.dry_run:
        return launched, handoff_ack_required, handoff_ack_observed, cleanup_warnings
    prelaunch_snapshot = extract_bridge_snapshot(
        request.bridge_path.read_text(encoding="utf-8")
    )
    prelaunch_poll_utc = prelaunch_snapshot.metadata.get("last_codex_poll_utc")
    prelaunch_poll_status = prelaunch_snapshot.sections.get("Poll Status", "")
    if args.terminal == "terminal-app":
        request.launch_terminal_sessions_fn(
            request.sessions,
            terminal_profile=request.terminal_profile_applied,
            default_terminal_profile=DEFAULT_TERMINAL_PROFILE,
            auto_dark_terminal_profiles=AUTO_DARK_TERMINAL_PROFILES,
        )
        launched = True
    elif args.terminal == "none":
        launched = _launch_sessions_headless(request.sessions, cleanup_warnings)
    if not launched:
        return launched, handoff_ack_required, handoff_ack_observed, cleanup_warnings
    if args.action == "launch" and args.terminal == "terminal-app" and args.await_ack_seconds > 0:
        launch_poll = wait_for_codex_poll_refresh(
            bridge_path=request.bridge_path,
            previous_poll_utc=prelaunch_poll_utc,
            previous_poll_status=prelaunch_poll_status,
            timeout_seconds=args.await_ack_seconds,
            observe_launch_state_fn=request.observe_launch_state_fn,
        )
        if not bool(launch_poll.get("observed")):
            raise ValueError(
                "Live review-channel launch did not produce a fresh Codex "
                f"reviewer turn within {args.await_ack_seconds}s. "
                + _render_launch_timeout_detail(
                    launch_poll=launch_poll,
                    previous_poll_utc=prelaunch_poll_utc,
                )
            )
    if args.action == "rollover" and request.handoff_bundle is not None and args.await_ack_seconds > 0:
        handoff_ack_required = True
        handoff_ack_observed = wait_for_rollover_ack(
            bridge_path=request.bridge_path,
            rollover_id=request.handoff_bundle.rollover_id,
            timeout_seconds=args.await_ack_seconds,
        )
    if (
        args.action == "rollover"
        and request.retired_sessions
        and (
            not handoff_ack_required
            or (
                isinstance(handoff_ack_observed, dict)
                and bool(handoff_ack_observed)
                and all(bool(value) for value in handoff_ack_observed.values())
            )
        )
    ):
        for retired_session in request.retired_sessions:
            cleanup_warnings.extend(
                request.cleanup_terminal_session_fn(retired_session)
            )
    return launched, handoff_ack_required, handoff_ack_observed, cleanup_warnings


def _launch_sessions_headless(
    sessions: list[dict[str, object]],
    warnings: list[str],
) -> bool:
    """Start conductor sessions as detached background processes (no GUI).

    Each session has a ``launch_command`` pointing at a shell script that
    already handles supervised restart.  This path spawns each script in a
    new process group so it survives the parent daemon exiting.
    """
    any_launched = False
    for session in sessions:
        script_path = str(session.get("script_path") or "").strip()
        if not script_path or not Path(script_path).is_file():
            warnings.append(
                f"Headless launch skipped: script not found at {script_path}"
            )
            continue
        log_path_str = str(session.get("log_path") or "").strip()
        log_handle = None
        try:
            if log_path_str:
                log_path = Path(log_path_str)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                log_handle = log_path.open("a", encoding="utf-8")
            subprocess.Popen(
                ["/bin/zsh", script_path],
                cwd=str(Path(script_path).parent),
                stdout=log_handle or subprocess.DEVNULL,
                stderr=log_handle or subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
            any_launched = True
        except OSError as exc:
            warnings.append(f"Headless launch failed for {script_path}: {exc}")
            if log_handle is not None:
                log_handle.close()
    return any_launched


def _lane_assignment_dict(lane) -> dict[str, object]:
    return dict(
        agent_id=lane.agent_id,
        provider=lane.provider,
        lane=lane.lane,
        worktree=lane.worktree,
        branch=lane.branch,
        mp_scope=lane.mp_scope,
    )


def _render_launch_timeout_detail(
    *,
    launch_poll: dict[str, object],
    previous_poll_utc: str | None,
) -> str:
    latest_poll_utc = str(launch_poll.get("last_codex_poll_utc") or "missing")
    previous_poll_display = previous_poll_utc or "missing"
    poll_status_detail: list[str] = []
    if bool(launch_poll.get("poll_advanced")):
        poll_status_detail.append(f"`Last Codex poll` advanced to {latest_poll_utc}")
    else:
        poll_status_detail.append(f"`Last Codex poll` stayed at {latest_poll_utc}")
    if bool(launch_poll.get("poll_status_automation_only")):
        poll_reason = str(launch_poll.get("poll_status_reason") or "unknown")
        poll_status_detail.append(
            "`Poll Status` only showed an automation heartbeat "
            f"(reason: {poll_reason})"
        )
    elif not bool(launch_poll.get("poll_status_changed")):
        poll_status_detail.append(
            "`Poll Status` did not change from the pre-launch reviewer state"
        )
    launch_truth = str(launch_poll.get("launch_truth") or "").strip()
    if launch_truth:
        poll_status_detail.append(f"typed launch truth stayed `{launch_truth}`")
    if not bool(launch_poll.get("codex_conductor_active")):
        poll_status_detail.append(
            "typed status did not show a live Codex conductor session"
        )
    if not bool(launch_poll.get("claude_conductor_active")):
        poll_status_detail.append(
            "typed status did not show a live Claude conductor session"
        )
    return "; ".join(poll_status_detail) + f" (pre-launch poll {previous_poll_display})."


def ensure_launch_runtime_daemons(
    *,
    args,
    repo_root: Path,
    review_channel_path: Path,
    bridge_path: Path,
    status_dir: Path,
    reviewer_mode: str,
) -> tuple[bool, list[str]]:
    """Start the detached launch-time publisher if needed.

    The persistent ensure-follow publisher owns long-lived daemon liveness for
    the review channel. Once it is alive, its normal cadence reclaims the
    detached reviewer-supervisor runtime when active review mode still requires
    it, so live launch only needs to prove the publisher is up.
    """
    del reviewer_mode

    from ._publisher import spawn_follow_publisher, verify_detached_start

    runtime_paths = {
        "review_channel_path": review_channel_path,
        "bridge_path": bridge_path,
        "status_dir": status_dir,
    }
    publisher_state = read_publisher_state(status_dir)
    if not bool(publisher_state.get("running")):
        started, pid, _log_path = spawn_follow_publisher(
            args=args,
            repo_root=repo_root,
            paths=runtime_paths,
        )
        if not started:
            return False, [
                "Persistent publisher start failed before launch confirmation."
            ]
        for _ in range(_PUBLISHER_START_WAIT_POLLS):
            time.sleep(_PUBLISHER_START_WAIT_SECONDS)
            publisher_state = read_publisher_state(status_dir)
            if bool(publisher_state.get("running")):
                break
        else:
            start_status = verify_detached_start(pid=pid, paths=runtime_paths)
            if start_status != "started":
                return False, [
                    "Persistent publisher failed to stay alive after launch."
                ]
    return True, []


def observe_launch_state(
    *,
    args,
    context,
    warnings: list[str],
    refresh_snapshot_fn: Callable[..., object],
) -> dict[str, object]:
    """Project the post-launch liveness fields used by launch-time waiting."""
    try:
        snapshot = extract_bridge_snapshot(context.bridge_path.read_text(encoding="utf-8"))
        bridge_liveness = summarize_bridge_liveness(snapshot)
        active_providers = active_conductor_providers(
            session_output_root=context.status_dir,
        )

        codex_active = "codex" in active_providers
        claude_active = "claude" in active_providers
        launch_state = build_launch_probe_state(
            bridge_liveness, active_providers, context.status_dir,
        )
        truth = classify_launch_truth(launch_state).value
        return {
            "launch_truth": truth,
            "codex_conductor_active": codex_active,
            "claude_conductor_active": claude_active,
        }
    except OSError:
        bridge_liveness = refresh_snapshot_fn(
            args=args,
            context=context,
            warnings=warnings,
        ).bridge_liveness
    return {
        "launch_truth": bridge_liveness.get("launch_truth"),
        "codex_conductor_active": bridge_liveness.get("codex_conductor_active"),
        "claude_conductor_active": bridge_liveness.get("claude_conductor_active"),
    }
