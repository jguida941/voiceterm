"""Reviewer follow-loop: promotion, recovery, rollover, and follow-packet orchestration."""

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
from .current_session_projection import bridge_implementer_state_hash
from .current_session_projection import build_bridge_current_session
from .handoff import extract_bridge_snapshot, summarize_bridge_liveness
from .heartbeat import bridge_excluded_rel_paths, compute_non_audit_worktree_hash
from .lifecycle_state import (
    ReviewerSupervisorHeartbeat,
)
from .plan_resolution import resolve_promotion_plan_path
from .promotion import (
    derive_promotion_candidate,
    promote_bridge_instruction,
    validate_promotion_ready,
)
from .reviewer_follow_actions import apply_auto_action, refresh_follow_report
from .reviewer_follow_guard import (
    ReviewerFollowPacketRequest,
    ReviewerFollowTriggerState,
    maybe_queue_reviewer_follow_packet,
    maybe_refresh_automation_reviewer_heartbeat,
)
from .reviewer_head_tracking import compute_review_range
from .reviewer_follow_recovery import (
    ReviewerFollowRecoveryInput,
    ReviewerFollowRecoveryState,
    ReviewerFollowRolloverInput,
    ReviewerFollowRolloverState,
    maybe_auto_relaunch_review_loop,
    maybe_auto_recover_stale_implementer,
    maybe_auto_trigger_rollover_on_stale_codex,
)


@dataclass(frozen=True)
class ReviewerFollowDeps:
    ensure_reviewer_heartbeat_fn: Callable[..., object]
    build_reviewer_state_report_fn: Callable[..., tuple[dict, int]]
    reviewer_state_write_to_dict_fn: Callable[..., dict[str, object] | None]
    run_recovery_action_fn: Callable[..., tuple[dict, int]] | None
    run_bridge_action_fn: Callable[..., tuple[dict, int]] | None
    emit_follow_ndjson_frame_fn: Callable[..., int]
    reset_follow_output_fn: Callable[..., None]
    build_follow_completion_report_fn: Callable[..., dict[str, object]]
    build_follow_output_error_report_fn: Callable[..., dict[str, object]]
    write_reviewer_supervisor_heartbeat_fn: Callable[..., Path]
    utc_timestamp_fn: Callable[[], str]
    sleep_fn: Callable[[float], None]


@dataclass
class ReviewerFollowLoopState:
    """Mutable reviewer-follow state carried across loop iterations."""

    recovery: ReviewerFollowRecoveryState
    rollover: ReviewerFollowRolloverState
    trigger: ReviewerFollowTriggerState


def run_reviewer_follow_action(*, args, repo_root: Path, paths: dict[str, object], deps: ReviewerFollowDeps) -> tuple[dict, int]:
    """Poll reviewer-worker state on cadence and emit NDJSON frames."""
    loop_state = ReviewerFollowLoopState(
        recovery=ReviewerFollowRecoveryState(),
        rollover=ReviewerFollowRolloverState(),
        trigger=ReviewerFollowTriggerState(),
    )
    return run_configured_follow_action(
        args=args, repo_root=repo_root, paths=paths, deps_source=deps,
        action=_reviewer_follow_action_shape(deps),
        build_tick_fn=lambda: _build_reviewer_follow_tick(
            args=args,
            repo_root=repo_root,
            paths=paths,
            deps=deps,
            loop_state=loop_state,
        ),
    )


def _reviewer_follow_action_shape(
    deps: ReviewerFollowDeps,
) -> FollowActionShape:
    return FollowActionShape(
        daemon_kind="reviewer_supervisor",
        completion_action="reviewer-heartbeat",
        output_error_action="reviewer-heartbeat",
        write_heartbeat_fn=deps.write_reviewer_supervisor_heartbeat_fn,
        heartbeat_factory=ReviewerSupervisorHeartbeat,
    )


