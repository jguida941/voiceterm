"""Packet-row helpers used by the review-channel event reducer."""

from __future__ import annotations

from datetime import datetime, timezone

from .context_refs import normalize_context_pack_refs
from .event_models import ReviewPacketRow
from .event_store import parse_utc


def summarize_packets(
    packets_by_id: dict[str, ReviewPacketRow],
) -> tuple[list[dict[str, object]], dict[str, int], int]:
    now_utc = datetime.now(timezone.utc)
    stale_packet_count = 0
    packet_rows: list[dict[str, object]] = []
    pending_counts = {"codex": 0, "claude": 0, "cursor": 0, "operator": 0}
    for packet in sorted(
        packets_by_id.values(),
        key=lambda item: str(item.get("_sort_timestamp") or ""),
        reverse=True,
    ):
        expires_at = parse_utc(packet.get("expires_at_utc"))
        is_expired = expires_at is not None and expires_at <= now_utc
        if packet.get("status") == "pending":
            if is_expired:
                stale_packet_count += 1
            else:
                target = str(packet.get("to_agent") or "").strip()
                if target in pending_counts:
                    pending_counts[target] += 1
        clean_packet = dict(packet)
        clean_packet.pop("_sort_timestamp", None)
        packet_rows.append(clean_packet)
    return packet_rows, pending_counts, stale_packet_count


def packet_from_event(event: dict[str, object]) -> ReviewPacketRow:
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
        status=event.get("status"),
        posted_at=event.get("timestamp_utc"),
        acked_by=None,
        acked_at_utc=None,
        applied_at_utc=None,
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
    if event.get("context_pack_refs") is not None or packet.get("context_pack_refs"):
        next_packet["context_pack_refs"] = normalize_context_pack_refs(
            event.get("context_pack_refs") or packet.get("context_pack_refs")
        )
    actor = str((event.get("metadata") or {}).get("actor") or "").strip()
    if event_type == "packet_acked":
        next_packet["acked_by"] = actor or packet.get("to_agent")
        next_packet["acked_at_utc"] = event.get("timestamp_utc")
    if event_type == "packet_applied":
        next_packet["applied_at_utc"] = event.get("timestamp_utc")
    return next_packet
