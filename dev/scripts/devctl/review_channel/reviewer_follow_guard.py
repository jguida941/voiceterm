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
    load_conductor_sessions_fn: Callable[..., tuple[object, ...]] = (
        load_conductor_sessions
    )
    cleanup_terminal_session_fn: Callable[..., list[str]] = cleanup_terminal_session
    mark_action_request_packets_observed_fn: Callable[..., bool] = (
        mark_action_request_packets_observed
    )

    def __post_init__(self) -> None:
        if self.launch_sessions_headless_fn is not None:
            return
        object.__setattr__(
            self,
            "launch_sessions_headless_fn",
            _launch_sessions_headless,
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


def live_codex_sessions(
    *,
    session_output_root: Path,
    deps: ReviewerWakeDeps,
) -> tuple[object, ...]:
    sessions = deps.load_conductor_sessions_fn(session_output_root=session_output_root)
    return tuple(
        session
        for session in sessions
        if getattr(session, "provider", "") == "codex"
        and bool(getattr(session, "live", False))
    )


def launch_waiting_reviewer_conductor(
    *,
    context: ReviewerWakeLaunchContext,
    deps: ReviewerWakeDeps,
) -> dict[str, object]:
    bridge_liveness = context.report.get("bridge_liveness")
    assert isinstance(bridge_liveness, dict)
    artifact_root = _artifact_root(context.paths.get("artifact_paths"))

    try:
        _review_channel_text, lanes = deps.ensure_launcher_prereqs_fn(
            review_channel_path=context.wake_paths.review_channel_path,
            bridge_path=context.wake_paths.bridge_path,
            execution_mode=str(
                getattr(context.args, "execution_mode", "markdown-bridge")
            ),
        )

        codex_lanes = filter_provider_lanes(lanes, provider="codex")
        if not codex_lanes:
            return wake_report(
                packet=context.packet,
                attempted=True,
                woke=False,
                reason="codex_lanes_missing",
                warnings=list(context.cleanup_warnings),
            )

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
                approval_mode=str(getattr(context.args, "approval_mode", "") or ""),
                dangerous=bool(getattr(context.args, "dangerous", False)),
                headless=True,
                bridge_liveness=bridge_liveness,
                handoff_bundle=None,
                script_dir=as_path(context.paths.get("script_dir")),
                session_output_root=context.wake_paths.status_dir,
                provider_lane_map={"codex": codex_lanes},
                requested_worker_budgets={"codex": 0},
                providers_to_launch=("codex",),
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
            warnings=[*context.cleanup_warnings, str(exc)],
        )

    launch_warnings: list[str] = []
    woke = deps.launch_sessions_headless_fn(sessions, launch_warnings)
    if woke and artifact_root is not None:
        deps.mark_action_request_packets_observed_fn(
            artifact_root=artifact_root,
            packets=[context.packet],
            observer="publisher",
        )
    return wake_report(
        packet=context.packet,
        attempted=True,
        woke=woke,
        reason="launched" if woke else "launch_failed",
        warnings=[*context.cleanup_warnings, *launch_warnings],
    )


def as_path(value: object) -> Path | None:
    return value if isinstance(value, Path) else None


def wake_report(
    *,
    packet: Mapping[str, object],
    attempted: bool,
    woke: bool,
    reason: str,
    warnings: list[str] | None = None,
) -> dict[str, object]:
    report = {
        "attempted": attempted,
        "woke": woke,
        "reason": reason,
        "packet_id": str(packet.get("packet_id") or "").strip(),
        "requested_action": str(packet.get("requested_action") or "").strip(),
    }
    if warnings:
        report["warnings"] = list(warnings)
    return report


def _promotion_plan_rel(*, repo_root: Path, promotion_plan_path: Path | None) -> str:
    if promotion_plan_path is None:
        return "dev/active/review_channel.md"
    try:
        return str(promotion_plan_path.relative_to(repo_root))
    except ValueError:
        return "dev/active/review_channel.md"


def _artifact_root(value: object) -> Path | None:
    if value is None:
        return None
    artifact_root = getattr(value, "artifact_root", None)
    return artifact_root if isinstance(artifact_root, Path) else None


def _launch_sessions_headless(
    sessions: list[dict[str, object]],
    warnings: list[str],
) -> bool:
    from ..commands.review_channel.bridge_launch_headless import (
        launch_sessions_headless,
    )

    return launch_sessions_headless(sessions, warnings)