def _build_reviewer_follow_tick(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
    deps: ReviewerFollowDeps,
    loop_state: ReviewerFollowLoopState,
) -> FollowLoopTick:
    bridge_path = paths["bridge_path"]
    assert isinstance(bridge_path, Path)
    progress_token = build_claude_progress_token(repo_root=repo_root, bridge_path=bridge_path)
    ensure_result = maybe_refresh_automation_reviewer_heartbeat(
        repo_root=repo_root,
        bridge_path=bridge_path,
        reason="reviewer-follow",
        requested_reviewer_mode=getattr(args, "reviewer_mode", None),
        ensure_reviewer_heartbeat_fn=deps.ensure_reviewer_heartbeat_fn,
    )
    report, frame_exit_code = refresh_follow_report(
        args=args,
        repo_root=repo_root,
        paths=paths,
        bridge_path=bridge_path,
        build_reviewer_state_report_fn=deps.build_reviewer_state_report_fn,
    )
    review_range = compute_review_range(repo_root=repo_root, bridge_path=bridge_path)
    if review_range is not None:
        report["review_range"] = review_range
    auto_promotion = _maybe_auto_promote(
        args=args,
        repo_root=repo_root,
        paths=paths,
        bridge_path=bridge_path,
    )
    report, frame_exit_code, progress_token = apply_auto_action(
        action_key="auto_promotion",
        success_key="promoted",
        action_payload=auto_promotion,
        report=report,
        frame_exit_code=frame_exit_code,
        progress_token=progress_token,
        args=args,
        repo_root=repo_root,
        paths=paths,
        bridge_path=bridge_path,
        build_reviewer_state_report_fn=deps.build_reviewer_state_report_fn,
    )
    auto_recovery = maybe_auto_recover_stale_implementer(
        recovery_fn=deps.run_recovery_action_fn,
        recovery_input=ReviewerFollowRecoveryInput(
            args=args,
            repo_root=repo_root,
            paths=paths,
            report=report,
            progress_token=progress_token,
            recovery_state=loop_state.recovery,
        ),
    )
    report, frame_exit_code, progress_token = apply_auto_action(
        action_key="auto_recovery",
        success_key="recovered",
        action_payload=auto_recovery,
        report=report,
        frame_exit_code=frame_exit_code,
        progress_token=progress_token,
        args=args,
        repo_root=repo_root,
        paths=paths,
        bridge_path=bridge_path,
        build_reviewer_state_report_fn=deps.build_reviewer_state_report_fn,
    )
    auto_relaunch = maybe_auto_relaunch_review_loop(
        bridge_action_fn=deps.run_bridge_action_fn,
        rollover_input=ReviewerFollowRolloverInput(
            args=args,
            repo_root=repo_root,
            paths=paths,
            report=report,
            rollover_state=loop_state.rollover,
        ),
    )
    report, frame_exit_code, progress_token = apply_auto_action(
        action_key="auto_relaunch",
        success_key="launched",
        action_payload=auto_relaunch,
        report=report,
        frame_exit_code=frame_exit_code,
        progress_token=progress_token,
        args=args,
        repo_root=repo_root,
        paths=paths,
        bridge_path=bridge_path,
        build_reviewer_state_report_fn=deps.build_reviewer_state_report_fn,
    )
    auto_rollover = None
    if auto_relaunch is None:
        auto_rollover = maybe_auto_trigger_rollover_on_stale_codex(
            bridge_action_fn=deps.run_bridge_action_fn,
            rollover_input=ReviewerFollowRolloverInput(
                args=args,
                repo_root=repo_root,
                paths=paths,
                report=report,
                rollover_state=loop_state.rollover,
            ),
        )
    report, frame_exit_code, progress_token = apply_auto_action(
        action_key="auto_rollover",
        success_key="rolled_over",
        action_payload=auto_rollover,
        report=report,
        frame_exit_code=frame_exit_code,
        progress_token=progress_token,
        args=args,
        repo_root=repo_root,
        paths=paths,
        bridge_path=bridge_path,
        build_reviewer_state_report_fn=deps.build_reviewer_state_report_fn,
    )
    review_trigger = maybe_queue_reviewer_follow_packet(
        request=ReviewerFollowPacketRequest(
            args=args,
            repo_root=repo_root,
            paths=paths,
            report=report,
        ),
        trigger_state=loop_state.trigger,
    )
    if review_trigger is not None:
        report["review_trigger"] = review_trigger
    report["reviewer_heartbeat_refreshed"] = ensure_result.refreshed
    report["reviewer_heartbeat_suppressed"] = ensure_result.suppressed
    _append_follow_error(report, ensure_result.error)
    if ensure_result.state_write is not None:
        report["reviewer_state_write"] = deps.reviewer_state_write_to_dict_fn(
            ensure_result.state_write
        )
    return FollowLoopTick(
        report=report,
        exit_code=frame_exit_code,
        reviewer_mode=ensure_result.reviewer_mode,
        progress_token=progress_token,
    )


def _maybe_auto_promote(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
    bridge_path: Path,
) -> dict[str, object] | None:
    if not bool(getattr(args, "auto_promote", False)):
        return None
    if not bridge_path.exists():
        return {"attempted": False, "promoted": False, "reason": "bridge_missing"}
    explicit_plan_path = paths.get("promotion_plan_path")
    if not isinstance(explicit_plan_path, Path):
        explicit_plan_path = None
    resolution = resolve_promotion_plan_path(
        repo_root=repo_root,
        bridge_path=bridge_path,
        explicit_plan_path=explicit_plan_path,
    )
    promotion_plan_path = resolution.path
    if promotion_plan_path is None:
        return {
            "attempted": True,
            "promoted": False,
            "reason": "scope_missing",
            "detail": resolution.detail or "Unable to resolve scoped plan path.",
        }

    bridge_text = bridge_path.read_text(encoding="utf-8")
    snapshot = extract_bridge_snapshot(bridge_text)
    readiness_errors = validate_promotion_ready(snapshot)
    try:
        current_hash = compute_non_audit_worktree_hash(
            repo_root=repo_root,
            excluded_rel_paths=bridge_excluded_rel_paths(
                repo_root=repo_root,
                bridge_path=bridge_path,
            ),
        )
    except (OSError, ValueError):
        current_hash = None
    liveness = summarize_bridge_liveness(
        snapshot,
        current_worktree_hash=current_hash,
    )
    if liveness.reviewed_hash_current is False:
        readiness_errors.append(
            "reviewed_hash_stale"
        )
    candidate = derive_promotion_candidate(
        repo_root=repo_root,
        promotion_plan_path=promotion_plan_path,
        require_exists=False,
    )
    if candidate is None:
        return {
            "attempted": True,
            "promoted": False,
            "reason": "no_unchecked_items",
        }
    if readiness_errors:
        return {
            "attempted": True,
            "promoted": False,
            "reason": "not_ready",
            "errors": readiness_errors,
        }

    promoted = promote_bridge_instruction(
        repo_root=repo_root,
        bridge_path=bridge_path,
        promotion_plan_path=promotion_plan_path,
        expected_instruction_revision=str(
            snapshot.metadata.get("current_instruction_revision") or ""
        ),
        expected_implementer_state_hash=bridge_implementer_state_hash(snapshot),
    )
    return {
        "attempted": True,
        "promoted": True,
        "source_path": promoted.source_path,
        "checklist_item": promoted.checklist_item,
        "instruction": promoted.instruction,
    }


def _append_follow_error(report: dict[str, object], error: str | None) -> None:
    if error is None:
        return
    errors = report.setdefault("errors", [])
    if isinstance(errors, list):
        errors.append(error)
