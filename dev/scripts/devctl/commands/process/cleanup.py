"""Host-side repo process cleanup command."""

from __future__ import annotations

import json
import signal
from dataclasses import asdict, dataclass
from typing import Any

from ...common import emit_output, pipe_output, write_output
from ...process_sweep.core import (
    DEFAULT_STALE_MIN_AGE_SECONDS,
    expand_cleanup_target_rows,
    extend_process_row_markdown,
    kill_processes,
)
from ...time_utils import utc_timestamp
from .audit import (
    PROCESS_REPORT_LIMIT,
    SUPERVISED_CONDUCTOR_SCOPE,
    build_process_audit_report,
    collect_process_audit_state,
)


@dataclass(slots=True)
class StaleConductorRetirementResult:
    requested_pid: int
    signal: str
    target_count: int
    target_pids: list[int]
    target_rows: list[dict[str, Any]]
    killed_pids: list[int]
    recommended_followup: str


def _stale_conductor_retirement_commands(state: dict) -> list[str]:
    commands: list[str] = []
    for row in state.get("stale_supervised_conductor_rows", []):
        try:
            pid = int(row.get("pid", 0) or 0)
        except (TypeError, ValueError):
            continue
        if pid <= 0:
            continue
        if int(row.get("ppid", 0) or 0) != 1:
            continue
        commands.append(
            "python3 dev/scripts/devctl.py controller-action "
            f"--action retire-stale-conductor --pid {pid} --format md"
        )
    return commands


def _row_command(row: dict[str, Any]) -> str:
    return str(row.get("command") or row.get("cmd") or "").strip()


def _row_pid(row: dict[str, Any]) -> int:
    return int(row.get("pid", 0) or 0)


def _is_review_channel_conductor_row(row: dict[str, Any]) -> bool:
    if str(row.get("match_scope") or "") == SUPERVISED_CONDUCTOR_SCOPE:
        return True
    command = _row_command(row)
    return "-conductor.sh" in command and "__review_channel_inner" in command


def retire_stale_conductor(report: Any, args: Any) -> None:
    pid = int(args.pid or 0)
    if pid <= 0:
        report.reason = "pid_required"
        report.errors.append("--pid is required for retire-stale-conductor")
        return

    state = collect_process_audit_state()
    scan_warnings = [str(item) for item in state.get("scan_warnings", [])]
    if scan_warnings:
        report.reason = "process_audit_unavailable"
        report.errors.extend(scan_warnings)
        return

    rows = list(state.get("rows", []))
    target_row = next((row for row in rows if _row_pid(row) == pid), None)
    if target_row is None:
        report.reason = "conductor_pid_not_found"
        report.errors.append(f"pid {pid} was not present in process-audit rows")
        return
    if not _is_review_channel_conductor_row(target_row):
        report.reason = "target_not_review_channel_conductor"
        report.errors.append(
            f"pid {pid} is not classified as a review-channel conductor"
        )
        return

    elapsed_seconds = int(target_row.get("elapsed_seconds", -1) or -1)
    if elapsed_seconds >= 0 and elapsed_seconds < DEFAULT_STALE_MIN_AGE_SECONDS:
        report.reason = "conductor_not_stale"
        report.errors.append(
            f"pid {pid} age {elapsed_seconds}s is below the stale threshold "
            f"{DEFAULT_STALE_MIN_AGE_SECONDS}s"
        )
        return

    target_rows = expand_cleanup_target_rows(rows, [target_row]) or [target_row]
    killed_pids: list[int] = []
    kill_warnings: list[str] = []
    if not args.dry_run:
        killed_pids, kill_warnings = kill_processes(
            target_rows,
            kill_signal=signal.SIGTERM,
        )
    report.result = asdict(
        StaleConductorRetirementResult(
            requested_pid=pid,
            signal="SIGTERM",
            target_count=len(target_rows),
            target_pids=[_row_pid(row) for row in target_rows],
            target_rows=target_rows,
            killed_pids=killed_pids,
            recommended_followup=(
                "python3 dev/scripts/devctl.py process-cleanup --verify --format md"
            ),
        )
    )
    if kill_warnings:
        report.reason = "retire_stale_conductor_failed"
        report.errors.extend(kill_warnings)
        return
    report.ok = True
    report.reason = (
        "retire_stale_conductor_dry_run"
        if args.dry_run
        else "stale_conductor_retired"
    )


