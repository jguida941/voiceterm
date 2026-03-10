"""Bridge-action execution for `devctl review-channel`."""

from __future__ import annotations

from pathlib import Path

from ..approval_mode import normalize_approval_mode
from ..common import display_path
from ..review_channel.core import (
    DEFAULT_TERMINAL_PROFILE,
    REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE,
    detect_active_session_conflicts,
    summarize_active_session_conflicts,
)
from ..review_channel.handoff import BRIDGE_LIVENESS_KEYS, handoff_bundle_to_dict
from ..review_channel.events import post_packet
from ..review_channel.event_store import ReviewChannelArtifactPaths, event_state_exists
from ..review_channel.launch import (
    build_launch_sessions,
    launch_terminal_sessions,
    resolve_cli_path,
)
from ..review_channel.promotion import DEFAULT_PROMOTION_PLAN_REL, promote_bridge_instruction
from ..review_channel.state import refresh_status_snapshot
from .review_channel_bridge_render import (
    build_bridge_success_report,
    render_bridge_md,
)
from .review_channel_bridge_support import (
    build_bridge_guard_report,
    bridge_launch_state,
    list_terminal_profiles,
    launch_sessions_if_requested,
    prepare_rollover_bundle,
    resolve_terminal_launch_state,
)

BRIDGE_ACTIONS = {"launch", "rollover"}


