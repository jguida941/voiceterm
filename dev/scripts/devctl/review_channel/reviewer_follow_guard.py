"""Compatibility support surface for reviewer follow guard helpers."""

from __future__ import annotations

from .reviewer_follow_heartbeat_guard import (
    maybe_refresh_automation_reviewer_heartbeat,
)
from .reviewer_follow_packet_guard import (
    ReviewerFollowPacketDeps,
    ReviewerFollowPacketRequest,
    ReviewerFollowTriggerState,
    maybe_queue_reviewer_follow_packet,
)

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .action_request_delivery import mark_action_request_packets_observed
from .core import ensure_launcher_prereqs, filter_provider_lanes
from .launch import build_launch_sessions
from .launch_records import LaunchSessionRequest
from .session_probe import load_conductor_sessions
from .terminal_app import cleanup_terminal_session
from .headless_delegate import terminal_window_ids
from .reviewer_wake_launch import (
    artifact_root as _artifact_root,
    launch_sessions_headless as _launch_sessions_headless,
    launch_sessions_visible as _launch_sessions_visible,
    provider_target as _provider_target,
    resolved_wake_approval_mode as _resolved_wake_approval_mode,
    visible_session_woke as _visible_session_woke,
)
from .wake_receipt_models import (
    WakeReceiptExtras,
    headless_launch_pids,
    wake_report,
)

__all__ = (
    "ReviewerWakeDeps",
    "ReviewerWakePaths",
    "ReviewerWakeLaunchContext",
    "WakeReceiptExtras",
    "wake_report",
    "cleanup_codex_sessions",
    "cleanup_candidate_codex_sessions",
    "cleanup_candidate_provider_sessions",
    "has_blocking_cleanup_warning",
    "launch_waiting_reviewer_conductor",
    "as_path",
    "maybe_refresh_automation_reviewer_heartbeat",
    "ReviewerFollowPacketDeps",
    "ReviewerFollowPacketRequest",
    "ReviewerFollowTriggerState",
    "maybe_queue_reviewer_follow_packet",
)


_BLOCKING_CLEANUP_WARNING_FRAGMENTS = (
    "permission denied",
    "failed to stop pid",
    "stayed alive",
)


@dataclass(frozen=True)
class ReviewerWakeDeps:
    """Injectable wake helpers for ensure-follow automation."""

    ensure_launcher_prereqs_fn: Callable[..., tuple[str, list[object]]] = (
        ensure_launcher_prereqs
    )
    build_launch_sessions_fn: Callable[..., list[dict[str, object]]] = (
        build_launch_sessions
    )
    launch_sessions_headless_fn: Callable[..., bool] = None
    launch_sessions_visible_fn: Callable[..., bool] = None
    load_conductor_sessions_fn: Callable[..., tuple[object, ...]] = (
        load_conductor_sessions
    )
    cleanup_terminal_session_fn: Callable[..., list[str]] = cleanup_terminal_session
    mark_action_request_packets_observed_fn: Callable[..., bool] = (
        mark_action_request_packets_observed
    )

    def __post_init__(self) -> None:
        if self.launch_sessions_headless_fn is None:
            object.__setattr__(
                self,
                "launch_sessions_headless_fn",
                _launch_sessions_headless,
            )
        if self.launch_sessions_visible_fn is None:
            object.__setattr__(
                self,
                "launch_sessions_visible_fn",
                _launch_sessions_visible,
            )


@dataclass(frozen=True)
class ReviewerWakePaths:
    status_dir: Path
    review_channel_path: Path
    bridge_path: Path


@dataclass(frozen=True)
class ReviewerWakeLaunchContext:
    args: object
    repo_root: Path
    paths: Mapping[str, object]
    report: Mapping[str, object]
    packet: Mapping[str, object]
    wake_paths: ReviewerWakePaths
    cleanup_warnings: tuple[str, ...]
    operator_interaction_mode: str
    provider: str = "codex"
    replaced_session_count: int = 0
    replaced_pids: tuple[int, ...] = ()
    wake_method_override: str = ""
    target_role: str = ""
    target_session_id: str = ""
    dashboard_session_id: str = ""


def cleanup_codex_sessions(
    *,
    live_codex_sessions: tuple[object, ...],
    deps: ReviewerWakeDeps,
) -> list[str]:
    warnings: list[str] = []
    for session in live_codex_sessions:
        warnings.extend(deps.cleanup_terminal_session_fn(session))
    return warnings


def has_blocking_cleanup_warning(warnings: list[str]) -> bool:
    normalized = [warning.lower() for warning in warnings]
    return any(
        fragment in warning
        for warning in normalized
        for fragment in _BLOCKING_CLEANUP_WARNING_FRAGMENTS
    )


def cleanup_candidate_codex_sessions(
    *,
    session_output_root: Path,
    deps: ReviewerWakeDeps,
) -> tuple[object, ...]:
    return cleanup_candidate_provider_sessions(
        session_output_root=session_output_root,
        provider="codex",
        deps=deps,
    )


def cleanup_candidate_provider_sessions(
    *,
    session_output_root: Path,
    provider: str,
    deps: ReviewerWakeDeps,
) -> tuple[object, ...]:
    target_provider = str(provider or "").strip().lower()
    sessions = deps.load_conductor_sessions_fn(session_output_root=session_output_root)
    return tuple(
        session
        for session in sessions
        if str(getattr(session, "provider", "")).strip().lower() == target_provider
        and (
            bool(getattr(session, "live", False))
            or bool(int(getattr(session, "session_pid", 0) or 0) > 0)
            or getattr(session, "terminal_window_id", None) is not None
            or str(getattr(session, "script_probe_state", "")).strip().lower()
            == "running"
        )
    )


