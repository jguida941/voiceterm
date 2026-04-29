"""Markdown rendering helpers for event-backed review-channel actions."""

from __future__ import annotations

from ..review_channel.doctor_markdown import append_doctor_markdown
from ..review_channel.context_refs import (
    context_pack_ref_summary,
    normalize_context_pack_refs,
)
from ..review_channel.pending_packets import partition_live_packet_queue

from ..commands.review_channel_bridge_render import append_common_report_sections


def render_event_md(report: dict) -> str:
    """Render a markdown summary for event-backed review-channel actions."""
    lines = ["# devctl review-channel", ""]
    lines.append(f"- ok: {report['ok']}")
    lines.append(f"- action: {report.get('action')}")
    lines.append(f"- execution_mode: {report.get('execution_mode')}")
    queue = report.get("queue") or {}
    lines.append(f"- pending_total: {queue.get('pending_total', 0)}")
    lines.append(
        "- stale_packet_count: "
        f"{queue.get('stale_packet_count', 0)} (expired pending packets)"
    )
    if report.get("target"):
        lines.append(f"- target: {report.get('target')}")
    if report.get("status_filter"):
        lines.append(f"- status_filter: {report.get('status_filter')}")
    if report.get("limit") is not None:
        lines.append(f"- limit: {report.get('limit')}")
    _append_queue_reconciliation(lines, report.get("queue_reconciliation"))
    append_common_report_sections(lines, report)
    append_doctor_markdown(lines, report.get("doctor"))
    packet = report.get("packet")
    if isinstance(packet, dict):
        _append_packet_section(lines, packet)
    _append_packet_outcome_ledger(lines, report.get("packet_outcome_ledger"))
    packets = report.get("packets")
    if isinstance(packets, list) and packets:
        _append_packet_queue_sections(lines, packets)
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


def _append_queue_reconciliation(lines: list[str], reconciliation: object) -> None:
    if not isinstance(reconciliation, dict):
        return
    if not bool(reconciliation.get("needs_attention")):
        return
    lines.append("")
    lines.append("## Packet Queue Reconciliation")
    lines.append(
        f"- live_pending_total: {reconciliation.get('live_pending_total', 0)}"
    )
    lines.append(f"- history_total: {reconciliation.get('history_total', 0)}")
    lines.append(
        f"- expired_pending_total: {reconciliation.get('stale_pending_total', 0)}"
    )
    lines.append(
        f"- queue_pending_total: {reconciliation.get('queue_pending_total', 0)}"
    )
    lines.append(f"- queue_stale_total: {reconciliation.get('queue_stale_total', 0)}")
    lines.append(
        "- expired_pending_hidden_from_inbox_total: "
        f"{reconciliation.get('stale_pending_hidden_from_inbox_total', 0)}"
    )
    lines.append(
        f"- history_shown_total: {reconciliation.get('history_shown_total', 0)}"
    )
    lines.append(
        f"- history_truncated: {bool(reconciliation.get('history_truncated'))}"
    )
    if reconciliation.get("stale_pending_hidden_from_inbox_total"):
        lines.append(
            "- note: expired pending packets are archived audit rows whose TTL "
            "elapsed; they stay in history with disposition evidence and are "
            "intentionally excluded from the live inbox until they are reissued"
        )
    if reconciliation.get("history_truncated"):
        lines.append(
            "- note: this surface is only showing the newest packet-history rows"
        )


def _format_packet_line(
    packet_row: dict,
    *,
    stale_pending: bool = False,
) -> str:
    """Format one packet as a markdown list item."""
    if not isinstance(packet_row, dict):
        return "- packet: (unavailable)"
    status = str(packet_row.get("status") or "unknown").strip()
    if stale_pending and status == "pending":
        status = "pending (expired)"
    summary = (
        f"- {packet_row.get('packet_id')}: {status} | "
        f"{packet_row.get('from_agent')} -> {packet_row.get('to_agent')} | "
        f"{packet_row.get('summary')}"
    )
    ctx = context_pack_ref_summary(packet_row.get("context_pack_refs"))
    if ctx:
        summary += f" | packs: {ctx}"
    if packet_row.get("pipeline_generation"):
        summary += f" | gen: {packet_row.get('pipeline_generation')}"
    outcome = packet_row.get("packet_outcome")
    if isinstance(outcome, dict):
        outcome_name = str(outcome.get("outcome") or "").strip()
        evidence_ref = str(outcome.get("evidence_ref") or "").strip()
        if outcome_name:
            summary += f" | outcome: {outcome_name}"
            if evidence_ref:
                summary += f" ({evidence_ref})"
    disposition = packet_row.get("disposition")
    if isinstance(disposition, dict):
        sink = str(disposition.get("sink") or "").strip()
        anchor = str(disposition.get("resolution_anchor") or "").strip()
        if sink:
            summary += f" | disposition: {sink}"
            if anchor:
                summary += f" ({anchor})"
    return summary


