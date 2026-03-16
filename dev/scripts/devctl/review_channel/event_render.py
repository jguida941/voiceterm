"""Markdown rendering helpers for event-backed review-channel actions."""

from __future__ import annotations

from ..review_channel.context_refs import (
    context_pack_ref_summary,
    normalize_context_pack_refs,
)

from ..commands.review_channel_bridge_render import append_common_report_sections


def render_event_md(report: dict) -> str:
    """Render a markdown summary for event-backed review-channel actions."""
    lines = ["# devctl review-channel", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- action: {report.get('action')}")
    lines.append(f"- execution_mode: {report.get('execution_mode')}")
    queue = report.get("queue") or {}
    lines.append(f"- pending_total: {queue.get('pending_total', 0)}")
    lines.append(f"- stale_packet_count: {queue.get('stale_packet_count', 0)}")
    if report.get("target"):
        lines.append(f"- target: {report.get('target')}")
    if report.get("status_filter"):
        lines.append(f"- status_filter: {report.get('status_filter')}")
    if report.get("limit") is not None:
        lines.append(f"- limit: {report.get('limit')}")
    append_common_report_sections(lines, report)
    packet = report.get("packet")
    if isinstance(packet, dict):
        lines.append("")
        lines.append("## Packet")
        lines.append(f"- packet_id: {packet.get('packet_id')}")
        lines.append(f"- trace_id: {packet.get('trace_id')}")
        lines.append(f"- route: {packet.get('from_agent')} -> {packet.get('to_agent')}")
        lines.append(f"- status: {packet.get('status')}")
        lines.append(f"- summary: {packet.get('summary')}")
        append_context_pack_ref_lines(
            lines,
            packet.get("context_pack_refs"),
            heading="- context_pack_refs:",
            indent="  ",
        )
    packets = report.get("packets")
    if isinstance(packets, list) and packets:
        lines.append("")
        lines.append("## Packets")
        for packet_row in packets:
            if not isinstance(packet_row, dict):
                continue
            summary = (
                f"- {packet_row.get('packet_id')}: {packet_row.get('status')} | "
                f"{packet_row.get('from_agent')} -> {packet_row.get('to_agent')} | "
                f"{packet_row.get('summary')}"
            )
            context_summary = context_pack_ref_summary(packet_row.get("context_pack_refs"))
            if context_summary:
                summary += f" | packs: {context_summary}"
            lines.append(summary)
    history = report.get("history")
    if isinstance(history, list) and history:
        lines.append("")
        lines.append("## History")
        for event in history:
            if not isinstance(event, dict):
                continue
            lines.append(
                f"- {event.get('event_id')}: {event.get('event_type')} | "
                f"{event.get('packet_id')} | {event.get('timestamp_utc')}"
            )
    return "\n".join(lines)


def append_context_pack_ref_lines(
    lines: list[str],
    context_pack_refs: object,
    *,
    heading: str,
    indent: str,
) -> None:
    """Append normalized context-pack ref entries to a markdown line buffer."""
    summary = normalize_context_pack_refs(context_pack_refs)
    if not summary:
        return
    lines.append(heading)
    for ref in summary:
        label = f"{ref['pack_kind']}: {ref['pack_ref']}"
        adapter = ref.get("adapter_profile")
        if adapter:
            label += f" ({adapter})"
        lines.append(f"{indent}- {label}")
