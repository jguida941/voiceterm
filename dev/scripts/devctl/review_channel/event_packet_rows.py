"""Packet-row helpers used by the review-channel event reducer."""

from __future__ import annotations

from .context_refs import normalize_context_pack_refs
from .event_models import ReviewPacketRow
from .pending_packets import partition_live_pending_packets


def summarize_packets(
    packets_by_id: dict[str, ReviewPacketRow],
) -> tuple[list[dict[str, object]], dict[str, int], int]:
    packet_rows: list[dict[str, object]] = []
    pending_counts = {"codex": 0, "claude": 0, "cursor": 0, "operator": 0}
    ordered_packets = [
        dict(packet)
        for packet in sorted(
            packets_by_id.values(),
            key=lambda item: str(item.get("_sort_timestamp") or ""),
            reverse=True,
        )
    ]
    live_packets, stale_packets = partition_live_pending_packets(ordered_packets)
    live_packet_ids = {
        str(packet.get("packet_id") or "").strip()
        for packet in live_packets
        if isinstance(packet, dict)
    }
    for packet in ordered_packets:
        if str(packet.get("packet_id") or "").strip() in live_packet_ids:
            target = str(packet.get("to_agent") or "").strip()
            if target in pending_counts:
                pending_counts[target] += 1
        clean_packet = dict(packet)
        clean_packet.pop("_sort_timestamp", None)
        packet_rows.append(clean_packet)
    return packet_rows, pending_counts, len(stale_packets)


def packet_from_event(event: dict[str, object]) -> ReviewPacketRow:
    is_action_request = str(event.get("kind") or "").strip() == "action_request"
    return ReviewPacketRow(
        packet_id=event.get("packet_id"),
        trace_id=event.get("trace_id"),
        latest_event_id=event.get("event_id"),
        from_agent=event.get("from_agent"),
        to_agent=event.get("to_agent"),
        kind=event.get("kind"),
        summary=event.get("summary"),
        body=event.get("body"),
        evidence_refs=list(event.get("evidence_refs") or []),
        guidance_refs=list(event.get("guidance_refs") or []),
        context_pack_refs=normalize_context_pack_refs(
            event.get("context_pack_refs")
        ),
        confidence=float(event.get("confidence") or 0.0),
        requested_action=event.get("requested_action"),
        policy_hint=event.get("policy_hint"),
        approval_required=bool(event.get("approval_required")),
        target_kind=event.get("target_kind"),
        target_ref=event.get("target_ref"),
        target_revision=event.get("target_revision"),
        anchor_refs=list(event.get("anchor_refs") or []),
        intake_ref=event.get("intake_ref"),
        mutation_op=event.get("mutation_op"),
        pipeline_generation=event.get("pipeline_generation"),
        staged_snapshot_hash=event.get("staged_snapshot_hash"),
        guard_results_summary=event.get("guard_results_summary"),
        full_guard_bundle_evidence=event.get("full_guard_bundle_evidence"),
        status=event.get("status"),
        posted_at=event.get("timestamp_utc"),
        acked_by=None,
        acked_at_utc=None,
        applied_at_utc=None,
        delivery_emitted_at_utc=event.get("timestamp_utc") if is_action_request else None,
        delivery_observed_at_utc="",
        delivery_observed_by="",
        execution_started_at_utc="",
        execution_started_by="",
        expires_at_utc=event.get("expires_at_utc"),
        _sort_timestamp=event.get("timestamp_utc"),
    )


def apply_packet_transition(
    packet: dict[str, object],
    event: dict[str, object],
) -> dict[str, object]:
    next_packet = dict(packet)
    event_type = str(event.get("event_type") or "").strip()
    next_packet["latest_event_id"] = event.get("event_id")
    next_packet["_sort_timestamp"] = event.get("timestamp_utc")
    next_packet["status"] = event.get("status")
    if event.get("guidance_refs") is not None or packet.get("guidance_refs"):
        next_packet["guidance_refs"] = list(
            event.get("guidance_refs") or packet.get("guidance_refs") or []
        )
    if event.get("context_pack_refs") is not None or packet.get("context_pack_refs"):
        next_packet["context_pack_refs"] = normalize_context_pack_refs(
            event.get("context_pack_refs") or packet.get("context_pack_refs")
        )
    if event.get("pipeline_generation") is not None or packet.get("pipeline_generation"):
        next_packet["pipeline_generation"] = (
            event.get("pipeline_generation") or packet.get("pipeline_generation")
        )
    if event.get("staged_snapshot_hash") is not None or packet.get("staged_snapshot_hash"):
        next_packet["staged_snapshot_hash"] = (
            event.get("staged_snapshot_hash")
            or packet.get("staged_snapshot_hash")
        )
    if event.get("guard_results_summary") is not None or packet.get("guard_results_summary"):
        next_packet["guard_results_summary"] = (
            event.get("guard_results_summary")
            or packet.get("guard_results_summary")
        )
    if (
        event.get("full_guard_bundle_evidence") is not None
        or packet.get("full_guard_bundle_evidence")
    ):
        next_packet["full_guard_bundle_evidence"] = (
            event.get("full_guard_bundle_evidence")
            or packet.get("full_guard_bundle_evidence")
        )
    actor = str((event.get("metadata") or {}).get("actor") or "").strip()
    if event_type == "packet_acked":
        next_packet["acked_by"] = actor or packet.get("to_agent")
        next_packet["acked_at_utc"] = event.get("timestamp_utc")
    if event_type == "packet_applied":
        next_packet["applied_at_utc"] = event.get("timestamp_utc")
    if str(packet.get("kind") or "").strip() == "action_request":
        if not str(next_packet.get("delivery_emitted_at_utc") or "").strip():
            next_packet["delivery_emitted_at_utc"] = (
                packet.get("delivery_emitted_at_utc")
                or packet.get("posted_at")
            )
        if event_type == "packet_acked":
            next_packet["execution_started_at_utc"] = event.get("timestamp_utc")
            next_packet["execution_started_by"] = actor or packet.get("to_agent")
        if (
            event_type == "packet_applied"
            and not str(next_packet.get("execution_started_at_utc") or "").strip()
        ):
            next_packet["execution_started_at_utc"] = event.get("timestamp_utc")
            next_packet["execution_started_by"] = actor or packet.get("to_agent")
    return next_packet
