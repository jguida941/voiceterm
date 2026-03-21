"""Reviewer follow-loop helpers for report-only supervisor status."""

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
from .handoff import extract_bridge_snapshot, summarize_bridge_liveness
from .heartbeat import compute_non_audit_worktree_hash
from .lifecycle_state import (
    ReviewerSupervisorHeartbeat,
)
from .plan_resolution import resolve_promotion_plan_path
from .promotion import (
    derive_promotion_candidate,
    promote_bridge_instruction,
    validate_promotion_ready,
)


@dataclass(frozen=True)
class ReviewerFollowDeps:
    ensure_reviewer_heartbeat_fn: Callable[..., object]
    build_reviewer_state_report_fn: Callable[..., tuple[dict, int]]
    reviewer_state_write_to_dict_fn: Callable[..., dict[str, object] | None]
    emit_follow_ndjson_frame_fn: Callable[..., int]
    reset_follow_output_fn: Callable[..., None]
    build_follow_completion_report_fn: Callable[..., dict[str, object]]
    build_follow_output_error_report_fn: Callable[..., dict[str, object]]
    write_reviewer_supervisor_heartbeat_fn: Callable[..., Path]
    utc_timestamp_fn: Callable[[], str]
    sleep_fn: Callable[[float], None]


def run_reviewer_follow_action(*, args, repo_root: Path, paths: dict[str, object], deps: ReviewerFollowDeps) -> tuple[dict, int]:
    """Poll reviewer-worker state on cadence and emit NDJSON frames."""
    return run_configured_follow_action(
        args=args, repo_root=repo_root, paths=paths, deps_source=deps,
        action=_reviewer_follow_action_shape(deps),
        build_tick_fn=lambda: _build_reviewer_follow_tick(args=args, repo_root=repo_root, paths=paths, deps=deps),
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
) -> FollowLoopTick:
    bridge_path = paths["bridge_path"]
    assert isinstance(bridge_path, Path)
    progress_token = build_claude_progress_token(
        repo_root=repo_root,
        bridge_path=bridge_path,
    )
    ensure_result = deps.ensure_reviewer_heartbeat_fn(
        repo_root=repo_root,
        bridge_path=bridge_path,
        reason="reviewer-follow",
        requested_reviewer_mode=getattr(args, "reviewer_mode", None),
    )
    report, frame_exit_code = deps.build_reviewer_state_report_fn(
        args=args,
        repo_root=repo_root,
        paths=paths,
    )
    auto_promotion = _maybe_auto_promote(
        args=args,
        repo_root=repo_root,
        paths=paths,
        bridge_path=bridge_path,
    )
    if auto_promotion is not None:
        report["auto_promotion"] = auto_promotion
        if bool(auto_promotion.get("promoted")):
            report, frame_exit_code = deps.build_reviewer_state_report_fn(
                args=args,
                repo_root=repo_root,
                paths=paths,
            )
            report["auto_promotion"] = auto_promotion
            progress_token = build_claude_progress_token(
                repo_root=repo_root,
                bridge_path=bridge_path,
            )
    report["reviewer_heartbeat_refreshed"] = ensure_result.refreshed
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
            excluded_rel_paths=("bridge.md",),
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
