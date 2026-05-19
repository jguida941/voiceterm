"""Shared packet semantic action-item helpers."""

from __future__ import annotations

from collections.abc import Mapping

from .agent_packet_attention import _semantic_action_item_rows


def semantic_action_item_rows_for_packet(
    packet: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    """Return semantic action rows using the review-channel packet classifier."""

    return _semantic_action_item_rows(packet)
