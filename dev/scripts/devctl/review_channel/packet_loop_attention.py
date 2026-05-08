"""Shared packet-attention policy for agent-loop wake decisions."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.session_termination_policy import SESSION_TERMINATION_PACKET_KINDS
from ..runtime.value_coercion import coerce_text


def packet_requires_loop_attention(packet: Mapping[str, object]) -> bool:
    """Return whether a live pending packet should wake an agent loop."""
    if coerce_text(packet.get("kind")) in SESSION_TERMINATION_PACKET_KINDS:
        return False
    if coerce_text(packet.get("to_agent")) != "operator":
        return True
    if coerce_text(packet.get("kind")) != "system_notice":
        return True
    if bool(packet.get("approval_required")):
        return True
    requested_action = coerce_text(packet.get("requested_action"))
    policy_hint = coerce_text(packet.get("policy_hint"))
    return requested_action not in {"", "review_only"} or policy_hint not in {
        "",
        "review_only",
    }
