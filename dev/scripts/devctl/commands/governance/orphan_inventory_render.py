"""Render helpers for devctl orphan-inventory."""

from __future__ import annotations

import json

from .orphan_inventory_parser import COMMAND_NAME


def render_report_output(report, *, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(report_payload(report), indent=2, sort_keys=True)

    return render_markdown(report)


def report_payload(report) -> dict[str, object]:
    return {
        "command": COMMAND_NAME,
        "ok": True,
        "report": report.to_dict(),
    }


def render_markdown(report) -> str:
    lines = summary_lines(report)
    lines.extend(warning_lines(report))
    lines.extend(source_lines(report))

    return "\n".join(lines)


def summary_lines(report) -> list[str]:
    return [
        "# orphan inventory",
        "",
        "- ok: True",
        f"- report_id: `{report.report_id}`",
        f"- generated_at_utc: `{report.generated_at_utc}`",
        f"- scan_scope: `{report.scan_scope}`",
        f"- report_only: {report.report_only}",
        f"- gates_evaluated: {report.gates_evaluated}",
        f"- checkout_rows: {len(report.checkout_inventory.rows)}",
        f"- total_sources: {report.stats.total_sources}",
        f"- unresolved_sources: {report.stats.unresolved_sources}",
        f"- load_bearing_sources: {report.stats.load_bearing_sources}",
    ]


def warning_lines(report) -> list[str]:
    if report.warnings:
        return ["", "## Warnings", *(f"- {warning}" for warning in report.warnings)]

    return []


def source_lines(report) -> list[str]:
    if not report.sources:
        return ["", "## Sources", "", "- none"]

    lines = [
        "",
        "## Sources",
        "",
        "| Kind | Status | Ref | Counts | Notes |",
        "|---|---|---|---|---|",
    ]
    lines.extend(source_row(source) for source in report.sources)

    return lines


def source_row(source) -> str:
    counts = source_counts(source)
    notes = "; ".join(source.classification.notes)

    return (
        "| "
        f"`{source.source_kind}` | `{source.status}` | "
        f"`{source.source_ref}` | {counts} | {notes} |"
    )


def source_counts(source) -> str:
    return (
        f"dirty={source.dirty_path_count}, "
        f"untracked={source.untracked_path_count}, "
        f"unpublished={len(source.unpublished_commit_shas)}"
    )


__all__ = ["render_report_output"]
