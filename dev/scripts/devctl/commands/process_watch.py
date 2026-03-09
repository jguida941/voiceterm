"""Periodic host-side repo process audit/cleanup watch command."""

from __future__ import annotations

import json
import time

from ..common import emit_output, pipe_output, write_output
from ..time_utils import utc_timestamp
from .process_audit import build_process_audit_report
from .process_cleanup import build_process_cleanup_report

FATAL_WATCH_ERROR_PREFIXES = (
    "Host process audit unavailable:",
    "Host process cleanup unavailable:",
    "Host process cleanup warning:",
)


def _is_fatal_watch_error(message: str) -> bool:
    return str(message).startswith(FATAL_WATCH_ERROR_PREFIXES)


def _iteration_message(iteration: int, message: str) -> str:
    return f"iteration {iteration}: {message}"


def _extend_iteration_messages(
    bucket: list[str],
    *,
    iteration: int,
    messages: list[str],
) -> None:
    bucket.extend(_iteration_message(iteration, str(message)) for message in messages)


def _collect_fatal_iteration_errors(
    *,
    iteration: int,
    messages: list[str],
) -> list[str]:
    return [
        _iteration_message(iteration, str(message))
        for message in messages
        if _is_fatal_watch_error(str(message))
    ]


def _render_md(report: dict) -> str:
    lines = ["# devctl process-watch", ""]
    lines.append(f"- cleanup: {report['cleanup']}")
    lines.append(f"- strict: {report['strict']}")
    lines.append(f"- iterations_requested: {report['iterations_requested']}")
    lines.append(f"- iterations_run: {report['iterations_run']}")
    lines.append(f"- interval_seconds: {report['interval_seconds']}")
    lines.append(f"- stop_on_clean: {report['stop_on_clean']}")
    lines.append(f"- stop_reason: {report['stop_reason']}")
    lines.append(f"- ok: {report['ok']}")

    if report["iterations"]:
        lines.append("")
        lines.append("| Iteration | Cleanup targets | Killed | Detected | Orphaned | Stale | Active recent | OK |")
        lines.append("|---:|---:|---:|---:|---:|---:|---:|---|")
        for item in report["iterations"]:
            lines.append(
                "| "
                f"{item['iteration']} | "
                f"{item['cleanup_target_count']} | "
                f"{item['killed_count']} | "
                f"{item['total_detected']} | "
                f"{item['orphaned_count']} | "
                f"{item['stale_active_count']} | "
                f"{item['active_recent_count']} | "
                f"{item['ok']} |"
            )

    if report["warnings"]:
        lines.append("")
        lines.append("## Warnings" if not report["ok"] else "## Watch Warnings")
        for warning in report["warnings"]:
            lines.append(f"- {warning}")

    if report["errors"]:
        lines.append("")
        lines.append("## Errors" if not report["ok"] else "## Watch History")
        for error in report["errors"]:
            lines.append(f"- {error}")

    return "\n".join(lines)


def _iteration_summary(*, iteration: int, audit_report: dict, cleanup_report: dict | None) -> dict:
    return {
        "iteration": iteration,
        "cleanup_target_count": (
            cleanup_report["cleanup_target_count"] if cleanup_report is not None else 0
        ),
        "killed_count": cleanup_report["killed_count"] if cleanup_report is not None else 0,
        "total_detected": audit_report["total_detected"],
        "orphaned_count": audit_report["orphaned_count"],
        "stale_active_count": audit_report["stale_active_count"],
        "active_recent_count": audit_report["active_recent_count"],
        "ok": audit_report["ok"],
        "cleanup_report": cleanup_report,
        "audit_report": audit_report,
    }


def run(args) -> int:
    """Periodically audit host repo-related processes and optionally clean leaks."""
    iterations_requested = max(1, int(args.iterations))
    interval_seconds = max(0.0, float(args.interval_seconds))
    cleanup_enabled = bool(args.cleanup)
    strict = bool(args.strict)
    stop_on_clean = bool(args.stop_on_clean)

    iterations: list[dict] = []
    warnings: list[str] = []
    errors: list[str] = []
    fatal_errors: list[str] = []
    stop_reason = "max_iterations_reached"

    for iteration in range(1, iterations_requested + 1):
        cleanup_report = None
        if cleanup_enabled:
            cleanup_report = build_process_cleanup_report(dry_run=False, verify=False)
            _extend_iteration_messages(
                warnings,
                iteration=iteration,
                messages=list(cleanup_report.get("warnings", [])),
            )
            cleanup_messages = list(cleanup_report.get("errors", []))
            _extend_iteration_messages(
                errors,
                iteration=iteration,
                messages=cleanup_messages,
            )
            fatal_errors.extend(
                _collect_fatal_iteration_errors(
                    iteration=iteration,
                    messages=cleanup_messages,
                )
            )

        audit_report = build_process_audit_report(strict=strict)
        _extend_iteration_messages(
            warnings,
            iteration=iteration,
            messages=list(audit_report.get("warnings", [])),
        )
        audit_messages = list(audit_report.get("errors", []))
        _extend_iteration_messages(
            errors,
            iteration=iteration,
            messages=audit_messages,
        )
        fatal_errors.extend(
            _collect_fatal_iteration_errors(
                iteration=iteration,
                messages=audit_messages,
            )
        )
        iterations.append(
            _iteration_summary(
                iteration=iteration,
                audit_report=audit_report,
                cleanup_report=cleanup_report,
            )
        )

        if (
            stop_on_clean
            and int(audit_report.get("total_detected", 0)) == 0
            and audit_report.get("ok", False)
        ):
            stop_reason = "clean"
            break
        if iteration < iterations_requested and interval_seconds > 0:
            time.sleep(interval_seconds)

    final_audit = (
        iterations[-1]["audit_report"]
        if iterations
        else build_process_audit_report(strict=strict)
    )
    report = {
        "command": "process-watch",
        "timestamp": utc_timestamp(),
        "cleanup": cleanup_enabled,
        "strict": strict,
        "iterations_requested": iterations_requested,
        "iterations_run": len(iterations),
        "interval_seconds": interval_seconds,
        "stop_on_clean": stop_on_clean,
        "stop_reason": stop_reason,
        "iterations": iterations,
        "final_audit": final_audit,
        "warnings": warnings,
        "errors": errors,
        "fatal_errors": fatal_errors,
        "ok": final_audit.get("ok", False) and not fatal_errors,
    }

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