def _render_md(report: dict) -> str:
    lines = ["# devctl process-cleanup", ""]
    lines.append(f"- dry_run: {report['dry_run']}")
    lines.append(f"- verify: {report['verify']}")
    lines.append(f"- total_detected_pre: {report['total_detected_pre']}")
    lines.append(f"- orphaned_pre: {report['orphaned_count_pre']}")
    lines.append(f"- stale_active_pre: {report['stale_active_count_pre']}")
    lines.append(
        "- stale_supervised_conductors_pre: "
        f"{report['stale_supervised_conductor_count_pre']}"
    )
    lines.append(f"- active_recent_pre: {report['active_recent_count_pre']}")
    lines.append(f"- recent_detached_pre: {report['recent_detached_count_pre']}")
    lines.append(f"- cleanup_target_count: {report['cleanup_target_count']}")
    lines.append(f"- killed_count: {report['killed_count']}")
    lines.append(f"- verify_ok: {report['verify_ok']}")
    lines.append(f"- ok: {report['ok']}")

    if report["cleanup_target_rows"]:
        lines.append("")
        lines.append("## Cleanup Targets")
        extend_process_row_markdown(
            lines,
            report["cleanup_target_rows"],
            row_limit=PROCESS_REPORT_LIMIT,
            overflow_label="cleanup targets",
        )

    if report["skipped_recent_rows"]:
        lines.append("")
        lines.append("## Skipped Recent Active")
        extend_process_row_markdown(
            lines,
            report["skipped_recent_rows"],
            row_limit=PROCESS_REPORT_LIMIT,
            overflow_label="recent active processes",
        )

    if report["killed_pids"]:
        lines.append("")
        lines.append("## Killed PIDs")
        lines.append("- " + ", ".join(str(pid) for pid in report["killed_pids"]))

    if report["warnings"]:
        lines.append("")
        lines.append("## Warnings")
        for warning in report["warnings"]:
            lines.append(f"- {warning}")

    if report["stale_conductor_retirement_commands"]:
        lines.append("")
        lines.append("## Typed Conductor Retirement")
        for command in report["stale_conductor_retirement_commands"]:
            lines.append(f"- {command}")

    if report["errors"]:
        lines.append("")
        lines.append("## Errors")
        for error in report["errors"]:
            lines.append(f"- {error}")

    if report["verify_report"]:
        verify_report = report["verify_report"]
        lines.append("")
        lines.append("## Verify Report")
        lines.append(f"- total_detected: {verify_report['total_detected']}")
        lines.append(f"- orphaned: {verify_report['orphaned_count']}")
        lines.append(f"- stale_active: {verify_report['stale_active_count']}")
        lines.append(f"- active_recent: {verify_report['active_recent_count']}")
        lines.append(f"- ok: {verify_report['ok']}")
        for error in verify_report["errors"]:
            lines.append(f"- verify_error: {error}")
        for warning in verify_report["warnings"]:
            lines.append(f"- verify_warning: {warning}")

    return "\n".join(lines)


def _is_sandbox_ps_warning(message: str) -> bool:
    lowered = message.lower()
    return "unable to execute ps" in lowered and "operation not permitted" in lowered