def _render_bridge_md(report: dict) -> str:
    """Render a markdown summary for bridge-backed review-channel actions."""
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

    _validate_live_launch_conflicts(args=args, status_dir=status_dir)
    lanes, bridge_liveness, codex_lanes, claude_lanes, cursor_lanes, bridge_heartbeat_refresh = (
        _load_bridge_runtime_state(
            args=args,
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            bridge_path=bridge_path,
        )
    )
    promotion, terminal_profile_applied, warnings = _resolve_promotion_and_terminal_state(
        args=args,
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        bridge_path=bridge_path,
        promotion_plan_path=promotion_plan_path,
        codex_lanes=codex_lanes,
        claude_lanes=claude_lanes,
        cursor_lanes=cursor_lanes,
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
    sessions = _build_sessions(
        args=args,
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        bridge_path=bridge_path,
        bridge_liveness=bridge_liveness,
        codex_lanes=codex_lanes,
        claude_lanes=claude_lanes,
        cursor_lanes=cursor_lanes,
        handoff_bundle=handoff_bundle,
        promotion_plan_path=promotion_plan_path,
        script_dir=script_dir,
        status_dir=status_dir,
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
        _post_session_lifecycle_event(
            action=args.action,
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=paths.get("artifact_paths"),
            sessions=sessions,
        )
    return build_bridge_success_report(
        args=args,
        bridge_liveness=bridge_liveness,
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


def _validate_live_launch_conflicts(*, args, status_dir: Path) -> None:
    if (
        args.action == "launch"
        and args.terminal == "terminal-app"
        and not args.dry_run
    ):
        active_session_conflicts = detect_active_session_conflicts(
            session_output_root=status_dir,
        )
        if active_session_conflicts:
            raise ValueError(
                "Live review-channel launch refused because existing session "
                "artifacts still look active. Close the current conductor "
                "windows or wait for the session traces to go stale before "
                "launching again: "
                + summarize_active_session_conflicts(active_session_conflicts)
            )


def _load_bridge_runtime_state(
    *,
    args,
    repo_root: Path,
    review_channel_path: Path,
    bridge_path: Path,
) -> tuple[list, dict[str, object], list, list, list, object]:
    (
        lanes,
        bridge_liveness,
        _liveness_state,
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
    return lanes, bridge_liveness, codex_lanes, claude_lanes, cursor_lanes, bridge_heartbeat_refresh


def _resolve_promotion_and_terminal_state(
    *,
    args,
    repo_root: Path,
    review_channel_path: Path,
    bridge_path: Path,
    promotion_plan_path: Path,
    codex_lanes: list,
    claude_lanes: list,
    cursor_lanes: list | None = None,
) -> tuple[object, str | None, list[str]]:
    promotion = None
    if args.action != "promote":
        terminal_profile_applied, warnings = resolve_terminal_launch_state(
            args,
            codex_lanes=codex_lanes,
            claude_lanes=claude_lanes,
            list_terminal_profiles_fn=list_terminal_profiles,
        )
        return promotion, terminal_profile_applied, warnings

    promotion = promote_bridge_instruction(
        repo_root=repo_root,
        bridge_path=bridge_path,
        promotion_plan_path=promotion_plan_path,
    )
    bridge_launch_state(
        args=args,
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        bridge_path=bridge_path,
        bridge_actions=BRIDGE_ACTIONS,
        build_bridge_guard_report_fn=build_bridge_guard_report,
    )
    return promotion, None, []


def _build_sessions(
    *,
    args,
    repo_root: Path,
    review_channel_path: Path,
    bridge_path: Path,
    bridge_liveness: dict[str, object],
    codex_lanes: list,
    claude_lanes: list,
    cursor_lanes: list | None = None,
    handoff_bundle,
    promotion_plan_path: Path,
    script_dir,
    status_dir: Path,
) -> list[dict[str, object]]:
    if args.action not in BRIDGE_ACTIONS:
        return []
    effective_cursor_lanes = cursor_lanes or []
    approval_mode = normalize_approval_mode(
        getattr(args, "approval_mode", None),
        dangerous=bool(args.dangerous),
    )
    return build_launch_sessions(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        bridge_path=bridge_path,
        codex_lanes=codex_lanes,
        claude_lanes=claude_lanes,
        codex_workers=min(args.codex_workers, len(codex_lanes)),
        claude_workers=min(args.claude_workers, len(claude_lanes)),
        cursor_lanes=effective_cursor_lanes,
        cursor_workers=min(
            getattr(args, "cursor_workers", len(effective_cursor_lanes)),
            len(effective_cursor_lanes),
        ),
        approval_mode=approval_mode,
        dangerous=bool(args.dangerous),
        rollover_threshold_pct=args.rollover_threshold_pct,
        await_ack_seconds=args.await_ack_seconds,
        default_terminal_profile=DEFAULT_TERMINAL_PROFILE,
        retirement_note=REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE,
        promotion_plan_rel=display_path(
            promotion_plan_path,
            repo_root=repo_root,
        ),
        bridge_liveness=bridge_liveness,
        handoff_bundle=handoff_bundle_to_dict(handoff_bundle),
        script_dir=script_dir if isinstance(script_dir, Path) else None,
        session_output_root=status_dir,
        resolve_cli_path_fn=resolve_cli_path,
    )


def _post_session_lifecycle_event(
    *,
    action: str,
    repo_root: Path,
    review_channel_path: Path,
    artifact_paths: ReviewChannelArtifactPaths | None,
    sessions: list[dict[str, object]],
) -> None:
    """Post a system_notice event when conductor sessions launch.

    Makes session lifecycle visible in the conversation panel and task
    board. Silently skipped when the event store is not initialized.
    """
    if artifact_paths is None or not event_state_exists(artifact_paths):
        return
    provider_names = [str(s.get("provider", "")).capitalize() for s in sessions]
    label = "rollover" if action == "rollover" else "launch"
    summary = f"Session {label}: {', '.join(provider_names)} conductors started"
    lane_counts = [
        f"{s.get('provider', '?')}: {s.get('lane_count', 0)} lanes"
        for s in sessions
    ]
    body = (
        f"The operator {label}ed {len(sessions)} conductor session(s). "
        f"Lane allocation: {'; '.join(lane_counts)}."
    )
    try:
        post_packet(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
            from_agent="system",
            to_agent="operator",
            kind="system_notice",
            summary=summary,
            body=body,
            evidence_refs=[],
            context_pack_refs=[],
            confidence=1.0,
            requested_action="review_only",
            policy_hint="review_only",
            approval_required=False,
            expires_in_minutes=60,
        )
    except (OSError, ValueError):
        pass
