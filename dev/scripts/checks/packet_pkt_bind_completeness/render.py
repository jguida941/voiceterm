"""Markdown rendering for packet PKT-BIND completeness."""

from __future__ import annotations


def render_markdown(report: dict[str, object]) -> str:
    human_summary = report["human_summary"]
    lines = [
        "# check_packet_pkt_bind_completeness",
        "",
        f"- human_summary: {human_summary['headline']}",
    ]
    for conclusion in human_summary["conclusions"]:
        lines.append(f"- {conclusion}")
    lines.append("")
    for key in (
        "ok",
        "event_log_path",
        "plan_index_path",
        "mandate_packet_id",
        "grace_minutes",
        "strict_legacy",
        "task_started_count",
        "enforced_task_started_count",
        "legacy_task_started_count",
        "bound_task_started_count",
        "pending_within_grace_count",
        "violation_count",
        "legacy_gap_count",
    ):
        lines.append(f"- {key}: {report[key]}")
    _append_section(lines, "Errors", report.get("errors") or [])
    _append_packet_rows(lines, "Violations", report.get("violations") or [])
    _append_pending_rows(lines, report.get("pending_within_grace") or [])
    _append_packet_rows(lines, "Legacy Gaps", report.get("legacy_gaps") or [])
    return "\n".join(lines) + "\n"


def _append_section(lines: list[str], title: str, rows: object) -> None:
    if not rows:
        return
    lines.extend(["", f"## {title}"])
    lines.extend(f"- {row}" for row in rows)


def _append_packet_rows(lines: list[str], title: str, rows: object) -> None:
    if not rows:
        return
    lines.extend(["", f"## {title}"])
    for row in rows:
        lines.append(
            f"- line {row['line_number']} `{row['packet_id']}` "
            f"deadline={row['deadline_reason']} age={row['age_minutes']}m"
        )


def _append_pending_rows(lines: list[str], rows: object) -> None:
    if not rows:
        return
    lines.extend(["", "## Pending Within Grace"])
    for row in rows:
        lines.append(
            f"- line {row['line_number']} `{row['packet_id']}` "
            f"deadline={row['deadline_at_utc']}"
        )
