"""Event-backed action rendering and execution for `devctl review-channel`.

Handles post, watch, inbox, ack, dismiss, apply, and history actions that
operate against the structured event store. Extracted from
commands/review_channel.py to keep the command orchestrator under the
file-size soft limit.
"""

from __future__ import annotations

from pathlib import Path

from ..review_channel.context_refs import (
    context_pack_ref_summary,
    normalize_context_pack_refs,
    resolve_context_pack_refs,
)
from ..review_channel.events import (
    artifact_paths_to_dict,
    filter_history_events,
    filter_inbox_packets,
    load_or_refresh_event_bundle,
    post_packet,
    refresh_event_bundle,
    transition_packet,
)
from ..review_channel.state import projection_paths_to_dict
from ..time_utils import utc_timestamp

from .review_channel_bridge_render import append_common_report_sections


def _render_event_md(report: dict) -> str:
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
        _append_context_pack_ref_lines(
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


def _append_context_pack_ref_lines(
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


def _build_event_report(
    *,
    args,
    bundle,
    packet: dict[str, object] | None = None,
    event: dict[str, object] | None = None,
    packets: list[dict[str, object]] | None = None,
    history: list[dict[str, object]] | None = None,
    warnings: list[str] | None = None,
) -> tuple[dict, int]:
    """Assemble the event-backed action report dict."""
    report_warnings = list(bundle.review_state.get("warnings", []))
    report_warnings.extend(warnings or [])
    report_errors = list(bundle.review_state.get("errors", []))
    report = {
        "command": "review-channel",
        "timestamp": utc_timestamp(),
        "action": args.action,
        "report_mode": "event-backed",
        "ok": not report_errors,
        "exit_ok": not report_errors,
        "exit_code": 0 if not report_errors else 1,
        "execution_mode": "event-backed",
        "terminal": "none",
        "terminal_profile_requested": getattr(args, "terminal_profile", None),
        "terminal_profile_applied": None,
        "approval_mode": getattr(args, "approval_mode", "balanced"),
        "dangerous": False,
        "warnings": report_warnings,
        "errors": report_errors,
        "sessions": [],
        "handoff_bundle": None,
        "handoff_ack_required": False,
        "handoff_ack_observed": None,
        "bridge_liveness": None,
        "projection_paths": projection_paths_to_dict(bundle.projection_paths),
        "artifact_paths": artifact_paths_to_dict(bundle.artifact_paths),
        "queue": bundle.review_state.get("queue", {}),
        "packet": packet,
        "packets": packets or [],
        "history": history or [],
        "event": event,
        "target": getattr(args, "target", None),
        "status_filter": getattr(args, "status", None),
        "limit": getattr(args, "limit", None),
    }
    return report, report["exit_code"]


def _load_post_body(args) -> str:
    """Read the packet body from --body or --body-file."""
    body = getattr(args, "body", None)
    body_file = getattr(args, "body_file", None)
    if body:
        return str(body)
    assert body_file is not None
    return Path(body_file).read_text(encoding="utf-8")


def _run_event_action(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
) -> tuple[dict, int]:
    """Execute an event-backed review-channel action (post, inbox, watch, ack, etc.)."""
    review_channel_path = paths["review_channel_path"]
    artifact_paths = paths["artifact_paths"]
    assert isinstance(review_channel_path, Path)
    if args.action == "post":
        bundle, event = post_packet(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
            from_agent=args.from_agent,
            to_agent=args.to_agent,
            kind=args.kind,
            summary=args.summary,
            body=_load_post_body(args),
            evidence_refs=list(args.evidence_ref or []),
            confidence=float(args.confidence),
            requested_action=args.requested_action,
            policy_hint=args.policy_hint,
            approval_required=bool(args.approval_required),
            packet_id=getattr(args, "packet_id", None),
            trace_id=getattr(args, "trace_id", None),
            session_id=args.session_id,
            plan_id=args.plan_id,
            controller_run_id=getattr(args, "controller_run_id", None),
            expires_in_minutes=args.expires_in_minutes,
            context_pack_refs=resolve_context_pack_refs(args, repo_root),
        )
        packet = next(
            (
                packet_row
                for packet_row in bundle.review_state.get("packets", [])
                if isinstance(packet_row, dict)
                and packet_row.get("packet_id") == event.get("packet_id")
            ),
            None,
        )
        return _build_event_report(args=args, bundle=bundle, packet=packet, event=event)
    if args.action in {"ack", "dismiss", "apply"}:
        bundle, event = transition_packet(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
            action=args.action,
            packet_id=args.packet_id,
            actor=args.actor,
            session_id=args.session_id,
            plan_id=args.plan_id,
            controller_run_id=getattr(args, "controller_run_id", None),
        )
        packet = next(
            (
                packet_row
                for packet_row in bundle.review_state.get("packets", [])
                if isinstance(packet_row, dict)
                and packet_row.get("packet_id") == args.packet_id
            ),
            None,
        )
        return _build_event_report(args=args, bundle=bundle, packet=packet, event=event)
    bundle = load_or_refresh_event_bundle(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        artifact_paths=artifact_paths,
    )
    if args.action == "status":
        bundle = refresh_event_bundle(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        )
        return _build_event_report(args=args, bundle=bundle)
    if args.action == "inbox":
        packets = filter_inbox_packets(
            bundle.review_state,
            target=getattr(args, "target", None),
            status=getattr(args, "status", None),
            limit=args.limit,
        )
        return _build_event_report(args=args, bundle=bundle, packets=packets)
    if args.action == "watch":
        packets = filter_inbox_packets(
            bundle.review_state,
            target=getattr(args, "target", None),
            status=getattr(args, "status", None) or "pending",
            limit=args.limit,
        )
        warnings = []
        if getattr(args, "follow", False):
            warnings.append(
                "Follow mode is accepted but this CLI slice emits one refreshed "
                "snapshot per invocation."
            )
        return _build_event_report(
            args=args,
            bundle=bundle,
            packets=packets,
            warnings=warnings,
        )
    if args.action == "history":
        history = filter_history_events(
            bundle.events,
            trace_id=getattr(args, "trace_id", None),
            limit=args.limit,
        )
        return _build_event_report(args=args, bundle=bundle, history=history)
    raise ValueError(f"Unsupported event-backed review-channel action: {args.action}")
