"""Ensure-action helpers for `devctl review-channel`."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..review_channel_command import (
    EnsureBridgeStatus,
    PublisherLifecycleAssessment,
    RuntimePaths,
    PUBLISHER_FOLLOW_COMMAND,
    _coerce_runtime_paths,
)
from ._ensure_helpers import (
    build_ensure_detail,
    build_ensure_report,
    try_refresh_heartbeat,
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
    reviewer_runtime = report.get("reviewer_runtime")

    review_needed = report.get("review_needed")
    if review_needed is None and isinstance(reviewer_worker, dict):
        review_needed = reviewer_worker.get("review_needed")
    remote_control_attachment = (
        reviewer_runtime.get("remote_control_attachment")
        if isinstance(reviewer_runtime, Mapping)
        else None
    )

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
        remote_control_implementer_active=_remote_control_implementer_active(
            remote_control_attachment
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


def _try_start_publisher(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths,
    publisher_state: dict[str, object],
    deps: EnsureActionDeps,
) -> tuple[dict[str, object], bool, str, int | None, str | None, list[str]]:
    """Attempt to spawn the publisher and wait for it to confirm running."""
    details: list[str] = []

    started, pid, log_path = deps.spawn_follow_publisher_fn(
        args=args, repo_root=repo_root, paths=paths,
    )
    start_status = "started" if started else "failed"
    running = False

    if started:
        for _ in range(10):
            deps.sleep_fn(0.1)
            publisher_state = deps.read_publisher_state_safe_fn(paths)
            if bool(publisher_state.get("running")):
                running = True
                break

        if not running:
            start_status = deps.verify_detached_start_fn(pid=pid, paths=paths)

        details.append("Persistent publisher start was requested.")
    else:
        details.append(
            "Persistent publisher start failed before launch confirmation."
        )

    return publisher_state, running, start_status, pid, log_path, details


def _stopped_publisher_attention(stop_reason: str) -> str:
    """Map a publisher stop reason to an attention override label."""
    if stop_reason == "failed_start":
        return "publisher_failed_start"
    if stop_reason == "detached_exit":
        return "publisher_detached_exit"
    return "publisher_missing"


def assess_publisher_lifecycle(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
    reviewer_mode_active: bool,
    remote_control_implementer_active: bool,
    deps: EnsureActionDeps,
) -> PublisherLifecycleAssessment:
    """Assess publisher lifecycle for ensure."""
    runtime_paths = _coerce_runtime_paths(paths)
    publisher_state = deps.read_publisher_state_safe_fn(runtime_paths)
    publisher_running = bool(publisher_state.get("running"))
    publisher_required = reviewer_mode_active or remote_control_implementer_active

    if not publisher_required:
        return PublisherLifecycleAssessment(
            publisher_state=publisher_state,
            publisher_running=publisher_running,
            publisher_required=False,
            publisher_status="inactive_mode",
            details=(
                "Persistent publisher is not required while reviewer mode is inactive.",
            ),
        )

    start_status = "not_attempted"
    pid: int | None = None
    log_path: str | None = None
    details: list[str] = []

    if not publisher_running and bool(
        getattr(args, "start_publisher_if_missing", False)
    ):
        publisher_state, publisher_running, start_status, pid, log_path, details = (
            _try_start_publisher(
                args=args, repo_root=repo_root, paths=runtime_paths,
                publisher_state=publisher_state, deps=deps,
            )
        )

    if publisher_running:
        return PublisherLifecycleAssessment(
            publisher_state=publisher_state,
            publisher_running=True,
            publisher_required=True,
            publisher_status="running",
            publisher_start_status=start_status,
            publisher_pid=pid,
            publisher_log_path=log_path,
            details=tuple(details + ["Persistent publisher is running."]),
        )

    attention_override = _stopped_publisher_attention(
        str(publisher_state.get("stop_reason", ""))
    )
    recommended_command = PUBLISHER_FOLLOW_COMMAND if start_status != "started" else None

    details.append("Persistent publisher is not running; start the follow publisher.")
    return PublisherLifecycleAssessment(
        publisher_state=publisher_state,
        publisher_running=False,
        publisher_required=True,
        publisher_status="not_running",
        publisher_start_status=start_status,
        publisher_pid=pid,
        publisher_log_path=log_path,
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
        args=args, repo_root=repo_root, paths=runtime_paths, deps=deps,
    )

    hb = try_refresh_heartbeat(
        args=args, repo_root=repo_root, paths=runtime_paths,
        bridge_state=bridge_state, report=report, deps=deps,
        read_ensure_status_fn=read_ensure_status,
    )
    report, bridge_state = hb.report, hb.bridge_state

    restart_attempt = try_restart_reviewer_supervisor(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        deps=deps,
        snapshot=EnsureStatusSnapshot(report=report, bridge_state=bridge_state),
        read_ensure_status_fn=read_ensure_status,
    )
    report = restart_attempt.report
    bridge_state = restart_attempt.bridge_state

    pub = deps.assess_publisher_lifecycle_fn(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        reviewer_mode_active=deps.reviewer_mode_is_active_fn(bridge_state.reviewer_mode),
        remote_control_implementer_active=(
            bridge_state.remote_control_implementer_active
        ),
        deps=deps,
    )
    attention_status = pub.attention_override or bridge_state.attention_status
    ensure_ok = (
        bridge_state.heartbeat_ok
        and (bridge_state.reviewer_supervisor_ok or restart_attempt.restarted)
        and not (pub.publisher_required and not pub.publisher_running)
    )

    detail, recommended_command = build_ensure_detail(
        restart_attempt=restart_attempt,
        ensure_ok=ensure_ok,
        attention_status=attention_status,
        bridge_state=bridge_state,
        refresh_detail=hb.detail,
        pub=pub,
    )

    report_dict = build_ensure_report(
        ensure_ok=ensure_ok,
        bridge_state=bridge_state,
        attention_status=attention_status,
        hb=hb,
        pub=pub,
        detail=detail,
        recommended_command=recommended_command,
    )
    return report_dict, 0 if ensure_ok else 1


def _remote_control_implementer_active(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    status = str(value.get("status") or "").strip().lower()
    role = str(value.get("role") or "").strip().lower()
    return role == "implementer" and status in {"attached", "unknown", "stale"}
