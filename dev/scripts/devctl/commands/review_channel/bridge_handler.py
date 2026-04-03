"""Bridge-action execution for `devctl review-channel`."""

from __future__ import annotations

from functools import partial
from pathlib import Path

from ...review_channel.bridge_runtime_state import (
    BridgeStateContext,
    enforce_bridge_launch_attention,
)
from ...review_channel.core import (
    detect_active_session_conflicts,
    summarize_active_session_conflicts,
)
from ...review_channel.handoff import BRIDGE_LIVENESS_KEYS
from ...review_channel.launch import (
    build_launch_sessions,
    launch_terminal_sessions,
    list_terminal_profiles,
    resolve_cli_path,
)
from ...review_channel.session_probe import load_conductor_sessions
from ...review_channel.state import refresh_status_snapshot
from .bridge_action_support import (
    BridgeLifecycleEventContext,
    BridgePromotionContext,
    BridgeSessionContext,
    attach_service_identity,
    build_bridge_sessions,
    post_session_lifecycle_event,
    resolve_promotion_and_terminal_state,
    validate_live_launch_conflicts,
)
from .bridge_contexts import (
    BridgeReportContext,
    LaunchExecutionContext,
    LaunchRefreshContext,
)
from .bridge_launch_control import (
    LaunchSessionRequest,
    ensure_launch_runtime_daemons,
    launch_sessions_if_requested,
    observe_launch_state,
    prepare_rollover_bundle,
)
from ..review_channel_bridge_render import build_bridge_success_report, render_bridge_md
from .bridge_support import (
    apply_scope_if_requested as apply_bridge_scope_if_requested,
)
from .bridge_support import (
    bridge_launch_state,
    build_bridge_guard_report,
    resolve_launch_promotion_plan_path,
)

BRIDGE_ACTIONS = {"launch", "rollover", "promote"}
LAUNCH_GUARDED_ACTIONS = {"launch", "rollover"}


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


