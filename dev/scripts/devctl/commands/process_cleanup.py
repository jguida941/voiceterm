"""Host-side repo process cleanup command."""

from __future__ import annotations

import json

from ..common import emit_output, pipe_output, write_output
from ..process_sweep import (
    expand_cleanup_target_rows,
    extend_process_row_markdown,
    kill_processes,
)
from ..time_utils import utc_timestamp
from .process_audit import (
    PROCESS_REPORT_LIMIT,
    build_process_audit_report,
    collect_process_audit_state,
)


def _render_md(report: dict) -> str:
    lines = ["# devctl process-cleanup", ""]
    lines.append(f"- dry_run: {report['dry_run']}")
    lines.append(f"- verify: {report['verify']}")
    lines.append(f"- total_detected_pre: {report['total_detected_pre']}")
    lines.append(f"- orphaned_pre: {report['orphaned_count_pre']}")
    lines.append(f"- stale_active_pre: {report['stale_active_count_pre']}")
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


def build_process_cleanup_report(*, dry_run: bool, verify: bool) -> dict:
    """Build the structured cleanup + optional verify report."""
    state = collect_process_audit_state()
    errors: list[str] = []
    warnings: list[str] = []
    verify_report: dict | None = None

    for warning in state["scan_warnings"]:
        errors.append(f"Host process cleanup unavailable: {warning}")

    cleanup_target_rows = expand_cleanup_target_rows(
        state["rows"],
        [*state["orphaned_rows"], *state["stale_active_rows"]],
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

    if recent_detached_rows:
        warnings.append(
            "Recent detached repo-related processes were not killed yet; rerun "
            "`process-watch --cleanup --strict --stop-on-clean --iterations 6 "
            "--interval-seconds 15 --format md` or rerun "
            "`process-cleanup --verify --format md` after the detached tree "
            "has had time to age out."
        )
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
        "skipped_recent_rows": skipped_recent_rows,
        "total_detected_pre": len(state["rows"]),
        "orphaned_count_pre": len(state["orphaned_rows"]),
        "stale_active_count_pre": len(state["stale_active_rows"]),
        "active_recent_count_pre": len(state["active_recent_rows"]),
        "recent_detached_count_pre": len(recent_detached_rows),
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
