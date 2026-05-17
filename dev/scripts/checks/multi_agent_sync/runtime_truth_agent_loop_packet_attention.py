"""Global packet-attention checks for multi-agent runtime truth."""

from __future__ import annotations

from collections.abc import Mapping

from dev.scripts.devctl.runtime.value_coercion import (
    coerce_int,
    coerce_mapping,
    coerce_text,
)


def ambiguous_packet_attention_errors(
    payload: Mapping[str, object],
    decision_rows: list[Mapping[str, object]],
    *,
    pending_agents: set[str],
) -> list[str]:
    wake_rows = [
        row
        for row in decision_rows
        if bool(row.get("wake_required"))
        or coerce_int(row.get("pending_packet_count")) > 0
    ]
    if not wake_rows and not pending_agents:
        return []
    attention = coerce_mapping(
        coerce_mapping(payload.get("reviewer_runtime")).get("packet_attention")
    )
    if coerce_text(attention.get("observation_actor_id")):
        return []
    return _ambiguous_attention_shape_errors(attention)


def _ambiguous_attention_shape_errors(attention: Mapping[str, object]) -> list[str]:
    errors: list[str] = []
    if not bool(attention.get("wake_required")):
        errors.append(
            "Global packet_attention is actor-ambiguous but reports wake_required=false "
            "while scoped agent_loop_decisions require wake."
        )
    if coerce_int(attention.get("pending_packet_count")) <= 0:
        errors.append(
            "Global packet_attention is actor-ambiguous but reports pending_packet_count=0 "
            "while scoped agent_loop_decisions have pending packets."
        )
    stale_reason = coerce_text(attention.get("stale_reason"))
    if stale_reason != "actor_identity_ambiguous_with_pending_wake":
        errors.append(
            "Global packet_attention must surface "
            "actor_identity_ambiguous_with_pending_wake when scoped decisions require wake."
        )
    return errors