def launch_waiting_reviewer_conductor(
    *,
    context: ReviewerWakeLaunchContext,
    deps: ReviewerWakeDeps,
) -> dict[str, object]:
    bridge_liveness = context.report.get("bridge_liveness")
    assert isinstance(bridge_liveness, dict)
    artifact_root = _artifact_root(context.paths.get("artifact_paths"))
    provider = str(context.provider or "codex").strip().lower() or "codex"

    try:
        _review_channel_text, lanes = deps.ensure_launcher_prereqs_fn(
            review_channel_path=context.wake_paths.review_channel_path,
            bridge_path=context.wake_paths.bridge_path,
            execution_mode=str(
                getattr(context.args, "execution_mode", "markdown-bridge")
            ),
        )

        provider_lanes = filter_provider_lanes(lanes, provider=provider)
        if not provider_lanes:
            return wake_report(
                packet=context.packet,
                attempted=True,
                woke=False,
                reason=f"{provider}_lanes_missing",
                target_agent=_provider_target(provider),
                extras=WakeReceiptExtras(warnings=tuple(context.cleanup_warnings)),
            )

        visible_launch = context.wake_method_override == "visible_session_launch"
        sessions = deps.build_launch_sessions_fn(
            request=LaunchSessionRequest(
                repo_root=context.repo_root,
                review_channel_path=context.wake_paths.review_channel_path,
                bridge_path=context.wake_paths.bridge_path,
                codex_lanes=[],
                claude_lanes=[],
                codex_workers=0,
                claude_workers=0,
                rollover_threshold_pct=int(
                    getattr(context.args, "rollover_threshold_pct", 20) or 20
                ),
                await_ack_seconds=int(
                    getattr(context.args, "await_ack_seconds", 180) or 180
                ),
                retirement_note=(
                    "Ensure-follow wake: replace the stuck remote-control Codex "
                    "reviewer session from typed review-channel state and "
                    "resume pending action requests."
                ),
                promotion_plan_rel=_promotion_plan_rel(
                    repo_root=context.repo_root,
                    promotion_plan_path=as_path(
                        context.paths.get("promotion_plan_path")
                    ),
                ),
                approval_mode=_resolved_wake_approval_mode(
                    args=context.args,
                    interaction_mode=context.operator_interaction_mode,
                ),
                dangerous=bool(getattr(context.args, "dangerous", False)),
                headless=not visible_launch,
                bridge_liveness=bridge_liveness,
                handoff_bundle=None,
                script_dir=as_path(context.paths.get("script_dir")),
                session_output_root=context.wake_paths.status_dir,
                provider_lane_map={provider: provider_lanes},
                requested_worker_budgets={provider: 0},
                providers_to_launch=(provider,),
                interaction_mode=context.operator_interaction_mode,
                worktree_path=context.repo_root,
            )
        )
    except ValueError as exc:
        return wake_report(
            packet=context.packet,
            attempted=True,
            woke=False,
            reason="launch_build_failed",
            target_agent=_provider_target(provider),
            extras=WakeReceiptExtras(
                warnings=tuple([*context.cleanup_warnings, str(exc)]),
            ),
        )

    launch_warnings: list[str] = []
    visible_launch = context.wake_method_override == "visible_session_launch"
    if visible_launch:
        woke = deps.launch_sessions_visible_fn(sessions, launch_warnings)
        spawned_pids: tuple[int, ...] = ()
    else:
        woke = deps.launch_sessions_headless_fn(sessions, launch_warnings)
        spawned_pids = headless_launch_pids(sessions)
    if (
        woke
        and artifact_root is not None
        and str(context.packet.get("kind") or "").strip() == "action_request"
    ):
        deps.mark_action_request_packets_observed_fn(
            artifact_root=artifact_root,
            packets=[context.packet],
            observer="publisher",
        )
    wake_method = (
        context.wake_method_override
        or ("replace" if context.replaced_session_count else "spawn_fresh")
    )
    is_delegate = wake_method == "headless_delegate"
    if is_delegate:
        reason = "headless_delegate_launched" if woke else "headless_delegate_failed"
    elif visible_launch:
        reason = "visible_session_launched" if woke else "visible_session_failed"
    else:
        reason = "launched" if woke else "launch_failed"
    return wake_report(
        packet=context.packet,
        attempted=True,
        woke=False if is_delegate else woke,
        reason=reason,
        target_agent=_provider_target(provider),
        extras=WakeReceiptExtras(
            target_role=context.target_role,
            target_session_id=context.target_session_id,
            dashboard_session_id=context.dashboard_session_id,
            wake_method=wake_method,
            requested_session_visibility=(
                "visible" if visible_launch else "headless" if is_delegate else ""
            ),
            delegated=(woke and is_delegate) if is_delegate else None,
            visible_session_woke=_visible_session_woke(
                visible_launch=visible_launch,
                is_delegate=is_delegate,
                woke=bool(woke),
            ),
            spawned_pids=tuple(spawned_pids),
            delivered_to_pids=tuple(spawned_pids) if is_delegate else (),
            replaced_pids=tuple(context.replaced_pids),
            terminal_window_ids=(
                terminal_window_ids(sessions) if visible_launch else ()
            ),
            warnings=tuple([*context.cleanup_warnings, *launch_warnings]),
        ),
    )


def as_path(value: object) -> Path | None:
    return value if isinstance(value, Path) else None


def _promotion_plan_rel(*, repo_root: Path, promotion_plan_path: Path | None) -> str:
    if promotion_plan_path is None:
        return "dev/active/review_channel.md"
    try:
        return str(promotion_plan_path.relative_to(repo_root))
    except ValueError:
        return "dev/active/review_channel.md"
