"""Ensure-action helpers for `devctl review-channel`."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ...review_channel.peer_liveness import REVIEW_CHANNEL_REVIEWER_FOLLOW_COMMAND
from ..review_channel_command import (
    EnsureActionReport,
    EnsureBridgeStatus,
    PublisherLifecycleAssessment,
    RuntimePaths,
    PUBLISHER_FOLLOW_COMMAND,
    _coerce_runtime_paths,
)
from ._ensure_supervisor import EnsureStatusSnapshot, try_restart_reviewer_supervisor


def _noop_sleep(_seconds: float) -> None:
    """Default no-op sleep for tests that do not need timing behavior."""


@dataclass(frozen=True, slots=True)
class EnsureActionDeps:
    """Callable boundary for ensure orchestration."""

    run_status_action_fn: Callable[..., tuple[dict, int]]
    read_publisher_state_safe_fn: Callable[..., dict[str, object]]
    assess_publisher_lifecycle_fn: Callable[..., PublisherLifecycleAssessment]
    spawn_follow_publisher_fn: Callable[..., tuple[bool, int | None, str]]
    verify_detached_start_fn: Callable[..., str]
    refresh_bridge_heartbeat_fn: Callable[..., object]
    reviewer_mode_is_active_fn: Callable[[str | None], bool]
    run_ensure_follow_action_fn: Callable[..., tuple[dict, int]]
    spawn_reviewer_supervisor_fn: Callable[..., tuple[bool, int | None, str]] | None = None
    verify_reviewer_supervisor_start_fn: Callable[..., str] | None = None
    sleep_fn: Callable[[float], None] = _noop_sleep


def build_ensure_bridge_status(report: dict[str, object]) -> EnsureBridgeStatus:
    """Extract the bridge-health subset used by ensure."""
    bridge_liveness = report.get("bridge_liveness", {})
    attention = report.get("attention", {})
    reviewer_worker = report.get("reviewer_worker")
    reviewer_supervisor = report.get("reviewer_supervisor")

    review_needed = report.get("review_needed")
    if review_needed is None and isinstance(reviewer_worker, dict):
        review_needed = reviewer_worker.get("review_needed")

    return EnsureBridgeStatus(
        reviewer_mode=str(bridge_liveness.get("reviewer_mode", "unknown")),
        codex_poll_state=str(bridge_liveness.get("codex_poll_state", "unknown")),
        reviewer_freshness=str(bridge_liveness.get("reviewer_freshness", "")),
        heartbeat_age_seconds=bridge_liveness.get("last_codex_poll_age_seconds"),
        attention_status=str(attention.get("status", "unknown")),
        claude_ack_current=bool(bridge_liveness.get("claude_ack_current")),
        review_needed=bool(review_needed),
        reviewer_supervisor_running=bool(
            reviewer_supervisor.get("running")
        )
        if isinstance(reviewer_supervisor, dict)
        else False,
        reviewer_worker=reviewer_worker if isinstance(reviewer_worker, dict) else None,
        reviewer_supervisor=(
            reviewer_supervisor if isinstance(reviewer_supervisor, dict) else None
        ),
        service_identity=(
            report.get("service_identity")
            if isinstance(report.get("service_identity"), dict)
            else None
        ),
        attach_auth_policy=(
            report.get("attach_auth_policy")
            if isinstance(report.get("attach_auth_policy"), dict)
            else None
        ),
    )


def read_ensure_status(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
    deps: EnsureActionDeps,
) -> tuple[dict[str, object], EnsureBridgeStatus]:
    """Read status and its ensure view together."""
    report, _exit_code = deps.run_status_action_fn(
        args=args,
        repo_root=repo_root,
        paths=paths,
    )
    return report, build_ensure_bridge_status(report)


def assess_publisher_lifecycle(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
    reviewer_mode_active: bool,
    deps: EnsureActionDeps,
) -> PublisherLifecycleAssessment:
    """Assess publisher lifecycle for ensure."""
    runtime_paths = _coerce_runtime_paths(paths)
    publisher_state = deps.read_publisher_state_safe_fn(runtime_paths)
    publisher_running = bool(publisher_state.get("running"))

    if not reviewer_mode_active:
        return PublisherLifecycleAssessment(
            publisher_state=publisher_state,
            publisher_running=publisher_running,
            publisher_required=False,
            publisher_status="inactive_mode",
            details=(
                "Persistent publisher is not required while reviewer mode is inactive.",
            ),
        )

    publisher_start_status = "not_attempted"
    publisher_pid: int | None = None
    publisher_log_path: str | None = None
    details: list[str] = []

    if (
        not publisher_running
        and bool(getattr(args, "start_publisher_if_missing", False))
    ):
        started, publisher_pid, publisher_log_path = deps.spawn_follow_publisher_fn(
            args=args,
            repo_root=repo_root,
            paths=runtime_paths,
        )
        publisher_start_status = "started" if started else "failed"

        if started:
            for _ in range(10):
                deps.sleep_fn(0.1)
                publisher_state = deps.read_publisher_state_safe_fn(runtime_paths)
                if bool(publisher_state.get("running")):
                    publisher_running = True
                    break

            if not publisher_running:
                publisher_start_status = deps.verify_detached_start_fn(
                    pid=publisher_pid,
                    paths=runtime_paths,
                )

            details.append("Persistent publisher start was requested.")
        else:
            details.append(
                "Persistent publisher start failed before launch confirmation."
            )

    if publisher_running:
        return PublisherLifecycleAssessment(
            publisher_state=publisher_state,
            publisher_running=True,
            publisher_required=True,
            publisher_status="running",
            publisher_start_status=publisher_start_status,
            publisher_pid=publisher_pid,
            publisher_log_path=publisher_log_path,
            details=tuple(details + ["Persistent publisher is running."]),
        )

    stop_reason = str(publisher_state.get("stop_reason", ""))
    if stop_reason == "failed_start":
        attention_override = "publisher_failed_start"
    elif stop_reason == "detached_exit":
        attention_override = "publisher_detached_exit"
    else:
        attention_override = "publisher_missing"

    recommended_command = None
    if publisher_start_status != "started":
        recommended_command = PUBLISHER_FOLLOW_COMMAND

    details.append("Persistent publisher is not running; start the follow publisher.")
    return PublisherLifecycleAssessment(
        publisher_state=publisher_state,
        publisher_running=False,
        publisher_required=True,
        publisher_status="not_running",
        publisher_start_status=publisher_start_status,
        publisher_pid=publisher_pid,
        publisher_log_path=publisher_log_path,
        recommended_command=recommended_command,
        attention_override=attention_override,
        details=tuple(details),
    )


def run_ensure_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
    deps: EnsureActionDeps,
) -> tuple[dict, int]:
    """Run the reviewer-heartbeat ensure flow."""
    runtime_paths = _coerce_runtime_paths(paths)

    if getattr(args, "follow", False):
        return deps.run_ensure_follow_action_fn(
            args=args,
            repo_root=repo_root,
            paths=runtime_paths,
        )

    report, bridge_state = read_ensure_status(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        deps=deps,
    )
    refreshed = False
    refresh_detail = None

    if bridge_state.codex_poll_state in ("stale", "missing"):
        if runtime_paths.bridge_path is not None and runtime_paths.bridge_path.exists():
            try:
                refresh_result = deps.refresh_bridge_heartbeat_fn(
                    repo_root=repo_root,
                    bridge_path=runtime_paths.bridge_path,
                    reason="ensure",
                )
                refreshed = True
                refresh_detail = (
                    f"Heartbeat refreshed at {refresh_result.last_codex_poll_utc}"
                )

                report, bridge_state = read_ensure_status(
                    args=args,
                    repo_root=repo_root,
                    paths=runtime_paths,
                    deps=deps,
                )
            except (ValueError, OSError) as exc:
                refresh_detail = f"Heartbeat refresh failed: {exc}"

    restart_attempt = try_restart_reviewer_supervisor(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        deps=deps,
        snapshot=EnsureStatusSnapshot(
            report=report,
            bridge_state=bridge_state,
        ),
        read_ensure_status_fn=read_ensure_status,
    )
    reviewer_supervisor_restarted = restart_attempt.restarted
    report = restart_attempt.report
    bridge_state = restart_attempt.bridge_state

    pub = deps.assess_publisher_lifecycle_fn(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        reviewer_mode_active=deps.reviewer_mode_is_active_fn(bridge_state.reviewer_mode),
        deps=deps,
    )
    attention_status = pub.attention_override or bridge_state.attention_status
    ensure_ok = (
        bridge_state.heartbeat_ok
        and (bridge_state.reviewer_supervisor_ok or reviewer_supervisor_restarted)
        and not (pub.publisher_required and not pub.publisher_running)
    )

    detail_parts: list[str] = []

    if reviewer_supervisor_restarted:
        detail_parts.append("Reviewer supervisor was dead; auto-restarted.")
    elif restart_attempt.attempted and restart_attempt.start_status == "spawn_failed":
        detail_parts.append(
            "Reviewer supervisor auto-restart failed before launch confirmation."
        )
    elif restart_attempt.attempted and restart_attempt.start_status != "not_attempted":
        detail_parts.append(
            "Reviewer supervisor auto-restart failed before heartbeat confirmation."
        )
    if ensure_ok:
        detail_parts.append("Reviewer loop is healthy.")
    else:
        detail_parts.append(
            f"Reviewer loop needs attention: {attention_status} "
            f"(poll={bridge_state.codex_poll_state})."
        )

    if refresh_detail:
        detail_parts.append(refresh_detail)

    if not bridge_state.reviewer_supervisor_ok and not reviewer_supervisor_restarted:
        detail_parts.append(
            "reviewer supervisor follow loop is required while review is pending."
        )

    detail_parts.extend(pub.details)

    recommended_command = pub.recommended_command
    if not bridge_state.reviewer_supervisor_ok and not reviewer_supervisor_restarted:
        recommended_command = REVIEW_CHANNEL_REVIEWER_FOLLOW_COMMAND
    elif pub.publisher_required and not pub.publisher_running:
        recommended_command = PUBLISHER_FOLLOW_COMMAND

    ensure_report = EnsureActionReport(
        command="review-channel",
        action="ensure",
        ok=ensure_ok,
        reviewer_mode=bridge_state.reviewer_mode,
        codex_poll_state=bridge_state.codex_poll_state,
        reviewer_freshness=bridge_state.reviewer_freshness,
        heartbeat_age_seconds=bridge_state.heartbeat_age_seconds,
        attention_status=attention_status,
        refreshed=refreshed,
        publisher=pub.publisher_state,
        publisher_required=pub.publisher_required,
        publisher_status=pub.publisher_status,
        publisher_start_status=pub.publisher_start_status,
        reviewer_worker=bridge_state.reviewer_worker,
        reviewer_supervisor=bridge_state.reviewer_supervisor,
        service_identity=bridge_state.service_identity,
        attach_auth_policy=bridge_state.attach_auth_policy,
        detail=" ".join(detail_parts),
        review_needed=bridge_state.review_needed,
        publisher_pid=pub.publisher_pid,
        publisher_log_path=pub.publisher_log_path,
        recommended_command=recommended_command,
    )
    return ensure_report.to_report(), 0 if ensure_ok else 1
