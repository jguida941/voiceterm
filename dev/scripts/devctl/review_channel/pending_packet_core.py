"""Queue math for live/stale pending review packets."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone

from .pending_packet_models import PacketQueueReconciliation


def partition_live_pending_packets(
    packets: Iterable[object],
) -> tuple[list[object], list[object]]:
    """Split packets into live pending work and stale/history rows.

    Only packets with ``status == "pending"`` and a future expiry remain in the
    live actionable queue. Everything else stays in the history bucket so
    operator-facing projections can render it separately instead of mixing it
    back into the current work queue.
    """
    packet_list = list(packets)
    live_packets: list[object] = []
    stale_packets: list[object] = []
    resolved_approval_keys = {
        _approval_resolution_key(packet)
        for packet in packet_list
        if _is_applied_approval_decision(packet)
        and any(_approval_resolution_key(packet))
    }
    now = datetime.now(timezone.utc)
    for packet in packet_list:
        status = _packet_value(packet, "status")
        if str(status or "").strip() != "pending":
            continue
        if (
            _is_pending_approval_request(packet)
            and _approval_resolution_key(packet) in resolved_approval_keys
        ):
            continue
        expires_at = _parse_utc(
            str(_packet_value(packet, "expires_at_utc") or "").strip()
        )
        if expires_at is not None and expires_at <= now:
            stale_packets.append(packet)
            continue
        live_packets.append(packet)
    return live_packets, stale_packets


def live_pending_packets(
    packets: Iterable[object],
) -> tuple[object, ...]:
    """Return only the live actionable pending packets."""
    return tuple(partition_live_pending_packets(packets)[0])


def partition_live_packet_queue(
    packets: Iterable[object],
) -> tuple[list[object], list[object], list[object]]:
    """Split packets into live actionable rows, packet history, and expired pendings."""
    packet_list = list(packets)
    live_packets, stale_packets = partition_live_pending_packets(packet_list)
    history_packets = [
        packet
        for packet in packet_list
        if packet not in live_packets
    ]
    return live_packets, history_packets, stale_packets


def reconcile_review_state_packet_queue(
    review_state: Mapping[str, object],
    *,
    history_limit: int | None = None,
) -> PacketQueueReconciliation:
    """Summarize the rendered queue split for one reduced review-state payload."""
    packets = review_state.get("packets")
    queue = review_state.get("queue")
    packet_rows = packets if isinstance(packets, Iterable) else ()
    queue_mapping = queue if isinstance(queue, Mapping) else None
    return reconcile_packet_queue(
        packet_rows,
        queue=queue_mapping,
        history_limit=history_limit,
    )


def reconcile_packet_queue(
    packets: Iterable[object],
    *,
    queue: Mapping[str, object] | None = None,
    history_limit: int | None = None,
) -> PacketQueueReconciliation:
    """Summarize live/history/expired queue state for operator-facing projections."""
    packet_rows = [packet for packet in packets if isinstance(packet, Mapping)]
    live_packets, history_packets, stale_packets = partition_live_packet_queue(
        packet_rows
    )
    live_total = len(live_packets)
    stale_total = len(stale_packets)
    history_total = len(history_packets)
    shown_total = history_total
    if history_limit is not None and history_limit >= 0:
        shown_total = min(history_total, history_limit)
    queue_pending_total = _coerce_int(
        queue.get("pending_total") if isinstance(queue, Mapping) else None,
        default=live_total,
    )
    queue_stale_total = _coerce_int(
        queue.get("stale_packet_count") if isinstance(queue, Mapping) else None,
        default=stale_total,
    )
    return PacketQueueReconciliation(
        packet_total=len(packet_rows),
        live_pending_total=live_total,
        history_total=history_total,
        stale_pending_total=stale_total,
        queue_pending_total=queue_pending_total,
        queue_stale_total=queue_stale_total,
        history_shown_total=shown_total,
        history_truncated=history_total > shown_total,
        stale_pending_hidden_from_inbox_total=stale_total,
        pending_total_matches_queue=queue_pending_total == live_total,
        stale_total_matches_queue=queue_stale_total == stale_total,
    )


def _is_pending_approval_request(packet: object) -> bool:
    status = str(_packet_value(packet, "status") or "").strip()
    if status != "pending":
        return False
    if not bool(_packet_value(packet, "approval_required")):
        return False
    return _is_commit_approval_kind(packet)


def _is_applied_approval_decision(packet: object) -> bool:
    status = str(_packet_value(packet, "status") or "").strip()
    if status != "applied":
        return False
    if bool(_packet_value(packet, "approval_required")):
        return False
    return _is_commit_approval_kind(packet)


def _is_commit_approval_kind(packet: object) -> bool:
    return str(_packet_value(packet, "kind") or "").strip() == "commit_approval"


def _approval_resolution_key(packet: object) -> tuple[str, str, str, str]:
    return (
        str(_packet_value(packet, "trace_id") or "").strip(),
        str(_packet_value(packet, "kind") or "").strip(),
        str(_packet_value(packet, "target_ref") or "").strip(),
        str(_packet_value(packet, "pipeline_generation") or "").strip(),
    )


def _coerce_int(value: object, *, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _parse_utc(raw_value: str) -> datetime | None:
    if not raw_value:
        return None
    try:
        return datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _packet_value(packet: object, field_name: str) -> object:
    if isinstance(packet, Mapping):
        return packet.get(field_name)
    return getattr(packet, field_name, None)
