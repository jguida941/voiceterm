"""Bridge-action support helpers for `devctl review-channel`."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from ..review_channel.core import (
    AUTO_DARK_TERMINAL_PROFILES,
    DEFAULT_TERMINAL_PROFILE,
    build_bridge_guard_report,
    ensure_launcher_prereqs,
    filter_provider_lanes,
    summarize_bridge_guard_failures,
)
from ..review_channel.bridge_validation import validate_launch_bridge_state
from ..review_channel.bridge_runtime_state import (
    BridgeStateContext,
    BridgeStateResult,
)
from ..review_channel.handoff import (
    bridge_liveness_to_dict,
    extract_bridge_snapshot,
    summarize_bridge_liveness,
    wait_for_codex_poll_refresh,
    wait_for_rollover_ack,
    write_handoff_bundle,
)
from ..review_channel.heartbeat import (
    compute_non_audit_worktree_hash,
    refresh_bridge_heartbeat,
)
from ..review_channel.launch import launch_terminal_sessions
from ..review_channel.plan_resolution import resolve_promotion_plan_path
from ..review_channel.promotion import (
    DEFAULT_PROMOTION_PLAN_REL,
    resolve_scope_plan_path,
    scope_bridge_instruction,
)
from ..review_channel.reviewer_state_support import (
    current_instruction_revision_from_bridge_text,
)


def bridge_launch_state(
    *,
    args,
    context: BridgeStateContext,
    bridge_actions: set[str],
    build_bridge_guard_report_fn: Callable[..., dict[str, object]] | None = None,
) -> BridgeStateResult:
    """Parse lanes + liveness and validate the bridge guard for launch actions."""
    if build_bridge_guard_report_fn is None:
        build_bridge_guard_report_fn = build_bridge_guard_report
    _, lanes = ensure_launcher_prereqs(
        review_channel_path=context.review_channel_path,
        bridge_path=context.bridge_path,
        execution_mode=args.execution_mode,
    )
    bridge_refresh = None
    reviewer_state_write = None
    refreshable_actions = set(bridge_actions) | {"status"}
    allow_status_refresh = args.action != "status" or not getattr(args, "dry_run", False)
    if (
        context.bridge_path.exists()
        and args.action in refreshable_actions
        and allow_status_refresh
        and getattr(
            args,
            "refresh_bridge_heartbeat_if_stale",
            False,
        )
    ):
        stale_errors = stale_bridge_launch_errors(
            repo_root=context.repo_root,
            review_channel_path=context.review_channel_path,
            bridge_path=context.bridge_path,
        )
        if stale_errors:
            bridge_refresh = refresh_bridge_heartbeat(
                repo_root=context.repo_root,
                bridge_path=context.bridge_path,
                reason=f"devctl review-channel {args.action}",
            )
    if context.bridge_path.exists():
        bridge_snapshot = extract_bridge_snapshot(
            context.bridge_path.read_text(encoding="utf-8")
        )
    else:
        from ..review_channel.handoff import BridgeSnapshot
        bridge_snapshot = BridgeSnapshot(metadata={}, sections={})
    bridge_rel = str(context.bridge_path.relative_to(context.repo_root))
    try:
        current_hash = compute_non_audit_worktree_hash(
            repo_root=context.repo_root, excluded_rel_paths=(bridge_rel,)
        )
    except (ValueError, OSError):
        current_hash = None
    bridge_liveness_state = summarize_bridge_liveness(
        bridge_snapshot, current_worktree_hash=current_hash
    )
    if args.action in bridge_actions and context.bridge_path.exists():
        bridge_guard_report = build_bridge_guard_report_fn(
            repo_root=context.repo_root,
            review_channel_path=context.review_channel_path,
            bridge_path=context.bridge_path,
        )
        if not bridge_guard_report.get("ok", False):
            raise ValueError(
                "Fresh conductor bootstrap requires a green review-channel "
                "bridge guard before launch: " + summarize_bridge_guard_failures(bridge_guard_report)
            )
        launch_state_errors = validate_launch_bridge_state(
            bridge_snapshot,
            liveness=bridge_liveness_state,
        )
        if launch_state_errors:
            raise ValueError(
                "Fresh conductor bootstrap requires a live bridge "
                "contract before launch: " + "; ".join(launch_state_errors)
            )
    bridge_liveness = bridge_liveness_to_dict(bridge_liveness_state)
    codex_lanes = filter_provider_lanes(lanes, provider="codex")
    claude_lanes = filter_provider_lanes(lanes, provider="claude")
    cursor_lanes = filter_provider_lanes(lanes, provider="cursor")
    return BridgeStateResult(
        lanes=lanes,
        bridge_liveness=bridge_liveness,
        bridge_liveness_state=bridge_liveness_state,
        codex_lanes=codex_lanes,
        claude_lanes=claude_lanes,
        cursor_lanes=cursor_lanes,
        bridge_heartbeat_refresh=bridge_refresh,
        reviewer_state_write=reviewer_state_write,
    )


def resolve_launch_promotion_plan_path(
    *,
    repo_root: Path,
    bridge_path: Path,
    promotion_plan_path: Path | None,
    action: str,
) -> Path:
    """Resolve the launch-time promotion plan, with a default fallback for non-promote actions."""
    explicit_plan_path = promotion_plan_path if isinstance(promotion_plan_path, Path) else None
    plan_resolution = resolve_promotion_plan_path(
        repo_root=repo_root,
        bridge_path=bridge_path,
        explicit_plan_path=explicit_plan_path,
    )
    resolved_path = plan_resolution.path
    if resolved_path is None and action != "promote":
        return (repo_root / DEFAULT_PROMOTION_PLAN_REL).resolve()
    if action == "promote" and resolved_path is None:
        raise ValueError(
            "scope_missing: unable to resolve promotion plan path for promote action. "
            f"{plan_resolution.detail or 'Provide --promotion-plan or set bridge/tracker scope.'}"
        )
    assert resolved_path is not None
    return resolved_path


def apply_scope_if_requested(*, args, repo_root: Path, bridge_path: Path) -> object | None:
    """Rewrite the bridge instruction from ``--scope`` before launch.

    Returns the :class:`PromotionCandidate` when scope was applied, or
    ``None`` when no scope was requested.
    """
    scope_value = getattr(args, "scope", None)
    if not scope_value:
        return None
    if args.action != "launch":
        raise ValueError("--scope is only supported with --action launch.")
    scope_plan_path = resolve_scope_plan_path(
        repo_root=repo_root,
        scope_value=scope_value,
    )
    expected_instruction_revision = getattr(
        args,
        "expected_instruction_revision",
        None,
    )
    if not expected_instruction_revision and bridge_path.exists():
        expected_instruction_revision = current_instruction_revision_from_bridge_text(
            bridge_path.read_text(encoding="utf-8")
        )
    return scope_bridge_instruction(
        repo_root=repo_root,
        bridge_path=bridge_path,
        scope_plan_path=scope_plan_path,
        expected_instruction_revision=expected_instruction_revision,
    )


def stale_bridge_launch_errors(
    *,
    repo_root: Path,
    review_channel_path: Path,
    bridge_path: Path,
    build_bridge_guard_report_fn: Callable[..., dict[str, object]] | None = None,
) -> list[str]:
    """Return refreshable metadata errors when the bridge guard fails on stale heartbeat."""
    if build_bridge_guard_report_fn is None:
        build_bridge_guard_report_fn = build_bridge_guard_report
    bridge_guard_report = build_bridge_guard_report_fn(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        bridge_path=bridge_path,
    )
    bridge = bridge_guard_report.get("bridge")
    review_channel = bridge_guard_report.get("review_channel")
    if not isinstance(bridge, dict) or not isinstance(review_channel, dict):
        return []
    if review_channel.get("error") or review_channel.get("missing_markers"):
        return []
    if bridge.get("error") or bridge.get("missing_h2") or bridge.get("missing_markers"):
        return []
    state_errors = bridge.get("state_errors")
    if isinstance(state_errors, list) and state_errors:
        return []
    bridge_snapshot = extract_bridge_snapshot(bridge_path.read_text(encoding="utf-8"))
    launch_errors = validate_launch_bridge_state(
        bridge_snapshot,
        liveness=summarize_bridge_liveness(bridge_snapshot),
    )
    return [str(error).strip() for error in launch_errors if _is_refreshable_metadata_error(str(error))]


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
            repo_root=repo_root, excluded_rel_paths=(rollover_bridge_rel,)
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
        lane_assignments=[
            {
                "agent_id": lane.agent_id,
                "provider": lane.provider,
                "lane": lane.lane,
                "worktree": lane.worktree,
                "branch": lane.branch,
                "mp_scope": lane.mp_scope,
            }
            for lane in lanes
        ],
        current_worktree_hash=rollover_hash,
    )
    return handoff_bundle, [
        "Planned rollover created a repo-visible handoff bundle. "
        "Fresh sessions should acknowledge it before the old sessions exit."
    ]


def launch_sessions_if_requested(
    *,
    args,
    sessions: list[dict[str, object]],
    bridge_path: Path,
    handoff_bundle,
    terminal_profile_applied: str | None,
    launch_terminal_sessions_fn: Callable[..., None] | None = None,
) -> tuple[bool, bool, dict[str, bool] | None]:
    """Open Terminal.app windows and optionally wait for rollover ACK."""
    if launch_terminal_sessions_fn is None:
        launch_terminal_sessions_fn = launch_terminal_sessions
    launched = False
    handoff_ack_required = False
    handoff_ack_observed = None
    prelaunch_snapshot = extract_bridge_snapshot(
        bridge_path.read_text(encoding="utf-8")
    )
    prelaunch_poll_utc = prelaunch_snapshot.metadata.get("last_codex_poll_utc")
    prelaunch_poll_status = prelaunch_snapshot.sections.get("Poll Status", "")
    if args.action in {"launch", "rollover"} and args.terminal == "terminal-app" and not args.dry_run:
        launch_terminal_sessions_fn(
            sessions,
            terminal_profile=terminal_profile_applied,
            default_terminal_profile=DEFAULT_TERMINAL_PROFILE,
            auto_dark_terminal_profiles=AUTO_DARK_TERMINAL_PROFILES,
        )
        launched = True
        if args.action == "launch" and args.await_ack_seconds > 0:
            launch_poll = wait_for_codex_poll_refresh(
                bridge_path=bridge_path,
                previous_poll_utc=prelaunch_poll_utc,
                previous_poll_status=prelaunch_poll_status,
                timeout_seconds=args.await_ack_seconds,
            )
            if not bool(launch_poll.get("observed")):
                latest_poll_utc = str(
                    launch_poll.get("last_codex_poll_utc") or "missing"
                )
                previous_poll_display = prelaunch_poll_utc or "missing"
                poll_status_detail = []
                if bool(launch_poll.get("poll_advanced")):
                    poll_status_detail.append(
                        f"`Last Codex poll` advanced to {latest_poll_utc}"
                    )
                else:
                    poll_status_detail.append(
                        f"`Last Codex poll` stayed at {latest_poll_utc}"
                    )
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
                raise ValueError(
                    "Live review-channel launch did not produce a fresh Codex "
                    f"reviewer turn within {args.await_ack_seconds}s. "
                    + "; ".join(poll_status_detail)
                    + f" (pre-launch poll {previous_poll_display})."
                )
        if args.action == "rollover" and handoff_bundle is not None and args.await_ack_seconds > 0:
            handoff_ack_required = True
            handoff_ack_observed = wait_for_rollover_ack(
                bridge_path=bridge_path,
                rollover_id=handoff_bundle.rollover_id,
                timeout_seconds=args.await_ack_seconds,
            )
    return launched, handoff_ack_required, handoff_ack_observed


def _is_refreshable_metadata_error(error: str) -> bool:
    refreshable_tokens = (
        "Invalid `Last Codex poll` timestamp",
        "`Last Codex poll` is stale",
        "`Last Codex poll` is in the future",
        "Invalid `Last Codex poll (Local America/New_York)` value",
        "Invalid `Last non-audit worktree hash`",
    )
    return any(token in error for token in refreshable_tokens)
