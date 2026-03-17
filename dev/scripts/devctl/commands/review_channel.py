"""`devctl review-channel` command implementation.

Orchestrates bridge-backed and event-backed review-channel actions. The
heavy rendering and execution logic lives in the dedicated handler modules:

- review_channel_bridge_handler: launch, rollover, promote, status (bridge)
- review_channel_event_handler: post, watch, inbox, ack, dismiss, apply, history
"""

from __future__ import annotations

from collections.abc import Mapping
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from ..common import emit_output
from ..config import REPO_ROOT
from ..review_channel.core import filter_provider_lanes
from ..review_channel.context_refs import resolve_context_pack_refs  # noqa: F401 -- re-exported for test patch targets
from ..review_channel.events import event_state_exists
from ..review_channel.event_store import (
    build_bridge_status_fallback_warning,
    summarize_review_state_errors,
)
from ..review_channel.follow_controller import EnsureFollowDeps, run_ensure_follow_action
from ..review_channel.follow_stream import (
    build_follow_completion_report,
    build_follow_output_error_report,
    emit_follow_ndjson_frame,
    reset_follow_output,
)
from ..review_channel.reviewer_follow import ReviewerFollowDeps, run_reviewer_follow_action
from ..review_channel.reviewer_state import (
    ReviewerCheckpointUpdate,
    ensure_reviewer_heartbeat,
    reviewer_state_write_to_dict,
    write_reviewer_checkpoint,
    write_reviewer_heartbeat,
)
from ..review_channel.reviewer_worker import (
    check_review_needed,
    reviewer_worker_tick_to_dict,
)
from ..review_channel.lifecycle_state import (
    PublisherHeartbeat,
    ReviewerSupervisorHeartbeat,
    read_publisher_state,
    read_reviewer_supervisor_state,
    write_publisher_heartbeat,
    write_reviewer_supervisor_heartbeat,
)
from ..review_channel.state import (
    build_attach_auth_policy,
    build_service_identity,
    refresh_status_snapshot,
)
from ..time_utils import utc_timestamp
from .review_channel_bridge_handler import BRIDGE_ACTIONS, _run_bridge_action
from .review_channel_bridge_render import build_bridge_success_report
from .review_channel_command import (
    EVENT_ACTION_SET,
    FAILED_START_HEARTBEAT_FIELDS,
    PUBLISHER_FOLLOW_COMMAND,
    PUBLISHER_FOLLOW_COMMAND_ARGS,
    PUBLISHER_FOLLOW_LOG_FILENAME,
    PUBLISHER_FOLLOW_OUTPUT_FILENAME,
    REVIEWER_STATE_ACTION_SET,
    REVIEWER_STATE_REPORT_DEFAULTS,
    EnsureActionReport,
    EnsureBridgeStatus,
    PublisherLifecycleAssessment,
    ReviewChannelAction,
    RuntimePaths,
    _coerce_action,
    _coerce_runtime_paths,
    _error_report,
    _event_report_error_detail,
    _render_report,
    _resolve_runtime_paths,
    _validate_args,
)
from .review_channel_event_handler import _run_event_action


def _run_status_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> tuple[dict, int]:
    """Run status with event-backed fallback."""
    runtime_paths = _coerce_runtime_paths(paths)
    artifact_paths = runtime_paths.artifact_paths
    execution_mode = getattr(args, "execution_mode", "auto")
    fallback_warnings: list[str] = []

    if (
        execution_mode != "markdown-bridge"
        and artifact_paths is not None
        and event_state_exists(artifact_paths)
    ):
        try:
            report, exit_code = _run_event_action(
                args=args,
                repo_root=repo_root,
                paths=runtime_paths,
            )
        except (OSError, ValueError) as exc:
            fallback_warnings.append(build_bridge_status_fallback_warning(str(exc)))
        else:
            state_errors = summarize_review_state_errors(
                {"ok": report.get("ok"), "errors": report.get("errors")}
            )

            if exit_code == 0 and state_errors is None:
                _attach_status_context(
                    report,
                    repo_root=repo_root,
                    paths=runtime_paths,
                )
                return report, exit_code

            fallback_warnings.append(
                build_bridge_status_fallback_warning(
                    state_errors or _event_report_error_detail(report)
                )
            )

    if not fallback_warnings:
        return _run_bridge_status(
            args=args,
            repo_root=repo_root,
            paths=runtime_paths,
        )

    try:
        return _run_bridge_status(
            args=args,
            repo_root=repo_root,
            paths=runtime_paths,
            extra_warnings=fallback_warnings,
            report_execution_mode="markdown-bridge",
        )
    except ValueError as exc:
        raise ValueError(
            f"{fallback_warnings[-1]} Markdown-bridge fallback was unavailable: {exc}"
        ) from exc


