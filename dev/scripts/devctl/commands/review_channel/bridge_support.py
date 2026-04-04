"""Bridge-action support helpers for `devctl review-channel`."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from ...review_channel.core import (
    build_bridge_guard_report,
    ensure_launcher_prereqs,
    filter_provider_lanes,
    summarize_bridge_guard_failures,
)
from ...review_channel.current_session_projection import bridge_implementer_state_hash
from ...review_channel.bridge_validation import validate_launch_bridge_state
from ...review_channel.bridge_runtime_state import (
    BridgeStateContext,
    BridgeStateResult,
)
from ...review_channel.handoff import (
    bridge_liveness_to_dict,
    extract_bridge_snapshot,
    summarize_bridge_liveness,
)
from ...review_channel.heartbeat import (
    compute_non_audit_worktree_hash,
    refresh_bridge_heartbeat,
)
from ...review_channel.plan_resolution import resolve_promotion_plan_path
from ...review_channel.promotion import (
    DEFAULT_PROMOTION_PLAN_REL,
    resolve_scope_plan_path,
    scope_bridge_instruction,
)
from ...review_channel.reviewer_state_support import (
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
        from ...review_channel.handoff import BridgeSnapshot
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
    expected_implementer_state_hash = getattr(
        args,
        "expected_implementer_state_hash",
        None,
    )
    if (
        (not expected_instruction_revision or not expected_implementer_state_hash)
        and bridge_path.exists()
    ):
        bridge_text = bridge_path.read_text(encoding="utf-8")
        if not expected_instruction_revision:
            expected_instruction_revision = current_instruction_revision_from_bridge_text(
                bridge_text
            )
        if not expected_implementer_state_hash:
            expected_implementer_state_hash = bridge_implementer_state_hash(
                extract_bridge_snapshot(bridge_text)
            )
    return scope_bridge_instruction(
        repo_root=repo_root,
        bridge_path=bridge_path,
        scope_plan_path=scope_plan_path,
        expected_instruction_revision=expected_instruction_revision,
        expected_implementer_state_hash=expected_implementer_state_hash,
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


def _is_refreshable_metadata_error(error: str) -> bool:
    refreshable_tokens = (
        "Invalid `Last Codex poll` timestamp",
        "`Last Codex poll` is stale",
        "`Last Codex poll` is in the future",
        "Invalid `Last Codex poll (Local",
        "Invalid `Last non-audit worktree hash`",
    )
    return any(token in error for token in refreshable_tokens)
