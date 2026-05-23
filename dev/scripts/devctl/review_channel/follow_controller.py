"""Follow-loop helpers for review-channel ensure publisher status."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .follow_loop import (
    FollowActionShape,
    FollowLoopTick,
    build_claude_progress_token,
    run_configured_follow_action,
)
from .lifecycle_state import PublisherHeartbeat
from .wake_receipt_models import WakeReceiptExtras
from .reviewer_follow_guard import (
    ReviewerWakeDeps,
    maybe_refresh_automation_reviewer_heartbeat,
    wake_report,
)
from ..runtime.reviewer_mode import reviewer_mode_is_active
from .reviewer_head_tracking import compute_review_range
from .follow_controller_wake_target import (
    resolve_reviewer_wake_target as _resolve_reviewer_wake_target,
)
from .event_store import active_push_window_write_suspension


@dataclass(frozen=True)
class EnsureFollowDeps:
    ensure_reviewer_heartbeat_fn: Callable[..., object]
    reviewer_state_write_to_dict_fn: Callable[..., dict[str, object] | None]
    run_status_action_fn: Callable[..., tuple[dict, int]]
    attach_reviewer_worker_fn: Callable[..., None]
    ensure_reviewer_supervisor_running_fn: Callable[..., dict[str, object] | None] | None
    emit_follow_ndjson_frame_fn: Callable[..., int]
    reset_follow_output_fn: Callable[..., None]
    build_follow_completion_report_fn: Callable[..., dict[str, object]]
    build_follow_output_error_report_fn: Callable[..., dict[str, object]]
    write_publisher_heartbeat_fn: Callable[..., Path]
    read_publisher_state_fn: Callable[..., dict[str, object]]
    write_monitor_snapshot_fn: Callable[..., object] | None
    utc_timestamp_fn: Callable[[], str]
    sleep_fn: Callable[[float], None]
    operator_interaction_mode: str = ""


def run_ensure_follow_action(*, args, repo_root: Path, paths: dict[str, object], deps: EnsureFollowDeps) -> tuple[dict, int]:
    """Refresh and publish ensure/status frames on cadence."""
    return run_configured_follow_action(
        args=args, repo_root=repo_root, paths=paths, deps_source=deps,
        action=_ensure_follow_action_shape(deps),
        build_tick_fn=lambda: _build_ensure_follow_tick(args=args, repo_root=repo_root, paths=paths, deps=deps),
    )


def _ensure_follow_action_shape(deps: EnsureFollowDeps) -> FollowActionShape:
    return FollowActionShape(
        daemon_kind="publisher",
        completion_action="ensure",
        output_error_action="ensure",
        write_heartbeat_fn=deps.write_publisher_heartbeat_fn,
        heartbeat_factory=PublisherHeartbeat,
    )


def _build_ensure_follow_tick(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
    deps: EnsureFollowDeps,
) -> FollowLoopTick:
    bridge_path = paths.get("bridge_path")
    status_dir = paths.get("status_dir")
    assert isinstance(bridge_path, Path)
    suspension = active_push_window_write_suspension(repo_root=repo_root)
    if suspension is not None:
        report: dict[str, object] = {
            "command": "review-channel",
            "action": "ensure",
            "status": "paused_by_vcs_window",
            "reason": "vcs_window_write_suspension_active",
            "vcs_window_write_suspension": suspension,
            "reviewer_heartbeat_suppressed": True,
        }
        if isinstance(status_dir, Path):
            report["publisher"] = deps.read_publisher_state_fn(status_dir)
        return FollowLoopTick(
            report=report,
            exit_code=0,
            reviewer_mode="publisher_suspended",
        )
    progress_token = build_claude_progress_token(
        repo_root=repo_root,
        bridge_path=bridge_path,
    )
    ensure_result = maybe_refresh_automation_reviewer_heartbeat(
        repo_root=repo_root,
        bridge_path=bridge_path,
        reason="ensure-follow",
        ensure_reviewer_heartbeat_fn=deps.ensure_reviewer_heartbeat_fn,
    )
    report, exit_code = deps.run_status_action_fn(
        args=args,
        repo_root=repo_root,
        paths=paths,
    )
    reviewer_supervisor_auto_start = _maybe_restart_reviewer_supervisor(
        deps=deps,
        args=args,
        repo_root=repo_root,
        paths=paths,
        report=report,
    )
    if reviewer_supervisor_auto_start is not None:
        report["reviewer_supervisor_auto_start"] = reviewer_supervisor_auto_start
        if bool(reviewer_supervisor_auto_start.get("started")):
            report, exit_code = deps.run_status_action_fn(
                args=args,
                repo_root=repo_root,
                paths=paths,
            )
            report["reviewer_supervisor_auto_start"] = reviewer_supervisor_auto_start
    reviewer_wake = maybe_wake_waiting_reviewer_conductor(
        args=args,
        repo_root=repo_root,
        paths=paths,
        report=report,
        operator_interaction_mode=deps.operator_interaction_mode,
    )
    if reviewer_wake is not None:
        report["reviewer_wake"] = reviewer_wake
        if bool(reviewer_wake.get("woke")):
            report, exit_code = deps.run_status_action_fn(
                args=args,
                repo_root=repo_root,
                paths=paths,
            )
            if reviewer_supervisor_auto_start is not None:
                report["reviewer_supervisor_auto_start"] = reviewer_supervisor_auto_start
            report["reviewer_wake"] = reviewer_wake
    review_range = compute_review_range(
        repo_root=repo_root,
        bridge_path=bridge_path,
    )
    if review_range is not None:
        report["review_range"] = review_range
    if ensure_result.state_write is not None:
        report["reviewer_state_write"] = deps.reviewer_state_write_to_dict_fn(
            ensure_result.state_write
        )
    report["ensure_refreshed"] = ensure_result.refreshed
    if report.get("reviewer_worker") is None:
        deps.attach_reviewer_worker_fn(
            report,
            repo_root=repo_root,
            bridge_path=bridge_path,
        )
    if isinstance(status_dir, Path):
        report["publisher"] = deps.read_publisher_state_fn(status_dir)
        write_monitor_snapshot_fn = deps.write_monitor_snapshot_fn
        if write_monitor_snapshot_fn is not None:
            try:
                report["monitor_snapshot"] = write_monitor_snapshot_fn(
                    repo_root=repo_root,
                    review_status_dir=status_dir,
                    mode="remote_phone",
                    agent="operator",
                )
            except (OSError, ValueError) as exc:
                report["monitor_snapshot_error"] = str(exc)
    report["reviewer_heartbeat_suppressed"] = ensure_result.suppressed
    if deps.operator_interaction_mode:
        report["operator_interaction_mode"] = deps.operator_interaction_mode
    return FollowLoopTick(
        report=report,
        exit_code=exit_code,
        reviewer_mode=ensure_result.reviewer_mode,
        progress_token=progress_token,
    )


def _manual_stop_recovery_allowed(report: dict[str, object]) -> bool:
    """Lazy import to break circular follow_controller ↔ commands/review_channel."""
    from ..commands.review_channel._supervisor_restart_policy import (
        manual_stop_recovery_allowed,
    )
    return manual_stop_recovery_allowed(report)


def _maybe_restart_reviewer_supervisor(
    *,
    deps: EnsureFollowDeps,
    args,
    repo_root: Path,
    paths: dict[str, object],
    report: dict[str, object],
) -> dict[str, object] | None:
    restart_fn = deps.ensure_reviewer_supervisor_running_fn
    if restart_fn is None:
        return None
    bridge_liveness = report.get("bridge_liveness")
    if not isinstance(bridge_liveness, dict):
        return None
    reviewer_supervisor = report.get("reviewer_supervisor")
    if not isinstance(reviewer_supervisor, dict):
        return None
    reviewer_mode = str(bridge_liveness.get("reviewer_mode") or "")
    if not reviewer_mode_is_active(reviewer_mode):
        return None
    if bool(reviewer_supervisor.get("running")):
        return None
    return restart_fn(
        args=args,
        repo_root=repo_root,
        paths=paths,
        allow_follow=True,
        allow_manual_stop_recovery=_manual_stop_recovery_allowed(report),
    )


def maybe_wake_waiting_reviewer_conductor(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
    report: dict[str, object],
    operator_interaction_mode: str,
    deps: ReviewerWakeDeps | None = None,
) -> dict[str, object] | None:
    """Record reviewer packet attention without launching a conductor."""

    packet, immediate_report = _resolve_reviewer_wake_target(
        report=report,
        operator_interaction_mode=operator_interaction_mode,
    )
    if immediate_report is not None or packet is None:
        return immediate_report
    report = wake_report(
        packet=packet,
        attempted=False,
        woke=False,
        reason="packet_delivery_records_typed_attention_only",
        target_agent="codex",
        extras=WakeReceiptExtras(
            target_role=str(packet.get("target_role") or "").strip(),
            target_session_id=str(packet.get("target_session_id") or "").strip(),
            wake_method="none",
            visible_session_woke=False,
            warnings=(
                "Packet attention does not launch or replace the reviewer "
                "conductor; scheduler/runtime controllers own session starts "
                "after explicit task boundaries.",
            ),
        ),
    )
    report["attention_recorded"] = True
    return report


def maybe_wake_waiting_agent_conductor(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
    report: dict[str, object],
    operator_interaction_mode: str,
    target_agent: str,
    packet: dict[str, object],
    deps: ReviewerWakeDeps | None = None,
) -> dict[str, object] | None:
    """Record provider packet attention for a typed packet target.

    Thin shim — dispatch logic lives in `agent_wake_dispatch` so the
    multi-mode resolution can grow independently of the follow loop.
    """
    from .agent_wake_dispatch import (
        WakeRoutingContext,
        maybe_wake_waiting_agent_conductor as _dispatch,
    )

    return _dispatch(
        routing=WakeRoutingContext(
            args=args,
            repo_root=repo_root,
            paths=paths,
            report=report,
            operator_interaction_mode=operator_interaction_mode,
        ),
        target_agent=target_agent,
        packet=packet,
        maybe_wake_reviewer_fn=maybe_wake_waiting_reviewer_conductor,
        deps=deps,
    )
