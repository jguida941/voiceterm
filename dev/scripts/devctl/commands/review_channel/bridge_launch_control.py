"""Launch-time control helpers for bridge-backed review-channel actions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ...review_channel.core import (
    AUTO_DARK_TERMINAL_PROFILES,
    DEFAULT_TERMINAL_PROFILE,
)
from ...review_channel.handoff import (
    extract_bridge_snapshot,
    wait_for_codex_poll_refresh,
    wait_for_rollover_ack,
    write_handoff_bundle,
)
from ...review_channel.heartbeat import compute_non_audit_worktree_hash
from ...review_channel.launch import launch_terminal_sessions


@dataclass(frozen=True)
class LaunchSessionRequest:
    """Typed launch inputs for the bridge-backed conductor start path."""

    args: object
    sessions: list[dict[str, object]]
    bridge_path: Path
    handoff_bundle: object
    terminal_profile_applied: str | None
    launch_terminal_sessions_fn: Callable[..., None] = launch_terminal_sessions
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
) -> tuple[bool, bool, dict[str, bool] | None]:
    """Open Terminal.app windows and optionally wait for rollover ACK."""
    args = request.args
    launched = False
    handoff_ack_required = False
    handoff_ack_observed = None
    prelaunch_snapshot = extract_bridge_snapshot(
        request.bridge_path.read_text(encoding="utf-8")
    )
    prelaunch_poll_utc = prelaunch_snapshot.metadata.get("last_codex_poll_utc")
    prelaunch_poll_status = prelaunch_snapshot.sections.get("Poll Status", "")
    if args.action in {"launch", "rollover"} and args.terminal == "terminal-app" and not args.dry_run:
        request.launch_terminal_sessions_fn(
            request.sessions,
            terminal_profile=request.terminal_profile_applied,
            default_terminal_profile=DEFAULT_TERMINAL_PROFILE,
            auto_dark_terminal_profiles=AUTO_DARK_TERMINAL_PROFILES,
        )
        launched = True
        if args.action == "launch" and args.await_ack_seconds > 0:
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
    return launched, handoff_ack_required, handoff_ack_observed


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
