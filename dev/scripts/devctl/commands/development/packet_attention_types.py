"""Shared packet attention DTOs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

NO_PENDING_ATTENTION_SUMMARY = (
    "no pending attention; proceed with current slice or /develop "
    "dispatch-agent for next work"
)


@dataclass(frozen=True, slots=True)
class PacketExitContext:
    review_state: Mapping[str, object]
    durable_packet_ids: frozenset[str]
    class_owner_by_failure: Mapping[str, str]
    terminal_receipt_by_packet: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class PacketAttentionSummaryInput:
    record: object
    expired_unresolved_packet_ids: tuple[str, ...]
    durable_row_id: str
    latest_attention_packet_id: str
    latest_finding_packet_id: str
    pending_delivery_packet_ids: tuple[str, ...]
    pending_actionable_packet_ids: tuple[str, ...]


__all__ = [
    "NO_PENDING_ATTENTION_SUMMARY",
    "PacketAttentionSummaryInput",
    "PacketExitContext",
]
