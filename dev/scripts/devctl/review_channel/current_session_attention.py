"""Shared packet-attention helpers for current-session projections."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.review_packet_inbox import packet_inbox_from_review_state

def codex_packet_attention_requires_clear(
    review_state: Mapping[str, object],
) -> bool:
    packet_inbox = packet_inbox_from_review_state(review_state)
    record = None if packet_inbox is None else packet_inbox.for_agent("codex")
    return packet_attention_requires_clear(record)


def packet_attention_requires_clear(record: object | None) -> bool:
    if record is None:
        return False
    return not str(
        getattr(record, "current_instruction_packet_id", "") or ""
    ).strip()
