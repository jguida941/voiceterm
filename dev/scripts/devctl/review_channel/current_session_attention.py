"""Shared packet-attention helpers for current-session projections."""

from __future__ import annotations

from collections.abc import Mapping

from .collaboration_provider import coding_provider_from_review_state
from ..runtime.review_packet_inbox import packet_inbox_from_review_state


def codex_packet_attention_requires_clear(
    review_state: Mapping[str, object],
) -> bool:
    return implementer_packet_attention_requires_clear(review_state)


def implementer_packet_attention_requires_clear(
    review_state: Mapping[str, object],
) -> bool:
    return packet_attention_requires_clear(implementer_packet_attention_for(review_state))


def packet_attention_requires_clear(record: object | None) -> bool:
    if record is None:
        return False
    return not str(
        getattr(record, "current_instruction_packet_id", "") or ""
    ).strip()


def packet_attention_for(
    review_state: Mapping[str, object],
    *,
    agent: str,
) -> object | None:
    if not has_explicit_packet_truth(review_state):
        return None
    packet_inbox = packet_inbox_from_review_state(review_state)
    if packet_inbox is None:
        return None
    return packet_inbox.for_agent(agent)


def implementer_packet_attention_for(
    review_state: Mapping[str, object],
) -> object | None:
    return packet_attention_for(
        review_state,
        agent=coding_provider_from_review_state(review_state),
    )


def has_explicit_packet_truth(review_state: Mapping[str, object]) -> bool:
    if "packet_inbox" in review_state:
        return True
    packets = review_state.get("packets")
    return isinstance(packets, list) and bool(packets)