def _read_publisher_state_safe(
    paths: RuntimePaths | Mapping[str, object],
) -> dict[str, object]:
    """Read publisher state without failing status."""
    runtime_paths = _coerce_runtime_paths(paths)

    if runtime_paths.status_dir is None:
        return {"running": False, "detail": "status_dir not resolved"}

    try:
        return read_publisher_state(runtime_paths.status_dir)
    except (OSError, ValueError):
        return {"running": False, "detail": "publisher state read failed"}


def _read_reviewer_supervisor_state_safe(
    paths: RuntimePaths | Mapping[str, object],
) -> dict[str, object]:
    """Read reviewer supervisor state without failing status."""
    runtime_paths = _coerce_runtime_paths(paths)

    if runtime_paths.status_dir is None:
        return {"running": False, "detail": "status_dir not resolved"}

    try:
        return read_reviewer_supervisor_state(runtime_paths.status_dir)
    except (OSError, ValueError):
        return {"running": False, "detail": "reviewer supervisor state read failed"}


def _attach_service_identity(
    report: dict[str, object],
    *,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> None:
    """Attach the repo/worktree service identity."""
    runtime_paths = _coerce_runtime_paths(paths)

    if runtime_paths.bridge_path is None:
        report["service_identity"] = None
        return

    if runtime_paths.review_channel_path is None:
        report["service_identity"] = None
        return

    if runtime_paths.status_dir is None:
        report["service_identity"] = None
        return

    report["service_identity"] = build_service_identity(
        repo_root=repo_root,
        bridge_path=runtime_paths.bridge_path,
        review_channel_path=runtime_paths.review_channel_path,
        output_root=runtime_paths.status_dir,
    )


def _attach_attach_auth_policy(report: dict[str, object]) -> None:
    """Attach the current attach/auth policy."""
    service_identity = report.get("service_identity")

    if not isinstance(service_identity, dict):
        report["attach_auth_policy"] = None
        return

    report["attach_auth_policy"] = build_attach_auth_policy(
        service_identity=service_identity,
    )


def _attach_backend_contract(
    report: dict[str, object],
    *,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> None:
    """Attach backend-contract metadata."""
    _attach_service_identity(report, repo_root=repo_root, paths=paths)
    _attach_attach_auth_policy(report)


def _attach_reviewer_worker(
    report: dict[str, object],
    *,
    repo_root: Path,
    bridge_path: Path | object,
) -> None:
    """Attach reviewer-worker status."""
    if not isinstance(bridge_path, Path):
        report["reviewer_worker"] = None
        return

    tick = check_review_needed(repo_root=repo_root, bridge_path=bridge_path)
    report["review_needed"] = tick.review_needed
    report["reviewer_worker"] = reviewer_worker_tick_to_dict(tick)


def _attach_status_context(
    report: dict[str, object],
    *,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> None:
    """Attach status-side lifecycle context."""
    runtime_paths = _coerce_runtime_paths(paths)

    report["publisher"] = _read_publisher_state_safe(runtime_paths)
    report["reviewer_supervisor"] = _read_reviewer_supervisor_state_safe(runtime_paths)

    _attach_backend_contract(report, repo_root=repo_root, paths=runtime_paths)

    if report.get("reviewer_worker") is None:
        _attach_reviewer_worker(
            report,
            repo_root=repo_root,
            bridge_path=runtime_paths.bridge_path,
        )


def _run_bridge_status(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
    extra_warnings: list[str] | None = None,
    report_execution_mode: str | None = None,
) -> tuple[dict, int]:
    """Run bridge-backed status and attach shared context."""
    runtime_paths = _coerce_runtime_paths(paths)
    report, exit_code = _run_bridge_action(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        extra_warnings=extra_warnings,
        report_execution_mode=report_execution_mode,
    )

    _attach_status_context(report, repo_root=repo_root, paths=runtime_paths)
    return report, exit_code


def _spawn_follow_publisher(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> tuple[bool, int | None, str]:
    """Start the persistent ensure-follow publisher."""
    runtime_paths = _coerce_runtime_paths(paths)

    if runtime_paths.status_dir is None:
        return False, None, "status_dir not resolved"

    if runtime_paths.bridge_path is None:
        return False, None, "bridge_path not resolved"

    if runtime_paths.review_channel_path is None:
        return False, None, "review_channel_path not resolved"

    output_path = runtime_paths.status_dir / PUBLISHER_FOLLOW_OUTPUT_FILENAME
    log_path = runtime_paths.status_dir / PUBLISHER_FOLLOW_LOG_FILENAME
    log_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        str((repo_root / "dev/scripts/devctl.py").resolve()),
        *PUBLISHER_FOLLOW_COMMAND_ARGS,
        "--output",
        str(output_path),
        "--bridge-path",
        os.path.relpath(runtime_paths.bridge_path, repo_root),
        "--review-channel-path",
        os.path.relpath(runtime_paths.review_channel_path, repo_root),
        "--status-dir",
        os.path.relpath(runtime_paths.status_dir, repo_root),
    ]

    with log_path.open("a", encoding="utf-8") as handle:
        process = subprocess.Popen(
            command,
            cwd=repo_root,
            stdout=handle,
            stderr=handle,
            start_new_session=True,
        )
    return True, process.pid, str(log_path)


def _verify_detached_start(
    *,
    pid: int | None,
    paths: RuntimePaths | Mapping[str, object],
) -> str:
    """Record failed start when a detached publisher exits immediately."""
    from ..review_channel.lifecycle_state import _pid_is_alive

    if pid is not None and _pid_is_alive(pid):
        return "started"

    runtime_paths = _coerce_runtime_paths(paths)
    if runtime_paths.status_dir is not None:
        write_publisher_heartbeat(
            runtime_paths.status_dir,
            PublisherHeartbeat(
                pid=pid or 0,
                started_at_utc=utc_timestamp(),
                last_heartbeat_utc=utc_timestamp(),
                stopped_at_utc=utc_timestamp(),
                **FAILED_START_HEARTBEAT_FIELDS,
            ),
        )

    return "failed_start"


def _assess_publisher_lifecycle(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
    reviewer_mode_active: bool,
) -> PublisherLifecycleAssessment:
    """Assess publisher lifecycle for ensure."""
    from ..review_channel.peer_liveness import AttentionStatus

    runtime_paths = _coerce_runtime_paths(paths)
    publisher_state = _read_publisher_state_safe(runtime_paths)
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
        started, publisher_pid, publisher_log_path = _spawn_follow_publisher(
            args=args,
            repo_root=repo_root,
            paths=runtime_paths,
        )
        publisher_start_status = "started" if started else "failed"

        if started:
            for _ in range(10):
                time.sleep(0.1)
                publisher_state = _read_publisher_state_safe(runtime_paths)
                if bool(publisher_state.get("running")):
                    publisher_running = True
                    break

            if not publisher_running:
                publisher_start_status = _verify_detached_start(
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
        attention_override = AttentionStatus.PUBLISHER_FAILED_START.value
    elif stop_reason == "detached_exit":
        attention_override = AttentionStatus.PUBLISHER_DETACHED_EXIT.value
    else:
        attention_override = AttentionStatus.PUBLISHER_MISSING.value

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


def _build_ensure_bridge_status(report: dict[str, object]) -> EnsureBridgeStatus:
    """Extract the bridge-health subset used by ensure."""
    bridge_liveness = report.get("bridge_liveness", {})
    attention = report.get("attention", {})
    return EnsureBridgeStatus(
        reviewer_mode=str(bridge_liveness.get("reviewer_mode", "unknown")),
        codex_poll_state=str(bridge_liveness.get("codex_poll_state", "unknown")),
        heartbeat_age_seconds=bridge_liveness.get("last_codex_poll_age_seconds"),
        attention_status=str(attention.get("status", "unknown")),
        reviewer_worker=report.get("reviewer_worker"),
        reviewer_supervisor=report.get("reviewer_supervisor"),
        service_identity=report.get("service_identity"),
        attach_auth_policy=report.get("attach_auth_policy"),
    )


def _read_ensure_status(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> tuple[dict[str, object], EnsureBridgeStatus]:
    """Read status and its ensure view together."""
    report, _exit_code = _run_status_action(
        args=args,
        repo_root=repo_root,
        paths=paths,
    )
    return report, _build_ensure_bridge_status(report)


def _run_ensure_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> tuple[dict, int]:
    """Run the reviewer-heartbeat ensure flow."""
    runtime_paths = _coerce_runtime_paths(paths)

    if getattr(args, "follow", False):
        return _run_ensure_follow_action(
            args=args,
            repo_root=repo_root,
            paths=runtime_paths,
        )

    from ..review_channel.heartbeat import refresh_bridge_heartbeat
    from ..review_channel.peer_liveness import reviewer_mode_is_active

    report, bridge_state = _read_ensure_status(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
    )
    refreshed = False
    refresh_detail = None

    if (
        reviewer_mode_is_active(bridge_state.reviewer_mode)
        and bridge_state.codex_poll_state in ("stale", "missing")
    ):
        if runtime_paths.bridge_path is not None and runtime_paths.bridge_path.exists():
            try:
                refresh_result = refresh_bridge_heartbeat(
                    repo_root=repo_root,
                    bridge_path=runtime_paths.bridge_path,
                    reason="ensure",
                )
                refreshed = True
                refresh_detail = (
                    f"Heartbeat refreshed at {refresh_result.last_codex_poll_utc}"
                )

                report, bridge_state = _read_ensure_status(
                    args=args,
                    repo_root=repo_root,
                    paths=runtime_paths,
                )
            except (ValueError, OSError) as exc:
                refresh_detail = f"Heartbeat refresh failed: {exc}"

    pub = _assess_publisher_lifecycle(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        reviewer_mode_active=reviewer_mode_is_active(bridge_state.reviewer_mode),
    )
    attention_status = pub.attention_override or bridge_state.attention_status
    ensure_ok = bridge_state.heartbeat_ok and not (
        pub.publisher_required and not pub.publisher_running
    )

    detail_parts: list[str] = []

    if bridge_state.heartbeat_ok:
        detail_parts.append("Reviewer loop is healthy.")
    else:
        detail_parts.append(
            f"Reviewer loop needs attention: {attention_status} "
            f"(poll={bridge_state.codex_poll_state})."
        )

    if refresh_detail:
        detail_parts.append(refresh_detail)

    detail_parts.extend(pub.details)

    ensure_report = EnsureActionReport(
        command="review-channel",
        action="ensure",
        ok=ensure_ok,
        reviewer_mode=bridge_state.reviewer_mode,
        codex_poll_state=bridge_state.codex_poll_state,
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
        review_needed=(
            bool(bridge_state.reviewer_worker.get("review_needed"))
            if isinstance(bridge_state.reviewer_worker, dict)
            else None
        ),
        publisher_pid=pub.publisher_pid,
        publisher_log_path=pub.publisher_log_path,
        recommended_command=pub.recommended_command,
    )
    return ensure_report.to_report(), 0 if ensure_ok else 1


def _run_ensure_follow_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> tuple[dict, int]:
    """Run the persistent ensure-follow publisher."""
    runtime_paths = _coerce_runtime_paths(paths)
    return run_ensure_follow_action(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        deps=ENSURE_FOLLOW_DEPS,
    )


def _build_reviewer_state_report(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> tuple[dict, int]:
    """Build the current reviewer-state report."""
    runtime_paths = _coerce_runtime_paths(paths)
    assert runtime_paths.bridge_path is not None
    assert runtime_paths.review_channel_path is not None
    assert runtime_paths.status_dir is not None
    assert runtime_paths.promotion_plan_path is not None

    status_snapshot = refresh_status_snapshot(
        repo_root=repo_root,
        bridge_path=runtime_paths.bridge_path,
        review_channel_path=runtime_paths.review_channel_path,
        output_root=runtime_paths.status_dir,
        promotion_plan_path=runtime_paths.promotion_plan_path,
        execution_mode=args.execution_mode,
        warnings=[],
        errors=[],
    )

    codex_lanes = filter_provider_lanes(status_snapshot.lanes, provider="codex")
    claude_lanes = filter_provider_lanes(status_snapshot.lanes, provider="claude")
    report, exit_code = build_bridge_success_report(
        args=args,
        bridge_liveness=status_snapshot.bridge_liveness,
        attention=status_snapshot.attention,
        reviewer_worker=status_snapshot.reviewer_worker,
        codex_lanes=codex_lanes,
        claude_lanes=claude_lanes,
        warnings=status_snapshot.warnings,
        projection_paths=status_snapshot.projection_paths,
        **REVIEWER_STATE_REPORT_DEFAULTS,
    )

    _attach_backend_contract(report, repo_root=repo_root, paths=runtime_paths)
    return report, exit_code


def _run_reviewer_follow_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> tuple[dict, int]:
    """Poll reviewer-worker state on cadence."""
    runtime_paths = _coerce_runtime_paths(paths)
    return run_reviewer_follow_action(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
        deps=REVIEWER_FOLLOW_DEPS,
    )


def _run_reviewer_state_action(
    *,
    args,
    repo_root: Path,
    paths: RuntimePaths | Mapping[str, object],
) -> tuple[dict, int]:
    """Run one reviewer heartbeat/checkpoint write."""
    action = _coerce_action(args.action)
    runtime_paths = _coerce_runtime_paths(paths)

    if (
        action is ReviewChannelAction.REVIEWER_HEARTBEAT
        and getattr(args, "follow", False)
    ):
        return _run_reviewer_follow_action(
            args=args,
            repo_root=repo_root,
            paths=runtime_paths,
        )

    assert runtime_paths.bridge_path is not None

    if action is ReviewChannelAction.REVIEWER_HEARTBEAT:
        state_write = write_reviewer_heartbeat(
            repo_root=repo_root,
            bridge_path=runtime_paths.bridge_path,
            reviewer_mode=args.reviewer_mode,
            reason=args.reason,
        )
    else:
        state_write = write_reviewer_checkpoint(
            repo_root=repo_root,
            bridge_path=runtime_paths.bridge_path,
            reviewer_mode=args.reviewer_mode,
            reason=args.reason,
            checkpoint=ReviewerCheckpointUpdate(
                current_verdict=args.verdict,
                open_findings=args.open_findings,
                current_instruction=args.instruction,
                reviewed_scope_items=tuple(args.reviewed_scope_item),
            ),
        )

    report, exit_code = _build_reviewer_state_report(
        args=args,
        repo_root=repo_root,
        paths=runtime_paths,
    )

    report["reviewer_state_write"] = reviewer_state_write_to_dict(state_write)
    return report, exit_code


ENSURE_FOLLOW_DEPS = EnsureFollowDeps(
    ensure_reviewer_heartbeat_fn=lambda *a, **kw: ensure_reviewer_heartbeat(*a, **kw),
    reviewer_state_write_to_dict_fn=lambda *a, **kw: reviewer_state_write_to_dict(*a, **kw),
    run_status_action_fn=lambda *a, **kw: _run_status_action(*a, **kw),
    attach_reviewer_worker_fn=lambda *a, **kw: _attach_reviewer_worker(*a, **kw),
    emit_follow_ndjson_frame_fn=lambda *a, **kw: emit_follow_ndjson_frame(*a, **kw),
    reset_follow_output_fn=lambda *a, **kw: reset_follow_output(*a, **kw),
    build_follow_completion_report_fn=lambda *a, **kw: build_follow_completion_report(*a, **kw),
    build_follow_output_error_report_fn=lambda *a, **kw: build_follow_output_error_report(*a, **kw),
    write_publisher_heartbeat_fn=lambda *a, **kw: write_publisher_heartbeat(*a, **kw),
    read_publisher_state_fn=lambda *a, **kw: read_publisher_state(*a, **kw),
    utc_timestamp_fn=lambda: utc_timestamp(),
    sleep_fn=lambda seconds: time.sleep(seconds),
)
REVIEWER_FOLLOW_DEPS = ReviewerFollowDeps(
    ensure_reviewer_heartbeat_fn=lambda *a, **kw: ensure_reviewer_heartbeat(*a, **kw),
    build_reviewer_state_report_fn=lambda *a, **kw: _build_reviewer_state_report(*a, **kw),
    reviewer_state_write_to_dict_fn=lambda *a, **kw: reviewer_state_write_to_dict(*a, **kw),
    emit_follow_ndjson_frame_fn=lambda *a, **kw: emit_follow_ndjson_frame(*a, **kw),
    reset_follow_output_fn=lambda *a, **kw: reset_follow_output(*a, **kw),
    build_follow_completion_report_fn=lambda *a, **kw: build_follow_completion_report(*a, **kw),
    build_follow_output_error_report_fn=lambda *a, **kw: build_follow_output_error_report(*a, **kw),
    write_reviewer_supervisor_heartbeat_fn=lambda *a, **kw: write_reviewer_supervisor_heartbeat(*a, **kw),
    utc_timestamp_fn=lambda: utc_timestamp(),
    sleep_fn=lambda seconds: time.sleep(seconds),
)


def _dispatch_action(
    *,
    args,
    action: ReviewChannelAction,
    repo_root: Path,
    paths: RuntimePaths,
) -> tuple[dict, int]:
    """Dispatch one validated review-channel action."""
    if action is ReviewChannelAction.STATUS:
        return _run_status_action(args=args, repo_root=repo_root, paths=paths)

    if action in REVIEWER_STATE_ACTION_SET:
        return _run_reviewer_state_action(
            args=args,
            repo_root=repo_root,
            paths=paths,
        )

    if action in EVENT_ACTION_SET:
        return _run_event_action(args=args, repo_root=repo_root, paths=paths)

    if action is ReviewChannelAction.ENSURE:
        return _run_ensure_action(args=args, repo_root=repo_root, paths=paths)

    if action.value in BRIDGE_ACTIONS or action is ReviewChannelAction.PROMOTE:
        return _run_bridge_action(args=args, repo_root=repo_root, paths=paths)

    return _error_report(
        args,
        f"Unsupported review-channel action: {action.value}",
        exit_code=2,
    )


def _emit_report_output(args, report: dict[str, object], exit_code: int) -> int:
    """Emit one review-channel report."""
    already_emitted = bool(report.pop("_already_emitted", False))
    if already_emitted:
        return exit_code

    output = json.dumps(report, indent=2) if args.format == "json" else _render_report(report)
    pipe_rc = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
    )
    if pipe_rc != 0:
        return pipe_rc

    return exit_code


def run(args) -> int:
    """Run one review-channel action."""
    repo_root = REPO_ROOT.resolve()

    try:
        action = _coerce_action(getattr(args, "action", None))
        _validate_args(args, action)
        paths = _resolve_runtime_paths(args, repo_root)
        report, exit_code = _dispatch_action(
            args=args,
            action=action,
            repo_root=repo_root,
            paths=paths,
        )
    except ValueError as exc:
        report, exit_code = _error_report(args, str(exc), exit_code=1)
    except subprocess.CalledProcessError as exc:
        report, exit_code = _error_report(
            args,
            f"launcher subprocess failed: {exc}",
            exit_code=1,
        )
    except OSError as exc:
        report, exit_code = _error_report(args, str(exc), exit_code=1)

    return _emit_report_output(args, report, exit_code)