def _launch_and_refresh(
    *,
    args,
    context: LaunchRefreshContext,
    execution: LaunchExecutionContext,
) -> tuple[bool, bool, dict[str, bool] | None, "ReviewChannelStatusSnapshot"]:
    """Launch sessions when requested and refresh the status snapshot afterward."""
    runtime_warnings: list[str] = []
    if (
        args.action in {"launch", "rollover"}
        and args.terminal == "terminal-app"
        and not args.dry_run
    ):
        runtime_ok, runtime_warnings = ensure_launch_runtime_daemons(
            args=args,
            repo_root=context.repo_root,
            review_channel_path=context.review_channel_path,
            bridge_path=context.bridge_path,
            status_dir=context.status_dir,
            reviewer_mode=str(
                execution.status_snapshot.bridge_liveness.get("reviewer_mode", "")
            ),
        )
        if not runtime_ok:
            detail = " ".join(runtime_warnings).strip()
            suffix = f" {detail}" if detail else ""
            raise ValueError(
                "Live review-channel launch did not start the repo-owned "
                f"publisher runtime.{suffix}"
            )
    (
        launched,
        handoff_ack_required,
        handoff_ack_observed,
        cleanup_warnings,
    ) = launch_sessions_if_requested(
        LaunchSessionRequest(
            args=args,
            sessions=execution.sessions,
            bridge_path=context.bridge_path,
            handoff_bundle=execution.handoff_bundle,
            terminal_profile_applied=execution.terminal_profile_applied,
            launch_terminal_sessions_fn=launch_terminal_sessions,
            retired_sessions=tuple(execution.retired_sessions),
            observe_launch_state_fn=partial(
                observe_launch_state,
                args=args,
                context=context,
                warnings=execution.status_snapshot.warnings,
                refresh_snapshot_fn=_refresh_snapshot,
            ),
        )
    )
    if not launched:
        return (
            launched,
            handoff_ack_required,
            handoff_ack_observed,
            execution.status_snapshot,
        )
    post_session_lifecycle_event(
        action=args.action,
        context=BridgeLifecycleEventContext(
            repo_root=context.repo_root,
            review_channel_path=context.review_channel_path,
            artifact_paths=context.artifact_paths,
            sessions=execution.sessions,
        ),
    )
    refreshed_snapshot = _refresh_snapshot(
        args=args,
        context=context,
        warnings=[
            *execution.status_snapshot.warnings,
            *runtime_warnings,
            *cleanup_warnings,
        ],
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
        reviewer_state_write=context.reviewer_state_write,
        execution_mode_override=report_execution_mode,
    )
    attach_service_identity(
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
    promotion_plan_path = resolve_launch_promotion_plan_path(
        repo_root=repo_root,
        bridge_path=bridge_path,
        promotion_plan_path=promotion_plan_path,
        action=args.action,
    )

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
    bridge_state = bridge_launch_state(
        args=args,
        context=BridgeStateContext(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            bridge_path=bridge_path,
            status_dir=status_dir,
        ),
        bridge_actions=LAUNCH_GUARDED_ACTIONS,
        build_bridge_guard_report_fn=build_bridge_guard_report,
    )
    enforce_bridge_launch_attention(
        action=args.action,
        bridge_actions=LAUNCH_GUARDED_ACTIONS,
        bridge_liveness=bridge_state.bridge_liveness,
    )
    promotion, terminal_profile_applied, warnings = resolve_promotion_and_terminal_state(
        args=args,
        context=BridgePromotionContext(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            bridge_path=bridge_path,
            promotion_plan_path=promotion_plan_path,
            codex_lanes=bridge_state.codex_lanes,
            claude_lanes=bridge_state.claude_lanes,
        ),
        list_terminal_profiles_fn=list_terminal_profiles,
    )
    if promotion is None and scope_promotion is not None:
        promotion = scope_promotion
    warnings = [*list(extra_warnings or []), *warnings]
    if promotion_plan_path is None:
        warnings.append(
            "Scoped promotion plan unresolved; auto-promotion is disabled until bridge/tracker scope is set."
        )
    handoff_bundle, handoff_warnings = prepare_rollover_bundle(
        args=args,
        repo_root=repo_root,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        rollover_dir=rollover_dir,
        lanes=bridge_state.lanes,
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
    retired_sessions = ()
    if args.action == "rollover" and args.terminal == "terminal-app" and not args.dry_run:
        retired_sessions = load_conductor_sessions(session_output_root=status_dir)
    sessions = build_bridge_sessions(
        args=args,
        context=BridgeSessionContext(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            bridge_path=bridge_path,
            bridge_liveness=bridge_state.bridge_liveness,
            codex_lanes=bridge_state.codex_lanes,
            claude_lanes=bridge_state.claude_lanes,
            cursor_lanes=bridge_state.cursor_lanes,
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
        execution=LaunchExecutionContext(
            sessions=sessions,
            handoff_bundle=handoff_bundle,
            terminal_profile_applied=terminal_profile_applied,
            status_snapshot=status_snapshot,
            retired_sessions=tuple(retired_sessions),
        ),
    )
    return _build_bridge_report(
        args=args,
        context=BridgeReportContext(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            bridge_path=bridge_path,
            status_dir=status_dir,
            status_snapshot=status_snapshot,
            codex_lanes=bridge_state.codex_lanes,
            claude_lanes=bridge_state.claude_lanes,
            terminal_profile_applied=terminal_profile_applied,
            sessions=sessions,
            handoff_bundle=handoff_bundle,
            launched=launched,
            handoff_ack_required=handoff_ack_required,
            handoff_ack_observed=handoff_ack_observed,
            promotion=promotion,
            bridge_heartbeat_refresh=bridge_state.bridge_heartbeat_refresh,
            reviewer_state_write=bridge_state.reviewer_state_write,
        ),
        report_execution_mode=report_execution_mode,
    )
