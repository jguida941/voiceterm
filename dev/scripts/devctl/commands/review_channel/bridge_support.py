"""Bridge-action support helpers for `devctl review-channel`."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from ...review_channel.bridge_file import rewrite_bridge_markdown
from ...review_channel.bridge_runtime_state import BridgeStateContext, BridgeStateResult
from ...review_channel.bridge_validation import validate_launch_bridge_state
from ...review_channel.instruction_reset import reset_implementer_sections
from ...review_channel.core import (
    build_bridge_guard_report,
    ensure_launcher_prereqs,
    filter_provider_lanes,
    summarize_bridge_guard_failures,
)
from ...review_channel.handoff import bridge_liveness_to_dict, extract_bridge_snapshot, summarize_bridge_liveness
from ...review_channel.heartbeat import compute_non_audit_worktree_hash
from ...review_channel.peer_liveness import (
    ReviewerMode,
    normalize_reviewer_mode,
    resolve_reported_reviewer_mode,
)
from ...review_channel.reviewer_state_support import (
    ReviewerMetadataUpdate,
    write_reviewer_metadata,
)
from .bridge_scope import apply_scope_if_requested, resolve_launch_promotion_plan_path
from .bridge_stale_refresh import (
    BridgeStaleRefreshContext,
    maybe_refresh_stale_bridge_heartbeat,
    stale_bridge_launch_errors,
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
    bridge_refresh = maybe_refresh_stale_bridge_heartbeat(
        args=args,
        context=BridgeStaleRefreshContext(
            repo_root=context.repo_root,
            review_channel_path=context.review_channel_path,
            bridge_path=context.bridge_path,
            status_dir=context.status_dir,
            bridge_actions=bridge_actions,
        ),
        build_bridge_guard_report_fn=build_bridge_guard_report_fn,
    )
    reviewer_state_write = None
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
        reviewer_state_write = _maybe_apply_launch_reviewer_mode_override(
            args=args,
            repo_root=context.repo_root,
            bridge_path=context.bridge_path,
            bridge_text=context.bridge_path.read_text(encoding="utf-8"),
            worktree_hash=current_hash,
        )
        if reviewer_state_write is not None:
            bridge_snapshot = extract_bridge_snapshot(
                context.bridge_path.read_text(encoding="utf-8")
            )
            bridge_liveness_state = summarize_bridge_liveness(
                bridge_snapshot,
                current_worktree_hash=current_hash,
            )
    if args.action in bridge_actions and context.bridge_path.exists():
        dry_run = bool(getattr(args, "dry_run", False))
        bridge_guard_report = build_bridge_guard_report_fn(
            repo_root=context.repo_root,
            review_channel_path=context.review_channel_path,
            bridge_path=context.bridge_path,
        )
        guard_blocked_by_implementer_state = (
            not bridge_guard_report.get("ok", False)
            and _bridge_guard_blockers_are_implementer_owned(bridge_guard_report)
        )
        if guard_blocked_by_implementer_state and not getattr(args, "dry_run", False):
            updated_text = rewrite_bridge_markdown(
                context.bridge_path,
                transform=reset_implementer_sections,
            )
            bridge_snapshot = extract_bridge_snapshot(updated_text)
            bridge_liveness_state = summarize_bridge_liveness(
                bridge_snapshot,
                current_worktree_hash=current_hash,
            )
            bridge_guard_report = build_bridge_guard_report_fn(
                repo_root=context.repo_root,
                review_channel_path=context.review_channel_path,
                bridge_path=context.bridge_path,
            )
            guard_blocked_by_implementer_state = (
                not bridge_guard_report.get("ok", False)
                and _bridge_guard_blockers_are_implementer_owned(bridge_guard_report)
            )
        if (
            not bridge_guard_report.get("ok", False)
            and not guard_blocked_by_implementer_state
            and not _can_defer_bridge_guard(
                dry_run=dry_run,
                bridge_guard_report=bridge_guard_report,
            )
        ):
            raise ValueError(
                "Fresh conductor bootstrap requires a green review-channel "
                "bridge guard before launch: "
                + summarize_bridge_guard_failures(bridge_guard_report)
            )
        launch_state_errors = validate_launch_bridge_state(
            bridge_snapshot,
            liveness=bridge_liveness_state,
        )
        if _launch_blockers_are_implementer_owned(launch_state_errors) and not dry_run:
            updated_text = rewrite_bridge_markdown(
                context.bridge_path,
                transform=reset_implementer_sections,
            )
            bridge_snapshot = extract_bridge_snapshot(updated_text)
            bridge_liveness_state = summarize_bridge_liveness(
                bridge_snapshot,
                current_worktree_hash=current_hash,
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


def _maybe_apply_launch_reviewer_mode_override(
    *,
    args,
    repo_root: Path,
    bridge_path: Path,
    bridge_text: str,
    worktree_hash: str | None,
):
    requested = str(getattr(args, "reviewer_mode", "") or "").strip()
    if not requested:
        return None
    normalized = normalize_reviewer_mode(requested)
    snapshot = extract_bridge_snapshot(bridge_text)
    current = resolve_reported_reviewer_mode(snapshot.metadata)
    if normalized.value == current:
        return None
    updated_text, write = write_reviewer_metadata(
        bridge_text=bridge_text,
        repo_root=repo_root,
        bridge_path=bridge_path,
        update=ReviewerMetadataUpdate(
            reviewer_mode=normalized,
            reason=str(getattr(args, "reason", "") or "launch-reviewer-mode-override"),
            action="launch-reviewer-mode-override",
            worktree_hash=worktree_hash,
            current_instruction_revision=None,
            poll_note=(
                "Reviewer mode overridden for launch "
                f"(requested={normalized.value}; prior={current or 'unknown'})."
            ),
        ),
    )
    bridge_path.write_text(updated_text, encoding="utf-8")
    return write


def _can_defer_bridge_guard(
    *,
    dry_run: bool,
    bridge_guard_report: dict[str, object],
) -> bool:
    """Let later launch checks handle metadata-only guard gaps."""
    bridge = bridge_guard_report.get("bridge")
    if not isinstance(bridge, dict):
        return False
    blocking_fields = (
        "error",
        "missing_h2",
        "missing_markers",
        "hygiene_errors",
    )
    if any(bridge.get(field) for field in blocking_fields):
        return False
    state_errors = bridge.get("state_errors")
    if isinstance(state_errors, list) and state_errors and not all(
        _dry_run_can_defer_state_error(error) for error in state_errors
    ):
        return False
    metadata_errors = bridge.get("metadata_errors")
    if not isinstance(metadata_errors, list):
        metadata_errors = []
    if len(metadata_errors) == 1:
        return (
            "Missing typed ReviewState bridge metadata" in str(metadata_errors[0])
            or dry_run
            and _dry_run_can_defer_state_error(metadata_errors[0])
        )
    return dry_run and bool(state_errors) and not metadata_errors


def _dry_run_can_defer_state_error(error: object) -> bool:
    text = str(error or "").strip()
    return any(
        phrase in text
        for phrase in (
            "Active bridge mode requires typed current-session instruction revision",
            "Assigned-role progress is not current for the active instruction revision",
            "Assigned-role progress does not match the current reviewer instruction revision",
        )
    )


_IMPLEMENTER_OWNED_LAUNCH_ERROR_PREFIXES = (
    "Missing live implementer status compatibility section",
    "Missing live implementer ACK compatibility section",
    "Live implementer ACK (`Claude Ack` compatibility heading)",
    "Implementer status/ack compatibility sections (`Claude Status` / ",
    "Typed implementer ACK is not current",
    "Typed implementer ACK revision does not match",
    "Active bridge mode requires typed current-session instruction revision",
    "Assigned-role progress is not current for the active instruction revision",
    "Assigned-role progress does not match the current reviewer instruction revision",
)


def _launch_blockers_are_implementer_owned(errors: list[str]) -> bool:
    """Return True only when pair launch can safely reset Claude-owned sections."""
    return bool(errors) and all(
        error.startswith(_IMPLEMENTER_OWNED_LAUNCH_ERROR_PREFIXES)
        for error in errors
    )


def _bridge_guard_blockers_are_implementer_owned(
    bridge_guard_report: dict[str, object],
) -> bool:
    bridge = bridge_guard_report.get("bridge")
    if not isinstance(bridge, dict):
        return False
    blocking_errors: list[str] = []
    for key in ("metadata_errors", "state_errors"):
        values = bridge.get(key)
        if isinstance(values, list):
            blocking_errors.extend(str(value).strip() for value in values if value)
    if bridge.get("missing_h2") or bridge.get("missing_markers"):
        return False
    if bridge.get("error") or bridge.get("hygiene_errors"):
        return False
    review_channel = bridge_guard_report.get("review_channel")
    if isinstance(review_channel, dict) and not review_channel.get("ok", False):
        return False
    return _launch_blockers_are_implementer_owned(blocking_errors)
