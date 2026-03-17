"""Bridge-action execution for `devctl review-channel`."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..review_channel.attention import derive_bridge_attention
from ..review_channel.core import (
    detect_active_session_conflicts,
    summarize_active_session_conflicts,
)
from ..review_channel.handoff import BRIDGE_LIVENESS_KEYS
from ..review_channel.peer_liveness import STALE_PEER_RECOVERY
from ..review_channel.launch import (
    build_launch_sessions,
    launch_terminal_sessions,
    list_terminal_profiles,
    resolve_cli_path,
)
from ..review_channel.state import (
    build_attach_auth_policy,
    build_service_identity,
    refresh_status_snapshot,
)
from .review_channel_bridge_action_support import (
    BridgeLifecycleEventContext,
    BridgePromotionContext,
    BridgeSessionContext,
    build_bridge_sessions,
    post_session_lifecycle_event,
    resolve_promotion_and_terminal_state,
    validate_live_launch_conflicts,
)
from .review_channel_bridge_render import build_bridge_success_report, render_bridge_md
from .review_channel_bridge_support import (
    apply_scope_if_requested as apply_bridge_scope_if_requested,
)
from .review_channel_bridge_support import (
    bridge_launch_state,
    build_bridge_guard_report,
    launch_sessions_if_requested,
    prepare_rollover_bundle,
)

BRIDGE_ACTIONS = {"launch", "rollover"}


@dataclass(frozen=True)
class LaunchRefreshContext:
    """Grouped bridge-launch paths needed for post-launch refresh work."""

    repo_root: Path
    review_channel_path: Path
    bridge_path: Path
    status_dir: Path
    promotion_plan_path: Path
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


def _refresh_snapshot(
    *,
    args,
    context: LaunchRefreshContext,
    warnings: list[str],
) -> "ReviewChannelStatusSnapshot":
    """Refresh status projections with the current CLI overdue threshold."""
    return refresh_status_snapshot(
        repo_root=context.repo_root,
        bridge_path=context.bridge_path,
        review_channel_path=context.review_channel_path,
        output_root=context.status_dir,
        promotion_plan_path=context.promotion_plan_path,
        execution_mode=args.execution_mode,
        warnings=warnings,
        errors=[],
        reviewer_overdue_threshold_seconds=getattr(args, "reviewer_overdue_seconds", None),
    )


def _render_bridge_md(report: dict) -> str:
    return render_bridge_md(report, bridge_liveness_keys=BRIDGE_LIVENESS_KEYS)


def _attach_service_identity(
    report: dict[str, object],
    *,
    repo_root: Path,
    bridge_path: Path,
    review_channel_path: Path,
    status_dir: Path,
) -> None:
    """Attach the repo/worktree identity plus attach/auth policy to one report."""
    service_identity = build_service_identity(
        repo_root=repo_root,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        output_root=status_dir,
    )
    report["service_identity"] = service_identity
    report["attach_auth_policy"] = build_attach_auth_policy(
        service_identity=service_identity,
    )


def _launch_and_refresh(
    *,
    args,
    context: LaunchRefreshContext,
    sessions: list[dict[str, object]],
    handoff_bundle,
    terminal_profile_applied: str | None,
    status_snapshot,
) -> tuple[bool, bool, dict[str, bool] | None, "ReviewChannelStatusSnapshot"]:
    """Launch sessions when requested and refresh the status snapshot afterward."""
    launched, handoff_ack_required, handoff_ack_observed = launch_sessions_if_requested(
        args=args,
        sessions=sessions,
        bridge_path=context.bridge_path,
        handoff_bundle=handoff_bundle,
        terminal_profile_applied=terminal_profile_applied,
        launch_terminal_sessions_fn=launch_terminal_sessions,
    )
    if not launched:
        return launched, handoff_ack_required, handoff_ack_observed, status_snapshot
    post_session_lifecycle_event(
        action=args.action,
        context=BridgeLifecycleEventContext(
            repo_root=context.repo_root,
            review_channel_path=context.review_channel_path,
            artifact_paths=context.artifact_paths,
            sessions=sessions,
        ),
    )
    refreshed_snapshot = _refresh_snapshot(
        args=args,
        context=context,
        warnings=status_snapshot.warnings,
    )
    return launched, handoff_ack_required, handoff_ack_observed, refreshed_snapshot


def _build_bridge_report(
    *,
    args,
    context: BridgeReportContext,
    report_execution_mode: str | None,
) -> tuple[dict, int]:
    """Build one bridge-backed report and attach service identity."""
    report, exit_code = build_bridge_success_report(
        args=args,
        bridge_liveness=context.status_snapshot.bridge_liveness,
        attention=context.status_snapshot.attention,
        reviewer_worker=context.status_snapshot.reviewer_worker,
        codex_lanes=context.codex_lanes,
        claude_lanes=context.claude_lanes,
        terminal_profile_applied=context.terminal_profile_applied,
        warnings=context.status_snapshot.warnings,
        sessions=context.sessions,
        handoff_bundle=context.handoff_bundle,
        projection_paths=context.status_snapshot.projection_paths,
        launched=context.launched,
        handoff_ack_required=context.handoff_ack_required,
        handoff_ack_observed=context.handoff_ack_observed,
        promotion=context.promotion,
        bridge_heartbeat_refresh=context.bridge_heartbeat_refresh,
        execution_mode_override=report_execution_mode,
    )
    _attach_service_identity(
        repo_root=context.repo_root,
        report=report,
        bridge_path=context.bridge_path,
        review_channel_path=context.review_channel_path,
        status_dir=context.status_dir,
    )
    return report, exit_code


def _run_bridge_action(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
    extra_warnings: list[str] | None = None,
    report_execution_mode: str | None = None,
) -> tuple[dict, int]:
    """Execute a bridge-backed review-channel action."""
    review_channel_path = paths["review_channel_path"]
    bridge_path = paths["bridge_path"]
    rollover_dir = paths["rollover_dir"]
    status_dir = paths["status_dir"]
    promotion_plan_path = paths["promotion_plan_path"]
    script_dir = paths["script_dir"]
    assert isinstance(review_channel_path, Path)
    assert isinstance(bridge_path, Path)
    assert isinstance(rollover_dir, Path)
    assert isinstance(status_dir, Path)
    assert isinstance(promotion_plan_path, Path)

    validate_live_launch_conflicts(
        args=args,
        status_dir=status_dir,
        detect_active_session_conflicts_fn=detect_active_session_conflicts,
        summarize_active_session_conflicts_fn=summarize_active_session_conflicts,
    )
    scope_promotion = apply_bridge_scope_if_requested(
        args=args,
        repo_root=repo_root,
        bridge_path=bridge_path,
    )
    (
        lanes,
        bridge_liveness,
        _bridge_liveness_state,
        codex_lanes,
        claude_lanes,
        cursor_lanes,
        bridge_heartbeat_refresh,
    ) = bridge_launch_state(
        args=args,
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        bridge_path=bridge_path,
        bridge_actions=BRIDGE_ACTIONS,
        build_bridge_guard_report_fn=build_bridge_guard_report,
    )
    if args.action in BRIDGE_ACTIONS:
        attention = derive_bridge_attention(bridge_liveness)
        attention_status = str(attention.get("status", ""))
        recovery_entry = STALE_PEER_RECOVERY.get(attention_status, {})
        if str(recovery_entry.get("guard_behavior")) == "block_launch":
            raise ValueError(
                f"Peer-liveness guard blocks launch: {attention.get('summary', attention_status)}. "
                f"Recovery: {attention.get('recommended_action', 'inspect bridge state')}."
            )
    promotion, terminal_profile_applied, warnings = resolve_promotion_and_terminal_state(
        args=args,
        context=BridgePromotionContext(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            bridge_path=bridge_path,
            promotion_plan_path=promotion_plan_path,
            codex_lanes=codex_lanes,
            claude_lanes=claude_lanes,
        ),
        list_terminal_profiles_fn=list_terminal_profiles,
    )
    if promotion is None and scope_promotion is not None:
        promotion = scope_promotion
    warnings = [*list(extra_warnings or []), *warnings]
    handoff_bundle, handoff_warnings = prepare_rollover_bundle(
        args=args,
        repo_root=repo_root,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        rollover_dir=rollover_dir,
        lanes=lanes,
    )
    warnings.extend(handoff_warnings)
    launch_context = LaunchRefreshContext(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        bridge_path=bridge_path,
        status_dir=status_dir,
        promotion_plan_path=promotion_plan_path,
        artifact_paths=paths.get("artifact_paths"),
    )
    status_snapshot = _refresh_snapshot(
        args=args,
        context=launch_context,
        warnings=warnings,
    )
    sessions = build_bridge_sessions(
        args=args,
        context=BridgeSessionContext(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            bridge_path=bridge_path,
            bridge_liveness=bridge_liveness,
            codex_lanes=codex_lanes,
            claude_lanes=claude_lanes,
            cursor_lanes=cursor_lanes,
            handoff_bundle=handoff_bundle,
            promotion_plan_path=promotion_plan_path,
            script_dir=script_dir if isinstance(script_dir, Path) else None,
            status_dir=status_dir,
        ),
        resolve_cli_path_fn=resolve_cli_path,
        build_launch_sessions_fn=build_launch_sessions,
    )
    launched, handoff_ack_required, handoff_ack_observed, status_snapshot = _launch_and_refresh(
        args=args,
        context=launch_context,
        sessions=sessions,
        handoff_bundle=handoff_bundle,
        terminal_profile_applied=terminal_profile_applied,
        status_snapshot=status_snapshot,
    )
    return _build_bridge_report(
        args=args,
        context=BridgeReportContext(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            bridge_path=bridge_path,
            status_dir=status_dir,
            status_snapshot=status_snapshot,
            codex_lanes=codex_lanes,
            claude_lanes=claude_lanes,
            terminal_profile_applied=terminal_profile_applied,
            sessions=sessions,
            handoff_bundle=handoff_bundle,
            launched=launched,
            handoff_ack_required=handoff_ack_required,
            handoff_ack_observed=handoff_ack_observed,
            promotion=promotion,
            bridge_heartbeat_refresh=bridge_heartbeat_refresh,
        ),
        report_execution_mode=report_execution_mode,
    )
