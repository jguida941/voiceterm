"""Host-side repo process audit command."""

from __future__ import annotations

import json

from ...common import emit_output, pipe_output, write_output
from ...config import REPO_ROOT
from ...process_sweep.core import (
    DEFAULT_ORPHAN_MIN_AGE_SECONDS,
    DEFAULT_STALE_MIN_AGE_SECONDS,
    extend_process_row_markdown,
    format_process_rows,
    scan_repo_hygiene_process_tree,
    split_orphaned_processes,
    split_stale_processes,
)
from ...process_sweep.review_channel_monitors import (
    review_channel_monitor_pids,
    review_channel_monitor_rows,
)
from ...time_utils import utc_timestamp
from ..check.process_sweep import _protected_registered_conductor_pids

PROCESS_LINE_MAX_LEN = 180
PROCESS_REPORT_LIMIT = 12
BLOCKING_SCOPES = {"voiceterm", "repo_runtime"}
SUPERVISED_CONDUCTOR_SCOPE = "review_channel_conductor"


def _is_sandbox_ps_warning(message: str) -> bool:
    lowered = message.lower()
    return "unable to execute ps" in lowered and "operation not permitted" in lowered


def collect_process_audit_state() -> dict:
    """Collect one host process snapshot and categorize repo-related rows."""
    rows, scan_warnings = scan_repo_hygiene_process_tree()
    protected_conductor_pids = _protected_registered_conductor_pids(
        rows=rows,
        repo_root=REPO_ROOT,
    )
    # Registry-known PIDs are treated as supervised even when ppid=1
    # (headless script daemons intentionally reparent).  Q37 Phase 2
    # will tighten this further by requiring operator_last_interaction_utc
    # so registered-but-unattended sessions get surfaced as warnings.
    supervised_conductor_rows = [
        row
        for row in rows
        if row.get("match_scope") == SUPERVISED_CONDUCTOR_SCOPE
        and (row.get("ppid") != 1 or row.get("pid") in protected_conductor_pids)
    ]
    supervised_conductor_pids = {row["pid"] for row in supervised_conductor_rows}
    protected_monitor_pids = review_channel_monitor_pids(rows)
    active_review_channel_monitor_rows = review_channel_monitor_rows(rows)
    unprotected_rows = [
        row
        for row in rows
        if row.get("pid") not in supervised_conductor_pids | protected_monitor_pids
    ]
    orphaned, active = split_orphaned_processes(
        unprotected_rows,
        min_age_seconds=DEFAULT_ORPHAN_MIN_AGE_SECONDS,
    )
    stale_active, active_recent = split_stale_processes(
        active,
        min_age_seconds=DEFAULT_STALE_MIN_AGE_SECONDS,
    )
    recent_detached = [row for row in active_recent if row.get("ppid") == 1]
    active_recent_non_detached = [
        row for row in active_recent if row.get("pid") not in {item["pid"] for item in recent_detached}
    ]
    direct_matches = sum(
        1 for row in rows if row.get("match_source", "direct") == "direct"
    )
    active_recent_blocking = [
        row for row in active_recent_non_detached if row.get("match_scope") in BLOCKING_SCOPES
    ]
    active_recent_advisory = [
        row
        for row in active_recent_non_detached
        if row.get("match_scope") not in BLOCKING_SCOPES
    ]

    return {
        "rows": rows,
        "scan_warnings": scan_warnings,
        "orphaned_rows": orphaned,
        "stale_active_rows": stale_active,
        "active_recent_rows": active_recent,
        "active_supervised_conductor_rows": supervised_conductor_rows,
        "active_review_channel_monitor_rows": active_review_channel_monitor_rows,
        "recent_detached_rows": recent_detached,
        "active_recent_blocking_rows": active_recent_blocking,
        "active_recent_advisory_rows": active_recent_advisory,
        "direct_matches": direct_matches,
        "descendant_matches": len(rows) - direct_matches,
    }


