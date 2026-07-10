"""Packet attention lifecycle/exit predicates."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ...runtime.development_packet_failure_owner import (
    CLOCK_EXPIRED_WITHOUT_DISPOSITION,
)
from ...runtime.packet_runtime_lifecycle import packet_requires_runtime_lifecycle
from .packet_attention_types import PacketExitContext


def packet_exits_next_pool(
    context: PacketExitContext,
    *,
    packet_id: str,
) -> bool:
    if not packet_id:
        return False
    if context.terminal_receipt_by_packet.get(packet_id):
        return True
    if packet_id not in context.durable_packet_ids:
        return False
    packet = packet_by_id(context.review_state, packet_id)
    if packet_requires_runtime_lifecycle(packet):
        return False
    return True


def expired_packet_exits_next_pool(
    context: PacketExitContext,
    *,
    packet_id: str,
) -> bool:
    if not packet_id:
        return True
    if context.terminal_receipt_by_packet.get(packet_id):
        return True
    if packet_id in context.durable_packet_ids:
        return True
    if class_owner_exits_expired_packet(context, packet_id=packet_id):
        return True
    packet = packet_by_id(context.review_state, packet_id)
    if has_clock_expired_without_disposition(packet):
        return False
    return has_terminal_packet_receipt(packet)


def packet_by_id(
    review_state: Mapping[str, object],
    packet_id: str,
) -> Mapping[str, object]:
    for packet in packet_rows(review_state.get("packets")):
        if str(packet.get("packet_id") or "").strip() == packet_id:
            return packet
    return {}


def has_terminal_packet_receipt(packet: Mapping[str, object]) -> bool:
    status = str(packet.get("status") or "").strip()
    if status in {"acked", "applied", "dismissed", "archived", "rejected"}:
        return True
    lifecycle = str(packet.get("lifecycle_current_state") or "").strip()
    if lifecycle in {"acked", "applied", "dismissed", "archived", "rejected"}:
        return True
    disposition = packet.get("disposition")
    if not isinstance(disposition, Mapping):
        return False
    sink = str(disposition.get("sink") or "").strip()
    classification = str(disposition.get("classification") or "").strip()
    terminal_sinks = {"applied", "dismissed", "archived", "rejected"}
    terminal_classifications = {
        "applied",
        "dismissed",
        "dismissed_with_actor",
        "duplicate",
        "obsolete",
        "rejected",
    }
    return sink in terminal_sinks or classification in terminal_classifications


def has_clock_expired_without_disposition(packet: Mapping[str, object]) -> bool:
    disposition = packet.get("disposition")
    if not isinstance(disposition, Mapping):
        return False
    classification = str(disposition.get("archive_classification") or "").strip()
    if not classification:
        resolution_anchor = str(disposition.get("resolution_anchor") or "").strip()
        prefix = "archive_classification:"
        if resolution_anchor.startswith(prefix):
            classification = resolution_anchor[len(prefix) :]
    return classification == "clock_expired_without_disposition"


def class_owner_exits_expired_packet(
    context: PacketExitContext,
    *,
    packet_id: str,
) -> bool:
    if not context.class_owner_by_failure.get(CLOCK_EXPIRED_WITHOUT_DISPOSITION):
        return False
    packet = packet_by_id(context.review_state, packet_id)
    return has_clock_expired_without_disposition(packet)


def packet_rows(packets: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(packets, Sequence) or isinstance(packets, (str, bytes)):
        return ()
    return tuple(packet for packet in packets if isinstance(packet, Mapping))


__all__ = [
    "expired_packet_exits_next_pool",
    "has_clock_expired_without_disposition",
    "packet_by_id",
    "packet_exits_next_pool",
    "packet_rows",
]
