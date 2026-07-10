"""Launch-time stale heartbeat refresh helpers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ...review_channel.bridge_validation import validate_launch_bridge_state
from ...review_channel.heartbeat import refresh_bridge_heartbeat
from ...review_channel.handoff import extract_bridge_snapshot, summarize_bridge_liveness
from ...review_channel.peer_liveness import (
    CodexPollState,
    ReviewerMode,
    resolve_reported_reviewer_mode,
)
from ...review_channel.remote_control_attachment_artifact import (
    load_remote_control_attachments,
)


@dataclass(frozen=True)
class BridgeStaleRefreshContext:
    repo_root: Path
    review_channel_path: Path
    bridge_path: Path
    status_dir: Path
    bridge_actions: set[str]


def maybe_refresh_stale_bridge_heartbeat(
    *,
    args,
    context: BridgeStaleRefreshContext,
    build_bridge_guard_report_fn: Callable[..., dict[str, object]],
):
    """Refresh stale bridge heartbeat metadata when launch/status allows it."""
    refreshable_actions = set(context.bridge_actions) | {"status"}
    allow_status_refresh = args.action != "status" or not getattr(
        args, "dry_run", False
    )
    if (
        not context.bridge_path.exists()
        or args.action not in refreshable_actions
        or not allow_status_refresh
        or not getattr(args, "refresh_bridge_heartbeat_if_stale", False)
    ):
        return None
    stale_errors = stale_bridge_launch_errors(
        repo_root=context.repo_root,
        review_channel_path=context.review_channel_path,
        bridge_path=context.bridge_path,
        status_dir=context.status_dir,
        enable_typed_remote_control_refresh=args.action == "status",
        build_bridge_guard_report_fn=build_bridge_guard_report_fn,
    )
    if not stale_errors:
        return None
    return refresh_bridge_heartbeat(
        repo_root=context.repo_root,
        bridge_path=context.bridge_path,
        reason=f"devctl review-channel {args.action}",
        allow_non_refreshable_launch_errors=args.action == "status",
    )


def stale_bridge_launch_errors(
    *,
    repo_root: Path,
    review_channel_path: Path,
    bridge_path: Path,
    status_dir: Path | None = None,
    enable_typed_remote_control_refresh: bool = False,
    build_bridge_guard_report_fn: Callable[..., dict[str, object]] | None = None,
) -> list[str]:
    """Return refreshable metadata errors when the bridge guard fails on stale heartbeat."""
    if build_bridge_guard_report_fn is None:
        from ...review_channel.core import build_bridge_guard_report

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
    if isinstance(state_errors, list) and state_errors and not all(
        _state_error_allows_stale_heartbeat_refresh(error) for error in state_errors
    ):
        return []
    bridge_snapshot = extract_bridge_snapshot(bridge_path.read_text(encoding="utf-8"))
    liveness = summarize_bridge_liveness(bridge_snapshot)
    launch_errors = validate_launch_bridge_state(
        bridge_snapshot,
        liveness=liveness,
    )
    refreshable_errors = [
        str(error).strip()
        for error in launch_errors
        if _is_refreshable_metadata_error(str(error))
    ]
    if refreshable_errors:
        return refreshable_errors
    if (
        enable_typed_remote_control_refresh
        and _typed_remote_control_tools_only_refreshable(
            snapshot=bridge_snapshot,
            liveness=liveness,
            status_dir=status_dir,
        )
    ):
        return [
            "`Last Codex poll` is stale; typed remote-control continuity "
            "requires a reviewer heartbeat refresh."
        ]
    return []


def _is_refreshable_metadata_error(error: str) -> bool:
    refreshable_tokens = (
        "Missing `Last Codex poll`",
        "Invalid `Last Codex poll` timestamp",
        "`Last Codex poll` is stale",
        "`Last Codex poll` is in the future",
        "Invalid `Last Codex poll (Local",
        "Invalid `Last non-audit worktree hash`",
    )
    return any(token in error for token in refreshable_tokens)


def _state_error_allows_stale_heartbeat_refresh(error: object) -> bool:
    return str(error or "").strip().startswith(
        "Active bridge mode requires typed current-session instruction revision"
    )


def _typed_remote_control_tools_only_refreshable(
    *,
    snapshot: object,
    liveness: object,
    status_dir: Path | None,
) -> bool:
    """Allow status refresh to reassert liveness from typed remote-control state."""
    if status_dir is None:
        return False
    reviewer_mode = resolve_reported_reviewer_mode(
        getattr(snapshot, "metadata", {}) or {}
    )
    if reviewer_mode != ReviewerMode.TOOLS_ONLY.value:
        return False
    poll_state = str(getattr(liveness, "codex_poll_state", "") or "").strip()
    if poll_state not in {CodexPollState.MISSING.value, CodexPollState.STALE.value}:
        return False
    return bool(
        load_remote_control_attachments(output_root=status_dir, active_only=True)
    )


__all__ = [
    "BridgeStaleRefreshContext",
    "maybe_refresh_stale_bridge_heartbeat",
    "stale_bridge_launch_errors",
]
