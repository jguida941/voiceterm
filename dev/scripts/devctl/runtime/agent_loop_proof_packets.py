"""Packet and plan evidence readers for agent-loop proof gates."""

from __future__ import annotations

from collections.abc import Mapping

from .agent_loop_proof_context import LoopProofContext
from .agent_loop_proof_plan import plan_row_satisfied
from .agent_loop_proof_rows import packet_rows, session_outcome_rows
from .agent_loop_proof_scope import packet_scoped_to_actor
from .value_coercion import coerce_mapping, coerce_mapping_items, coerce_text


def packet_target_satisfied(
    ctx: LoopProofContext,
    *,
    target_ref: str,
    active_packet_id: str,
) -> bool:
    if not target_ref:
        return bool(active_packet_id)
    if active_packet_id == target_ref:
        return True
    for packet in packet_rows(ctx):
        if coerce_text(packet.get("packet_id")) == target_ref:
            return packet_scoped_to_actor(ctx, packet)
    return False


def plan_target_satisfied(
    ctx: LoopProofContext,
    *,
    target_ref: str,
    plan_target_ref: str,
) -> bool:
    return plan_row_satisfied(ctx, target_ref=target_ref or plan_target_ref)


def guard_evidence_satisfied(ctx: LoopProofContext, *, target_ref: str) -> bool:
    for packet in packet_rows(ctx):
        if target_ref and target_ref not in {
            coerce_text(packet.get("packet_id")),
            coerce_text(packet.get("target_ref")),
        }:
            continue
        if coerce_text(packet.get("full_guard_bundle_evidence")):
            return True
        if packet_has_guard_attestation(packet):
            return True
    return False


def packet_has_guard_attestation(packet: Mapping[str, object]) -> bool:
    event_sources = (
        coerce_mapping_items(packet.get("acted_on_events")),
        coerce_mapping_items(
            coerce_mapping(packet.get("lifecycle_history")).get("acted_on_events")
        ),
    )
    for events in event_sources:
        for event in events:
            attestation = coerce_mapping(event.get("guard_attestation"))
            if attestation and coerce_text(attestation.get("attested_by")):
                return True
    return False


__all__ = [
    "guard_evidence_satisfied",
    "packet_target_satisfied",
    "plan_target_satisfied",
]
