"""Actionable packet selection for develop attention."""

from __future__ import annotations

from .packet_attention_lifecycle import packet_exits_next_pool
from .packet_attention_types import PacketExitContext


def pending_actionable_packet_ids(
    values: tuple[str, ...],
    *,
    exit_context: PacketExitContext,
    latest_finding_packet_id: str,
    wake_reason: str,
    attention_required: bool,
) -> tuple[str, ...]:
    packet_ids = [
        packet_id
        for value in values
        if (packet_id := str(value or "").strip())
        and not packet_exits_next_pool(
            exit_context,
            packet_id=packet_id,
        )
    ]
    if _should_insert_latest_finding(
        attention_required=attention_required,
        wake_reason=wake_reason,
        latest_finding_packet_id=latest_finding_packet_id,
        packet_ids=packet_ids,
    ):
        packet_ids.insert(0, latest_finding_packet_id)
    return tuple(packet_ids)


def _should_insert_latest_finding(
    *,
    attention_required: bool,
    wake_reason: str,
    latest_finding_packet_id: str,
    packet_ids: list[str],
) -> bool:
    return (
        attention_required
        and wake_reason == "finding_pending"
        and bool(latest_finding_packet_id)
        and latest_finding_packet_id not in packet_ids
    )


__all__ = ["pending_actionable_packet_ids"]