def build_process_audit_report(*, strict: bool) -> dict:
    """Build the structured host-process audit report."""
    state = collect_process_audit_state()
    errors: list[str] = []
    warnings: list[str] = []

    for warning in state["scan_warnings"]:
        if _is_sandbox_ps_warning(warning):
            warnings.append(warning)
            continue
        errors.append(f"Host process audit unavailable: {warning}")

    orphaned = state["orphaned_rows"]
    stale_active = state["stale_active_rows"]
    active_recent = state["active_recent_rows"]
    supervised_conductors = state["active_supervised_conductor_rows"]
    active_review_channel_monitors = state["active_review_channel_monitor_rows"]
    recent_detached = state["recent_detached_rows"]
    active_recent_blocking = state["active_recent_blocking_rows"]
    active_recent_advisory = state["active_recent_advisory_rows"]

    if orphaned:
        errors.append(
            "Orphaned repo-related host processes detected: "
            + format_process_rows(
                orphaned,
                line_max_len=PROCESS_LINE_MAX_LEN,
                row_limit=PROCESS_REPORT_LIMIT,
            )
        )
    if stale_active:
        errors.append(
            "Stale active repo-related host processes detected: "
            + format_process_rows(
                stale_active,
                line_max_len=PROCESS_LINE_MAX_LEN,
                row_limit=PROCESS_REPORT_LIMIT,
            )
        )
    if recent_detached:
        detached_message = (
            "Recently detached repo-related host processes detected: "
            + format_process_rows(
                recent_detached,
                line_max_len=PROCESS_LINE_MAX_LEN,
                row_limit=PROCESS_REPORT_LIMIT,
            )
        )
        if strict:
            errors.append(detached_message)
        else:
            warnings.append(detached_message)
    if active_recent_blocking:
        active_message = (
            "Active runtime/test repo-related host processes are still running: "
            + format_process_rows(
                active_recent_blocking,
                line_max_len=PROCESS_LINE_MAX_LEN,
                row_limit=PROCESS_REPORT_LIMIT,
            )
        )
        if strict:
            errors.append(active_message)
        else:
            warnings.append(active_message)
    if active_recent_advisory:
        warnings.append(
            "Active repo-tooling host processes are still running: "
            + format_process_rows(
                active_recent_advisory,
                line_max_len=PROCESS_LINE_MAX_LEN,
                row_limit=PROCESS_REPORT_LIMIT,
            )
        )

    return {
        "command": "process-audit",
        "timestamp": utc_timestamp(),
        "strict": bool(strict),
        "rows": state["rows"],
        "orphaned_rows": orphaned,
        "stale_active_rows": stale_active,
        "active_recent_rows": active_recent,
        "active_supervised_conductor_rows": supervised_conductors,
        "active_review_channel_monitor_rows": active_review_channel_monitors,
        "recent_detached_rows": recent_detached,
        "active_recent_blocking_rows": active_recent_blocking,
        "active_recent_advisory_rows": active_recent_advisory,
        "total_detected": len(state["rows"]),
        "direct_matches": state["direct_matches"],
        "descendant_matches": state["descendant_matches"],
        "orphaned_count": len(orphaned),
        "stale_active_count": len(stale_active),
        "active_recent_count": len(active_recent),
        "active_supervised_conductor_count": len(supervised_conductors),
        "active_review_channel_monitor_count": len(active_review_channel_monitors),
        "recent_detached_count": len(recent_detached),
        "active_recent_blocking_count": len(active_recent_blocking),
        "active_recent_advisory_count": len(active_recent_advisory),
        "warnings": warnings,
        "errors": errors,
        "ok": not errors,
    }


def _render_md(report: dict) -> str:
    lines = ["# devctl process-audit", ""]
    lines.append(f"- strict: {report['strict']}")
    lines.append(f"- total_detected: {report['total_detected']}")
    lines.append(f"- direct_matches: {report['direct_matches']}")
    lines.append(f"- descendant_matches: {report['descendant_matches']}")
    lines.append(f"- orphaned: {report['orphaned_count']}")
    lines.append(f"- stale_active: {report['stale_active_count']}")
    lines.append(f"- active_recent: {report['active_recent_count']}")
    lines.append(
        "- active_supervised_conductors: "
        f"{report['active_supervised_conductor_count']}"
    )
    lines.append(
        "- active_review_channel_monitors: "
        f"{report['active_review_channel_monitor_count']}"
    )
    lines.append(f"- recent_detached: {report['recent_detached_count']}")
    lines.append(f"- active_recent_blocking: {report['active_recent_blocking_count']}")
    lines.append(f"- active_recent_advisory: {report['active_recent_advisory_count']}")
    lines.append(f"- ok: {report['ok']}")

    if report["rows"]:
        lines.append("")
        lines.append("## Detected Processes")
        extend_process_row_markdown(
            lines,
            report["rows"],
            row_limit=PROCESS_REPORT_LIMIT,
            overflow_label="processes",
        )

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

    return "\n".join(lines)


def run(args) -> int:
    """Audit host processes for leaked repo-related runtime/tooling trees."""
    report = build_process_audit_report(strict=bool(args.strict))

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