def _append_packet_section(lines: list[str], packet: dict) -> None:
    lines.append("")
    lines.append("## Packet")
    lines.append(f"- packet_id: {packet.get('packet_id')}")
    lines.append(f"- trace_id: {packet.get('trace_id')}")
    lines.append(f"- route: {packet.get('from_agent')} -> {packet.get('to_agent')}")
    lines.append(f"- status: {packet.get('status')}")
    if packet.get("lifecycle_current_state"):
        lines.append(f"- lifecycle_current_state: {packet.get('lifecycle_current_state')}")
    if packet.get("resolution_anchor"):
        lines.append(f"- resolution_anchor: {packet.get('resolution_anchor')}")
    lines.append(f"- summary: {packet.get('summary')}")
    disposition = packet.get("disposition")
    if isinstance(disposition, dict):
        lines.append(
            "- disposition: "
            f"{disposition.get('sink') or 'n/a'} | "
            f"{disposition.get('resolution_anchor') or 'n/a'}"
        )
    if packet.get("target_kind"):
        lines.append(
            "- target: "
            f"{packet.get('target_kind')} | "
            f"{packet.get('target_ref') or 'n/a'} | "
            f"{packet.get('target_revision') or 'n/a'}"
        )
    if packet.get("pipeline_generation"):
        lines.append(f"- pipeline_generation: {packet.get('pipeline_generation')}")
    if packet.get("staged_snapshot_hash"):
        lines.append(f"- staged_snapshot_hash: {packet.get('staged_snapshot_hash')}")
    if packet.get("guard_results_summary"):
        lines.append(f"- guard_results_summary: {packet.get('guard_results_summary')}")
    if packet.get("full_guard_bundle_evidence"):
        lines.append(
            "- full_guard_bundle_evidence: "
            f"{packet.get('full_guard_bundle_evidence')}"
        )
    append_context_pack_ref_lines(
        lines,
        packet.get("context_pack_refs"),
        heading="- context_pack_refs:",
        indent="  ",
    )


def _append_packet_outcome_ledger(lines: list[str], ledger: object) -> None:
    if not isinstance(ledger, dict):
        return
    lines.append("")
    lines.append("## Packet Outcome Ledger")
    lines.append(f"- contract_id: {ledger.get('contract_id')}")
    lines.append(f"- record_count: {ledger.get('record_count', 0)}")
    counts = ledger.get("outcome_counts")
    if isinstance(counts, dict):
        nonzero = [
            f"{name}={count}"
            for name, count in counts.items()
            if int(count or 0) > 0
        ]
        if nonzero:
            lines.append(f"- outcome_counts: {', '.join(nonzero)}")


def _append_packet_queue_sections(
    lines: list[str],
    packets: list[dict],
) -> None:
    pending, history, stale_packets = partition_live_packet_queue(packets)
    stale_packet_ids = {_packet_id_text(packet_row) for packet_row in stale_packets}
    if pending:
        lines.append("")
        lines.append("## Live Packets")
        for packet_row in pending:
            lines.append(_format_packet_line(packet_row))
    if history:
        lines.append("")
        lines.append("## Packet History")
        for packet_row in history:
            lines.append(
                _format_packet_line(
                    packet_row,
                    stale_pending=_packet_id_text(packet_row) in stale_packet_ids,
                )
            )


def _packet_id_text(packet_row: object) -> str:
    if not isinstance(packet_row, dict):
        return ""
    return str(packet_row.get("packet_id") or "").strip()


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
