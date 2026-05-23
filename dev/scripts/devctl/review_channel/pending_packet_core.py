"""Queue math for live/stale pending review packets."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass

from ..runtime.packet_transport_expiry import (
    DURABLE_INTENT_PACKET_KINDS,
    packet_transport_expired,
)
from ..runtime.packet_absorption_resolution import absorption_resolves_packet_pressure
from .pending_packet_approval_resolution import (
    approval_resolution_key,
    is_applied_approval_decision,
    is_pending_approval_request,
)
from .pending_packet_durable_resolution import has_durable_resolution
from .pending_packet_models import PacketQueueReconciliation

_ACK_ABSORPTION_REQUIRED_KINDS = {
    "action_request",
    "decision",
    "finding",
    "proposal",
    "task_started",
    "task_produced",
}


@dataclass(frozen=True, slots=True)
class PendingPacketPartition:
    """Structured live/stale split with tuple-unpacking compatibility."""

    live: list[object]
    stale: list[object]

    @property
    def expired(self) -> list[object]:
        return self.stale

    def __iter__(self) -> Iterator[list[object]]:
        yield self.live
        yield self.stale

    def __getitem__(self, index: int) -> list[object]:
        if index == 0:
            return self.live
        if index == 1:
            return self.stale
        raise IndexError(index)

    def __len__(self) -> int:
        return 2


def partition_live_pending_packets(
    packets: Iterable[object],
) -> PendingPacketPartition:
    """Split packets into live pending work and stale/history rows.

    Only runtime-transport packets can become stale because a TTL elapsed.
    Durable-content and communication packets remain live until typed ingestion,
    dismissal, supersession, or another explicit lifecycle action resolves them.
    """
    packet_list = list(packets)
    live_packets: list[object] = []
    stale_packets: list[object] = []
    resolved_approval_keys = {
        approval_resolution_key(packet)
        for packet in packet_list
        if is_applied_approval_decision(packet)
        and any(approval_resolution_key(packet))
    }
    for packet in packet_list:
        status = _packet_value(packet, "status")
        if not _live_queue_status(packet):
            continue
        if _is_resolved_lifecycle(packet):
            continue
        if _has_terminal_action_request_receipt(packet):
            continue
        if has_durable_resolution(packet):
            continue
        if (
            is_pending_approval_request(packet)
            and approval_resolution_key(packet) in resolved_approval_keys
        ):
            continue
        if isinstance(packet, Mapping) and _packet_expired_for_live_queue(packet):
            stale_packets.append(packet)
            continue
        live_packets.append(packet)
    return PendingPacketPartition(live=live_packets, stale=stale_packets)


def _packet_expired_for_live_queue(packet: Mapping[str, object]) -> bool:
    if str(packet.get("kind") or "").strip() in DURABLE_INTENT_PACKET_KINDS:
        return False
    return packet_transport_expired(packet)


def _live_queue_status(packet: object) -> bool:
    if (
        _has_absorption_receipt(packet)
        and _absorbed_packet_resolves_queue_pressure(packet)
    ):
        return False
    status = str(_packet_value(packet, "status") or "").strip()
    if status == "pending":
        return True
    if status != "acked":
        return False
    kind = str(_packet_value(packet, "kind") or "").strip()
    if kind not in _ACK_ABSORPTION_REQUIRED_KINDS:
        return False
    return not (
        _has_absorption_receipt(packet)
        and _absorbed_packet_resolves_queue_pressure(packet)
    )


def _has_absorption_receipt(packet: object) -> bool:
    if not isinstance(packet, Mapping):
        return False
    receipts = [
        receipt
        for receipt in (
            _packet_value(packet, "absorption_receipt"),
            _packet_value(packet, "packet_absorption_receipt"),
        )
        if isinstance(receipt, Mapping)
    ]
    for events_key in ("absorption_events", "packet_absorption_events"):
        value = _packet_value(packet, events_key)
        if not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
            continue
        for item in value:
            if not isinstance(item, Mapping):
                continue
            receipt = item.get("packet_absorption_receipt")
            if isinstance(receipt, Mapping):
                receipts.append(receipt)
            elif str(item.get("contract_id") or "").strip() == "PacketAbsorptionReceipt":
                receipts.append(item)
    return bool(receipts) and absorption_resolves_packet_pressure(
        packet,
        absorption_receipts=tuple(receipts),
    )


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


def _has_terminal_action_request_receipt(packet: object) -> bool:
    if str(_packet_value(packet, "kind") or "").strip() != "action_request":
        return False
    return bool(
        str(_packet_value(packet, "execution_failed_at_utc") or "").strip()
        or str(
            _packet_value(packet, "apply_pending_after_execution_at_utc") or ""
        ).strip()
    )


def _is_resolved_lifecycle(packet: object) -> bool:
    lifecycle = str(_packet_value(packet, "lifecycle_current_state") or "").strip()
    if lifecycle == "absorbed":
        return _absorbed_packet_resolves_queue_pressure(packet)
    if lifecycle in {"applied", "dismissed", "archived"}:
        return True
    disposition = _packet_value(packet, "disposition")
    if not isinstance(disposition, Mapping):
        return False
    sink = str(disposition.get("sink") or "").strip()
    if sink == "absorbed":
        return _absorbed_packet_resolves_queue_pressure(packet)
    return sink in {"applied", "dismissed", "archived"}


def _absorbed_packet_resolves_queue_pressure(packet: object) -> bool:
    """Return whether absorption is enough to remove this packet from live queue.

    Durable plan/finding packets need a durable binding or a terminal semantic
    disposition before absorption can clear live pressure. Otherwise the packet
    was only parsed, not safely converted into typed work.
    """
    if not isinstance(packet, Mapping):
        return False
    return absorption_resolves_packet_pressure(packet)


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


def _packet_value(packet: object, field_name: str) -> object:
    if isinstance(packet, Mapping):
        return packet.get(field_name)
    return getattr(packet, field_name, None)
