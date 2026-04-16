"""Shared packet-attention helpers for current-session projections."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.review_packet_inbox import packet_inbox_from_review_state

_CLEAR_WAKE_REASONS = frozenset({"finding_pending", "expired_unresolved_packet"})


def codex_packet_attention_requires_clear(
    review_state: Mapping[str, object],
) -> bool:
    packet_inbox = packet_inbox_from_review_state(review_state)
    record = None if packet_inbox is None else packet_inbox.for_agent("codex")
    return packet_attention_requires_clear(record)


def packet_attention_requires_clear(record: object | None) -> bool:
    if record is None:
        return False
    wake_reason = str(getattr(record, "wake_reason", "") or "").strip()
    has_pending_attention = bool(
        tuple(getattr(record, "pending_actionable_packet_ids", ()) or ())
        or tuple(getattr(record, "expired_unresolved_packet_ids", ()) or ())
        or wake_reason in _CLEAR_WAKE_REASONS
    )
    return bool(
        not str(getattr(record, "current_instruction_packet_id", "") or "").strip()
        and has_pending_attention
    )
