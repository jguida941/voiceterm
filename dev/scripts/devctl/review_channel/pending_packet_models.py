"""Typed pending-packet queue models."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PendingPacketQueueSnapshot:
    """Expiry-aware pending/expired packet view derived from the event log."""

    pending_packets: tuple[dict[str, object], ...]
    stale_packet_count: int = 0
    control_packets: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True)
class PacketQueueReconciliation:
    """Operator-facing summary of live vs expired/history packet state."""

    packet_total: int
    live_pending_total: int
    history_total: int
    stale_pending_total: int
    queue_pending_total: int
    queue_stale_total: int
    history_shown_total: int
    history_truncated: bool
    stale_pending_hidden_from_inbox_total: int
    pending_total_matches_queue: bool
    stale_total_matches_queue: bool

    def needs_attention(self) -> bool:
        return (
            not self.pending_total_matches_queue
            or not self.stale_total_matches_queue
            or self.stale_pending_hidden_from_inbox_total > 0
            or self.history_truncated
        )

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["needs_attention"] = self.needs_attention()
        return payload
