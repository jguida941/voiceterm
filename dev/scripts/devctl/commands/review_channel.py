"""`devctl review-channel` command implementation.

Orchestrates bridge-backed and event-backed review-channel actions. The
heavy rendering and execution logic lives in the dedicated handler modules:

- review_channel_bridge_handler: launch, rollover, promote, status (bridge)
- review_channel_event_handler: post, watch, inbox, ack, dismiss, apply, history
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from ..approval_mode import normalize_approval_mode
from ..common import emit_output
from ..config import REPO_ROOT
from ..review_channel.core import REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE
from ..review_channel.core import filter_provider_lanes
from ..review_channel.context_refs import resolve_context_pack_refs  # noqa: F401 -- re-exported for test patch targets
from ..review_channel.events import event_state_exists, resolve_artifact_paths
from ..review_channel.event_store import (
    build_bridge_status_fallback_warning,
    summarize_review_state_errors,
)
from ..review_channel.follow_stream import (
    build_follow_completion_report,
    build_follow_output_error_report,
    emit_follow_ndjson_frame,
    reset_follow_output,
    validate_follow_json_format,
)
from ..review_channel.promotion import DEFAULT_PROMOTION_PLAN_REL
from ..review_channel.reviewer_state import (
    ReviewerCheckpointUpdate,
    ensure_reviewer_heartbeat,
    reviewer_state_write_to_dict,
    write_reviewer_checkpoint,
    write_reviewer_heartbeat,
)
from ..review_channel.state import (
    PublisherHeartbeat,
    read_publisher_state,
    refresh_status_snapshot,
    write_publisher_heartbeat,
)
from ..time_utils import utc_timestamp

from .review_channel_bridge_handler import (
    BRIDGE_ACTIONS,
    _render_bridge_md,
    _run_bridge_action,
)
from .review_channel_bridge_render import build_bridge_success_report
from .review_channel_event_handler import _render_event_md, _run_event_action

EVENT_ACTIONS = {"post", "watch", "inbox", "ack", "dismiss", "apply", "history"}
REVIEWER_STATE_ACTIONS = {"reviewer-heartbeat", "reviewer-checkpoint"}
PUBLISHER_FOLLOW_OUTPUT_FILENAME = "publisher_follow.ndjson"
PUBLISHER_FOLLOW_LOG_FILENAME = "publisher_follow.log"


def _error_report(args, message: str, *, exit_code: int) -> tuple[dict, int]:
    """Build a structured error report for any review-channel failure."""
    report: dict[str, object] = {}
    report["command"] = "review-channel"
    report["timestamp"] = utc_timestamp()
    report["action"] = getattr(args, "action", None)
    report["ok"] = False
    report["exit_ok"] = False
    report["exit_code"] = exit_code
    report["execution_mode"] = getattr(args, "execution_mode", "auto")
    report["terminal"] = getattr(args, "terminal", "terminal-app")
    report["terminal_profile_requested"] = getattr(args, "terminal_profile", None)
    report["terminal_profile_applied"] = None
    report["approval_mode"] = normalize_approval_mode(
        getattr(args, "approval_mode", None),
        dangerous=bool(getattr(args, "dangerous", False)),
    )
    report["dangerous"] = bool(getattr(args, "dangerous", False))
    report["rollover_threshold_pct"] = getattr(args, "rollover_threshold_pct", None)
    report["rollover_trigger"] = getattr(args, "rollover_trigger", None)
    report["await_ack_seconds"] = getattr(args, "await_ack_seconds", None)
    report["retirement_note"] = REVIEW_CHANNEL_LAUNCH_RETIREMENT_NOTE
    report["errors"] = [message]
    report["warnings"] = []
    report["sessions"] = []
    report["handoff_bundle"] = None
    report["handoff_ack_required"] = False
    report["handoff_ack_observed"] = None
    report["bridge_liveness"] = None
    report["projection_paths"] = None
    report["artifact_paths"] = None
    report["packet"] = None
    report["packets"] = []
    report["history"] = []
    report["promotion"] = None
    report["bridge_heartbeat_refresh"] = None
    return report, exit_code


def _render_report(report: dict) -> str:
    """Route to the appropriate markdown renderer based on report mode."""
    if report.get("report_mode") == "event-backed":
        return _render_event_md(report)
    return _render_bridge_md(report)


def _event_report_error_detail(report: dict[str, object]) -> str:
    """Extract a concise error string from an event-backed report."""
    errors = report.get("errors")
    if isinstance(errors, list):
        messages = [str(error).strip() for error in errors if str(error).strip()]
        if messages:
            return "; ".join(messages)
    return "event-backed review-channel state was not ok"


def _validate_args(args) -> None:
    """Validate CLI arguments for the requested review-channel action."""
    rollover_threshold_pct = getattr(args, "rollover_threshold_pct", 50)
    await_ack_seconds = getattr(args, "await_ack_seconds", 0)
    limit = getattr(args, "limit", 20)
    stale_minutes = getattr(args, "stale_minutes", 30)
    expires_in_minutes = getattr(args, "expires_in_minutes", 30)
    if rollover_threshold_pct <= 0 or rollover_threshold_pct > 100:
        raise ValueError("--rollover-threshold-pct must be between 1 and 100.")
    if await_ack_seconds < 0:
        raise ValueError("--await-ack-seconds must be zero or greater.")
    if args.action == "rollover" and await_ack_seconds <= 0:
        raise ValueError(
            "--await-ack-seconds must be greater than zero for rollover so "
            "fresh-session ACK stays fail-closed."
        )
    if args.action == "post":
        if not getattr(args, "from_agent", None):
            raise ValueError("--from-agent is required for review-channel post.")
        if not getattr(args, "to_agent", None):
            raise ValueError("--to-agent is required for review-channel post.")
        if not getattr(args, "kind", None):
            raise ValueError("--kind is required for review-channel post.")
        if not getattr(args, "summary", None):
            raise ValueError("--summary is required for review-channel post.")
        if bool(getattr(args, "body", None)) == bool(getattr(args, "body_file", None)):
            raise ValueError(
                "Review-channel post requires exactly one of --body or --body-file."
            )
    if args.action in {"ack", "dismiss", "apply"}:
        if not getattr(args, "packet_id", None):
            raise ValueError(f"--packet-id is required for review-channel {args.action}.")
        if not getattr(args, "actor", None):
            raise ValueError(f"--actor is required for review-channel {args.action}.")
    if args.action == "reviewer-checkpoint":
        if not getattr(args, "verdict", None):
            raise ValueError("--verdict is required for review-channel reviewer-checkpoint.")
        if not getattr(args, "open_findings", None):
            raise ValueError("--open-findings is required for review-channel reviewer-checkpoint.")
        if not getattr(args, "instruction", None):
            raise ValueError("--instruction is required for review-channel reviewer-checkpoint.")
        if not getattr(args, "reviewed_scope_item", None):
            raise ValueError(
                "--reviewed-scope-item is required for review-channel reviewer-checkpoint."
            )
    if args.action in {"inbox", "watch", "history"} and limit <= 0:
        raise ValueError("--limit must be greater than zero.")
    if getattr(args, "max_follow_snapshots", 0) < 0:
        raise ValueError("--max-follow-snapshots must be zero or greater.")
    if getattr(args, "follow_interval_seconds", 120) <= 0:
        raise ValueError("--follow-interval-seconds must be greater than zero.")
    if getattr(args, "start_publisher_if_missing", False) and args.action != "ensure":
        raise ValueError("--start-publisher-if-missing is only valid for review-channel ensure.")
    if args.action in {"watch", "ensure"} and getattr(args, "follow", False):
        validate_follow_json_format(
            action=args.action,
            output_format=getattr(args, "format", "json"),
        )
    if stale_minutes <= 0:
        raise ValueError("--stale-minutes must be greater than zero.")
    if expires_in_minutes <= 0:
        raise ValueError("--expires-in-minutes must be greater than zero.")


def _resolve_runtime_paths(args, repo_root: Path) -> dict[str, object]:
    """Resolve all filesystem paths from CLI arguments and repo root."""
    script_dir = None
    if getattr(args, "script_dir", None):
        script_dir = (repo_root / args.script_dir).resolve()
    promotion_plan_rel = getattr(args, "promotion_plan", None) or DEFAULT_PROMOTION_PLAN_REL
    artifact_paths = resolve_artifact_paths(
        repo_root=repo_root,
        artifact_root_rel=getattr(args, "artifact_root", None),
        state_json_rel=getattr(args, "state_json", None),
        projections_dir_rel=getattr(args, "emit_projections", None),
    )
    paths: dict[str, object] = {}
    paths["review_channel_path"] = (repo_root / args.review_channel_path).resolve()
    paths["bridge_path"] = (repo_root / args.bridge_path).resolve()
    paths["rollover_dir"] = (repo_root / args.rollover_dir).resolve()
    paths["status_dir"] = (repo_root / args.status_dir).resolve()
    paths["promotion_plan_path"] = (repo_root / promotion_plan_rel).resolve()
    paths["script_dir"] = script_dir
    paths["artifact_paths"] = artifact_paths
    return paths


def _run_status_action(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
) -> tuple[dict, int]:
    """Run the status action with event-backed fallback to bridge-backed mode."""
    artifact_paths = paths["artifact_paths"]
    execution_mode = getattr(args, "execution_mode", "auto")
    fallback_warnings: list[str] = []
    if execution_mode != "markdown-bridge" and event_state_exists(artifact_paths):
        try:
            report, exit_code = _run_event_action(
                args=args,
                repo_root=repo_root,
                paths=paths,
            )
        except (OSError, ValueError) as exc:
            fallback_warnings.append(build_bridge_status_fallback_warning(str(exc)))
        else:
            state_errors = summarize_review_state_errors(
                {"ok": report.get("ok"), "errors": report.get("errors")}
            )
            if exit_code == 0 and state_errors is None:
                report["publisher"] = _read_publisher_state_safe(paths)
                return report, exit_code
            fallback_warnings.append(
                build_bridge_status_fallback_warning(
                    state_errors or _event_report_error_detail(report)
                )
            )
    if not fallback_warnings:
        report, exit_code = _run_bridge_action(
            args=args, repo_root=repo_root, paths=paths,
        )
        report["publisher"] = _read_publisher_state_safe(paths)
        return report, exit_code
    try:
        report, exit_code = _run_bridge_action(
            args=args,
            repo_root=repo_root,
            paths=paths,
            extra_warnings=fallback_warnings,
            report_execution_mode="markdown-bridge",
        )
        report["publisher"] = _read_publisher_state_safe(paths)
        return report, exit_code
    except ValueError as exc:
        raise ValueError(
            f"{fallback_warnings[-1]} Markdown-bridge fallback was unavailable: {exc}"
        ) from exc


def _read_publisher_state_safe(paths: dict[str, object]) -> dict[str, object]:
    """Read publisher state without failing the status report."""
    status_dir = paths.get("status_dir")
    if not isinstance(status_dir, Path):
        return {"running": False, "detail": "status_dir not resolved"}
    try:
        return read_publisher_state(status_dir)
    except (OSError, ValueError):
        return {"running": False, "detail": "publisher state read failed"}


def _publisher_follow_command() -> str:
    """Return the canonical command for the persistent publisher loop."""
    return (
        "python3 dev/scripts/devctl.py review-channel --action ensure --follow "
        "--terminal none --format json"
    )


def _spawn_follow_publisher(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
) -> tuple[bool, int | None, str]:
    """Start the persistent ensure-follow publisher in the background."""
    status_dir = paths.get("status_dir")
    bridge_path = paths.get("bridge_path")
    review_channel_path = paths.get("review_channel_path")
    if not isinstance(status_dir, Path):
        return False, None, "status_dir not resolved"
    if not isinstance(bridge_path, Path):
        return False, None, "bridge_path not resolved"
    if not isinstance(review_channel_path, Path):
        return False, None, "review_channel_path not resolved"

    output_path = status_dir / PUBLISHER_FOLLOW_OUTPUT_FILENAME
    log_path = status_dir / PUBLISHER_FOLLOW_LOG_FILENAME
    log_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str((repo_root / "dev/scripts/devctl.py").resolve()),
        "review-channel",
        "--action",
        "ensure",
        "--follow",
        "--terminal",
        "none",
        "--format",
        "json",
        "--output",
        str(output_path),
        "--bridge-path",
        os.path.relpath(bridge_path, repo_root),
        "--review-channel-path",
        os.path.relpath(review_channel_path, repo_root),
        "--status-dir",
        os.path.relpath(status_dir, repo_root),
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


def _assess_publisher_lifecycle(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
    reviewer_mode_active: bool,
) -> dict[str, object]:
    """Check publisher lifecycle and optionally start if missing."""
    from ..review_channel.peer_liveness import AttentionStatus

    publisher_state = _read_publisher_state_safe(paths)
    publisher_running = bool(publisher_state.get("running"))
    result: dict[str, object] = {
        "publisher_state": publisher_state,
        "publisher_running": publisher_running,
        "publisher_required": reviewer_mode_active,
        "publisher_status": "inactive_mode",
        "publisher_start_status": "not_attempted",
        "publisher_pid": None,
        "publisher_log_path": None,
        "recommended_command": None,
        "attention_override": None,
        "details": [],
    }
    if not reviewer_mode_active:
        result["details"].append(
            "Persistent publisher is not required while reviewer mode is inactive."
        )
        return result
    if not publisher_running and bool(getattr(args, "start_publisher_if_missing", False)):
        started, pid, log_path = _spawn_follow_publisher(
            args=args, repo_root=repo_root, paths=paths,
        )
        result["publisher_start_status"] = "started" if started else "failed"
        result["publisher_pid"] = pid
        result["publisher_log_path"] = log_path
        if started:
            for _ in range(10):
                time.sleep(0.1)
                publisher_state = _read_publisher_state_safe(paths)
                if bool(publisher_state.get("running")):
                    publisher_running = True
                    break
            result["publisher_state"] = publisher_state
            result["publisher_running"] = publisher_running
            result["details"].append("Persistent publisher start was requested.")
        else:
            result["details"].append(
                "Persistent publisher start failed before launch confirmation."
            )
    if publisher_running:
        result["publisher_status"] = "running"
        result["details"].append("Persistent publisher is running.")
    else:
        result["publisher_status"] = "not_running"
        result["attention_override"] = AttentionStatus.PUBLISHER_MISSING
        if result["publisher_start_status"] != "started":
            result["recommended_command"] = _publisher_follow_command()
        result["details"].append(
            "Persistent publisher is not running; start the follow publisher."
        )
    return result


def _run_ensure_action(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
) -> tuple[dict, int]:
    """Controller-owned reviewer heartbeat ensure: check, refresh if stale, report."""
    if getattr(args, "follow", False):
        return _run_ensure_follow_action(
            args=args, repo_root=repo_root, paths=paths,
        )
    from ..review_channel.heartbeat import refresh_bridge_heartbeat
    from ..review_channel.peer_liveness import reviewer_mode_is_active

    report, _exit_code = _run_status_action(
        args=args, repo_root=repo_root, paths=paths,
    )
    bridge_liveness = report.get("bridge_liveness", {})
    reviewer_mode = str(bridge_liveness.get("reviewer_mode", "unknown"))
    codex_poll_state = str(bridge_liveness.get("codex_poll_state", "unknown"))
    age = bridge_liveness.get("last_codex_poll_age_seconds")
    attention = report.get("attention", {})
    attention_status = str(attention.get("status", "unknown"))

    refreshed = False
    refresh_detail = None
    if (
        reviewer_mode_is_active(reviewer_mode)
        and codex_poll_state in ("stale", "missing")
    ):
        bridge_path = paths.get("bridge_path")
        if isinstance(bridge_path, Path) and bridge_path.exists():
            try:
                refresh_result = refresh_bridge_heartbeat(
                    repo_root=repo_root, bridge_path=bridge_path, reason="ensure",
                )
                refreshed = True
                refresh_detail = (
                    f"Heartbeat refreshed at {refresh_result.last_codex_poll_utc}"
                )
                report, _exit_code = _run_status_action(
                    args=args, repo_root=repo_root, paths=paths,
                )
                bridge_liveness = report.get("bridge_liveness", {})
                codex_poll_state = str(bridge_liveness.get("codex_poll_state", "unknown"))
                age = bridge_liveness.get("last_codex_poll_age_seconds")
                attention = report.get("attention", {})
                attention_status = str(attention.get("status", "unknown"))
            except (ValueError, OSError) as exc:
                refresh_detail = f"Heartbeat refresh failed: {exc}"

    heartbeat_ok = codex_poll_state in ("fresh", "poll_due")
    pub = _assess_publisher_lifecycle(
        args=args, repo_root=repo_root, paths=paths,
        reviewer_mode_active=reviewer_mode_is_active(reviewer_mode),
    )
    if pub["attention_override"]:
        attention_status = str(pub["attention_override"])
    ensure_ok = heartbeat_ok and not (pub["publisher_required"] and not pub["publisher_running"])

    detail_parts = []
    if heartbeat_ok:
        detail_parts.append("Reviewer loop is healthy.")
    else:
        detail_parts.append(
            f"Reviewer loop needs attention: {attention_status} "
            f"(poll={codex_poll_state})."
        )
    if refresh_detail:
        detail_parts.append(refresh_detail)
    detail_parts.extend(pub["details"])

    result: dict[str, object] = {}
    result["command"] = "review-channel"
    result["action"] = "ensure"
    result["ok"] = ensure_ok
    result["reviewer_mode"] = reviewer_mode
    result["codex_poll_state"] = codex_poll_state
    result["heartbeat_age_seconds"] = age
    result["attention_status"] = attention_status
    result["refreshed"] = refreshed
    result["publisher"] = pub["publisher_state"]
    result["publisher_required"] = pub["publisher_required"]
    result["publisher_status"] = pub["publisher_status"]
    result["publisher_start_status"] = pub["publisher_start_status"]
    if pub["publisher_pid"] is not None:
        result["publisher_pid"] = pub["publisher_pid"]
    if pub["publisher_log_path"] is not None:
        result["publisher_log_path"] = pub["publisher_log_path"]
    if pub["recommended_command"] is not None:
        result["recommended_command"] = pub["recommended_command"]
    result["detail"] = " ".join(detail_parts)
    return result, 0 if ensure_ok else 1


def _run_ensure_follow_action(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
) -> tuple[dict, int]:
    """Persistent heartbeat publisher: refresh + publish status on cadence.

    Each iteration reads the current reviewer mode from the bridge (not from a
    stale CLI arg), refreshes the heartbeat when mode is active, writes status
    projections through the normal status path, writes a publisher heartbeat
    file for lifecycle consumers, and emits an NDJSON frame.

    Supports ``--timeout-minutes`` for an absolute run budget. On exit (timeout,
    completion, or manual stop), writes final state with the stop reason.
    """
    bridge_path = paths.get("bridge_path")
    status_dir = paths.get("status_dir")
    assert isinstance(bridge_path, Path)
    interval_seconds = max(1, int(getattr(args, "follow_interval_seconds", 120)))
    max_snapshots = getattr(args, "max_follow_snapshots", 0) or 0
    timeout_minutes = getattr(args, "timeout_minutes", 0) or 0
    deadline = (time.monotonic() + timeout_minutes * 60) if timeout_minutes > 0 else 0
    publisher_pid = os.getpid()
    started_at = utc_timestamp()
    stop_reason = "completed"

    reset_follow_output(getattr(args, "output", None))
    emitted_count = 0
    seq = 0
    exit_code = 0
    last_mode = "unknown"

    try:
        while max_snapshots == 0 or emitted_count < max_snapshots:
            if deadline and time.monotonic() >= deadline:
                stop_reason = "timed_out"
                break
            emitted_count, seq, exit_code, last_mode, pipe_rc = _ensure_follow_tick(
                args=args, repo_root=repo_root, paths=paths,
                bridge_path=bridge_path, status_dir=status_dir,
                publisher_pid=publisher_pid, started_at=started_at,
                emitted_count=emitted_count, seq=seq,
            )
            if pipe_rc != 0:
                stop_reason = "output_error"
                _write_final_publisher_state(
                    status_dir, publisher_pid, started_at, emitted_count,
                    last_mode, stop_reason,
                )
                return build_follow_output_error_report(
                    action="ensure",
                    snapshots_emitted=emitted_count,
                    pipe_rc=pipe_rc,
                ), pipe_rc
            if max_snapshots != 0 and emitted_count >= max_snapshots:
                break
            if deadline and time.monotonic() >= deadline:
                stop_reason = "timed_out"
                break
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        stop_reason = "manual_stop"

    _write_final_publisher_state(
        status_dir, publisher_pid, started_at, emitted_count,
        last_mode, stop_reason,
    )
    result = build_follow_completion_report(
        action="ensure",
        snapshots_emitted=emitted_count,
        ok=exit_code == 0,
        reviewer_mode=last_mode,
    )
    result["stop_reason"] = stop_reason
    return result, exit_code


def _ensure_follow_tick(
    *,
    args, repo_root: Path, paths: dict[str, object],
    bridge_path: Path, status_dir: Path | object,
    publisher_pid: int, started_at: str,
    emitted_count: int, seq: int,
) -> tuple[int, int, int, str, int]:
    """Run one ensure-follow iteration and return updated counters + pipe rc."""
    ensure_result = ensure_reviewer_heartbeat(
        repo_root=repo_root,
        bridge_path=bridge_path,
        reason="ensure-follow",
    )
    last_mode = ensure_result.reviewer_mode
    report, exit_code = _run_status_action(
        args=args, repo_root=repo_root, paths=paths,
    )
    if ensure_result.state_write is not None:
        report["reviewer_state_write"] = reviewer_state_write_to_dict(
            ensure_result.state_write,
        )
    report["ensure_refreshed"] = ensure_result.refreshed
    if isinstance(status_dir, Path):
        write_publisher_heartbeat(
            status_dir,
            PublisherHeartbeat(
                pid=publisher_pid,
                started_at_utc=started_at,
                last_heartbeat_utc=utc_timestamp(),
                snapshots_emitted=emitted_count + 1,
                reviewer_mode=last_mode,
            ),
        )
        publisher_state = read_publisher_state(status_dir)
        report["publisher"] = publisher_state
    frame = dict(report)
    frame["follow"] = True
    frame["snapshot_seq"] = seq
    pipe_rc = emit_follow_ndjson_frame(frame, args=args)
    if pipe_rc != 0:
        return emitted_count, seq, exit_code, last_mode, pipe_rc
    return emitted_count + 1, seq + 1, exit_code, last_mode, 0


def _write_final_publisher_state(
    status_dir: Path | object,
    publisher_pid: int,
    started_at: str,
    snapshots_emitted: int,
    reviewer_mode: str,
    stop_reason: str,
) -> None:
    """Write a final publisher heartbeat with the stop reason."""
    if not isinstance(status_dir, Path):
        return
    write_publisher_heartbeat(
        status_dir,
        PublisherHeartbeat(
            pid=publisher_pid,
            started_at_utc=started_at,
            last_heartbeat_utc=utc_timestamp(),
            snapshots_emitted=snapshots_emitted,
            reviewer_mode=reviewer_mode,
            stop_reason=stop_reason,
            stopped_at_utc=utc_timestamp(),
        ),
    )


def _run_reviewer_state_action(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
) -> tuple[dict, int]:
    """Run one repo-owned reviewer heartbeat/checkpoint write and refresh projections."""
    bridge_path = paths["bridge_path"]
    review_channel_path = paths["review_channel_path"]
    status_dir = paths["status_dir"]
    promotion_plan_path = paths["promotion_plan_path"]
    assert isinstance(bridge_path, Path)
    assert isinstance(review_channel_path, Path)
    assert isinstance(status_dir, Path)
    assert isinstance(promotion_plan_path, Path)

    if args.action == "reviewer-heartbeat":
        state_write = write_reviewer_heartbeat(
            repo_root=repo_root,
            bridge_path=bridge_path,
            reviewer_mode=args.reviewer_mode,
            reason=args.reason,
        )
    else:
        state_write = write_reviewer_checkpoint(
            repo_root=repo_root,
            bridge_path=bridge_path,
            reviewer_mode=args.reviewer_mode,
            reason=args.reason,
            checkpoint=ReviewerCheckpointUpdate(
                current_verdict=args.verdict,
                open_findings=args.open_findings,
                current_instruction=args.instruction,
                reviewed_scope_items=tuple(args.reviewed_scope_item),
            ),
        )

    status_snapshot = refresh_status_snapshot(
        repo_root=repo_root,
        bridge_path=bridge_path,
        review_channel_path=review_channel_path,
        output_root=status_dir,
        promotion_plan_path=promotion_plan_path,
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
        codex_lanes=codex_lanes,
        claude_lanes=claude_lanes,
        terminal_profile_applied=None,
        warnings=status_snapshot.warnings,
        sessions=[],
        handoff_bundle=None,
        projection_paths=status_snapshot.projection_paths,
        launched=False,
        handoff_ack_required=False,
        handoff_ack_observed=None,
        promotion=None,
        bridge_heartbeat_refresh=None,
        execution_mode_override="markdown-bridge",
    )
    report["reviewer_state_write"] = reviewer_state_write_to_dict(state_write)
    return report, exit_code


def run(args) -> int:
    """Run one review-channel action."""
    repo_root = REPO_ROOT.resolve()
    already_emitted = False
    try:
        _validate_args(args)
        paths = _resolve_runtime_paths(args, repo_root)
        if args.action == "status":
            report, exit_code = _run_status_action(
                args=args,
                repo_root=repo_root,
                paths=paths,
            )
        elif args.action in REVIEWER_STATE_ACTIONS:
            report, exit_code = _run_reviewer_state_action(
                args=args,
                repo_root=repo_root,
                paths=paths,
            )
        elif args.action in EVENT_ACTIONS:
            report, exit_code = _run_event_action(
                args=args,
                repo_root=repo_root,
                paths=paths,
            )
        elif args.action == "ensure":
            report, exit_code = _run_ensure_action(
                args=args,
                repo_root=repo_root,
                paths=paths,
            )
        elif args.action in BRIDGE_ACTIONS or args.action == "promote":
            report, exit_code = _run_bridge_action(
                args=args,
                repo_root=repo_root,
                paths=paths,
            )
        else:
            report, exit_code = _error_report(
                args,
                f"Unsupported review-channel action: {args.action}",
                exit_code=2,
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

    if isinstance(report, dict):
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
