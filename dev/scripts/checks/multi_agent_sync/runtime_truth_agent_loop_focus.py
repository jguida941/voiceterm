"""Packet focus comparisons for the multi-agent sync guard."""

from __future__ import annotations

from collections.abc import Mapping

from dev.scripts.devctl.runtime.value_coercion import coerce_text


def packet_focus_errors(
    key: str,
    row: Mapping[str, object],
    decision: Mapping[str, object],
) -> list[str]:
    errors: list[str] = []
    active = coerce_text(row.get("active_packet_id"))
    decision_active = coerce_text(decision.get("active_packet_id"))
    if active and not decision_packet_matches(decision, active, "active_packet_id"):
        errors.append(
            "Typed agent_loop_decision active packet does not match "
            f"agent_work_board for {key}: work_board={active}; "
            f"decision={decision_active or 'none'}"
        )
    attention = coerce_text(row.get("attention_packet_id"))
    decision_attention = coerce_text(decision.get("attention_packet_id"))
    if attention and not decision_packet_matches(
        decision,
        attention,
        "attention_packet_id",
    ):
        errors.append(
            "Typed agent_loop_decision attention packet does not match "
            f"agent_work_board for {key}: work_board={attention}; "
            f"decision={decision_attention or 'none'}"
        )
    return errors


def decision_packet_matches(
    decision: Mapping[str, object],
    expected_packet_id: str,
    field: str,
) -> bool:
    if coerce_text(decision.get(field)) == expected_packet_id:
        return True
    return coerce_text(decision.get("legacy_unscoped_packet_id")) == expected_packet_id
