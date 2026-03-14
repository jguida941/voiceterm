"""Bridge-action execution for `devctl review-channel`."""

from __future__ import annotations

from pathlib import Path

from ..review_channel.core import (
    detect_active_session_conflicts,
    summarize_active_session_conflicts,
)
from ..review_channel.handoff import BRIDGE_LIVENESS_KEYS
from ..review_channel.launch import (
    build_launch_sessions,
    launch_terminal_sessions,
    list_terminal_profiles,
    resolve_cli_path,
)
from ..review_channel.state import refresh_status_snapshot
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


def _render_bridge_md(report: dict) -> str:
    return render_bridge_md(report, bridge_liveness_keys=BRIDGE_LIVENESS_KEYS)


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
    apply_bridge_scope_if_requested(
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
    status_snapshot = refresh_status_snapshot(
        repo_root=repo_root,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        output_root=status_dir,
        promotion_plan_path=promotion_plan_path,
        execution_mode=args.execution_mode,
        warnings=warnings,
        errors=[],
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
    launched, handoff_ack_required, handoff_ack_observed = launch_sessions_if_requested(
        args=args,
        sessions=sessions,
        bridge_path=bridge_path,
        handoff_bundle=handoff_bundle,
        terminal_profile_applied=terminal_profile_applied,
        launch_terminal_sessions_fn=launch_terminal_sessions,
    )
    if launched:
        post_session_lifecycle_event(
            action=args.action,
            context=BridgeLifecycleEventContext(
                repo_root=repo_root,
                review_channel_path=review_channel_path,
                artifact_paths=paths.get("artifact_paths"),
                sessions=sessions,
            ),
        )
        status_snapshot = refresh_status_snapshot(
            repo_root=repo_root,
            bridge_path=bridge_path,
            review_channel_path=review_channel_path,
            output_root=status_dir,
            promotion_plan_path=promotion_plan_path,
            execution_mode=args.execution_mode,
            warnings=status_snapshot.warnings,
            errors=[],
        )
    bridge_liveness = status_snapshot.bridge_liveness
    return build_bridge_success_report(
        args=args,
        bridge_liveness=bridge_liveness,
        attention=status_snapshot.attention,
        codex_lanes=codex_lanes,
        claude_lanes=claude_lanes,
        terminal_profile_applied=terminal_profile_applied,
        warnings=status_snapshot.warnings,
        sessions=sessions,
        handoff_bundle=handoff_bundle,
        projection_paths=status_snapshot.projection_paths,
        launched=launched,
        handoff_ack_required=handoff_ack_required,
        handoff_ack_observed=handoff_ack_observed,
        promotion=promotion,
        bridge_heartbeat_refresh=bridge_heartbeat_refresh,
        execution_mode_override=report_execution_mode,
    )