def build_process_cleanup_report(*, dry_run: bool, verify: bool) -> dict:
    """Build the structured cleanup + optional verify report."""
    state = collect_process_audit_state()
    errors: list[str] = []
    warnings: list[str] = []
    verify_report: dict | None = None

    for warning in state["scan_warnings"]:
        if _is_sandbox_ps_warning(warning):
            warnings.append(warning)
            continue
        errors.append(f"Host process cleanup unavailable: {warning}")

    cleanup_target_rows = expand_cleanup_target_rows(
        state["rows"],
        [
            *state["orphaned_rows"],
            *state["stale_active_rows"],
            *state.get("stale_supervised_conductor_rows", []),
        ],
    )
    killed_pids: list[int] = []

    if not errors and cleanup_target_rows and not dry_run:
        killed_pids, kill_warnings = kill_processes(cleanup_target_rows)
        for warning in kill_warnings:
            errors.append(f"Host process cleanup warning: {warning}")

    cleanup_target_pids = {row["pid"] for row in cleanup_target_rows}
    skipped_recent_rows = [
        row
        for row in state["active_recent_rows"]
        if row["pid"] not in cleanup_target_pids
    ]
    recent_detached_rows = list(state.get("recent_detached_rows", []))
    stale_conductor_retirement_commands = (
        _stale_conductor_retirement_commands(state)
        if recent_detached_rows or state.get("stale_supervised_conductor_rows")
        else []
    )

    if recent_detached_rows:
        warning = (
            "Recent detached repo-related processes were not killed yet; rerun "
            "`process-watch --cleanup --strict --stop-on-clean --iterations 6 "
            "--interval-seconds 15 --format md` or rerun "
            "`process-cleanup --verify --format md` after the detached tree "
            "has had time to age out."
        )
        if stale_conductor_retirement_commands:
            warning += (
                " If a stale review-channel conductor is spawning fresh "
                "detached rows, retire the conductor through the typed "
                "controller-action listed in `stale_conductor_retirement_commands`."
            )
        warnings.append(warning)
    elif skipped_recent_rows:
        warnings.append(
            "Recent active repo-related processes were not killed; rerun "
            "`process-audit --strict` after expected local work finishes."
        )

    if verify:
        verify_report = build_process_audit_report(strict=True)
        if not verify_report["ok"]:
            errors.append("Host process cleanup verification failed.")

    return {
        "command": "process-cleanup",
        "timestamp": utc_timestamp(),
        "dry_run": bool(dry_run),
        "verify": bool(verify),
        "rows_pre": state["rows"],
        "orphaned_rows_pre": state["orphaned_rows"],
        "stale_active_rows_pre": state["stale_active_rows"],
        "stale_supervised_conductor_rows_pre": state.get(
            "stale_supervised_conductor_rows",
            [],
        ),
        "skipped_recent_rows": skipped_recent_rows,
        "total_detected_pre": len(state["rows"]),
        "orphaned_count_pre": len(state["orphaned_rows"]),
        "stale_active_count_pre": len(state["stale_active_rows"]),
        "stale_supervised_conductor_count_pre": len(
            state.get("stale_supervised_conductor_rows", [])
        ),
        "active_recent_count_pre": len(state["active_recent_rows"]),
        "recent_detached_count_pre": len(recent_detached_rows),
        "stale_conductor_retirement_commands": stale_conductor_retirement_commands,
        "cleanup_target_rows": cleanup_target_rows,
        "cleanup_target_count": len(cleanup_target_rows),
        "killed_pids": killed_pids,
        "killed_count": len(killed_pids),
        "warnings": warnings,
        "errors": errors,
        "verify_ok": verify_report["ok"] if verify_report is not None else not errors,
        "verify_report": verify_report,
        "ok": not errors,
    }


def run(args) -> int:
    """Clean orphaned/stale repo-related host process trees."""
    report = build_process_cleanup_report(
        dry_run=bool(getattr(args, "dry_run", False)),
        verify=bool(getattr(args, "verify", False)),
    )

    output = (
        json.dumps(report, indent=2) if args.format == "json" else _render_md(report)
    )
    pipe_rc = emit_output(
        output,
        output_path=args.output,
        pipe_command=args.pipe_command,
        pipe_args=args.pipe_args,
        writer=write_output,
        piper=pipe_output,
    )
    if pipe_rc != 0:
        return pipe_rc
    return 0 if report["ok"] else 1
