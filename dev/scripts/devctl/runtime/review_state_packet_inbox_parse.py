"""Packet-inbox helper for typed review-state parsing."""

from __future__ import annotations

from collections.abc import Mapping

from .review_packet_inbox import packet_inbox_from_review_state
from .review_state_models import packet_inbox_from_mapping


def review_state_packet_inbox(
    *,
    payload: Mapping[str, object],
    review_payload: Mapping[str, object],
    attention: Mapping[str, object],
):
    return (
        packet_inbox_from_review_state(
            _packet_inbox_review_payload(
                payload=payload,
                review_payload=review_payload,
                attention=attention,
            )
        )
        or packet_inbox_from_mapping({"attention_revision": "", "agents": []})
    )


def _packet_inbox_review_payload(
    *,
    payload: Mapping[str, object],
    review_payload: Mapping[str, object],
    attention: Mapping[str, object],
) -> dict[str, object]:
    packet_payload = dict(review_payload)
    if "packet_inbox" not in packet_payload and isinstance(
        payload.get("packet_inbox"), Mapping
    ):
        packet_payload["packet_inbox"] = payload.get("packet_inbox")
    if "attention" not in packet_payload and attention:
        packet_payload["attention"] = attention
    return packet_payload


__all__ = ["review_state_packet_inbox"]
