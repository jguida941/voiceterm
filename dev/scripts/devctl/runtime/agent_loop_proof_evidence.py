"""Aggregate proof evidence for agent-loop advancement."""

from __future__ import annotations

from .agent_loop_proof_context import LoopProofContext
from .agent_loop_proof_packets import (
    guard_evidence_satisfied,
    packet_target_satisfied,
    plan_target_satisfied,
)
from .agent_loop_proof_round import round_proof_satisfied
from .agent_loop_proof_runtime import (
    reviewer_proof_satisfied,
    wake_or_attention_satisfied,
)
from .agent_loop_proof_sessions import completed_handoff_satisfied


def satisfied_proofs(
    *,
    ctx: LoopProofContext,
    active_packet_id: str,
    plan_target_ref: str,
    target_kind: str,
    target_ref: str,
) -> frozenset[str]:
    satisfied: set[str] = set()
    if ctx.clock.get("source_latest_event_id") or ctx.clock.get("snapshot_id"):
        satisfied.add("typed_runtime_clock")
    if target_kind == "packet" and packet_target_satisfied(
        ctx,
        target_ref=target_ref,
        active_packet_id=active_packet_id,
    ):
        satisfied.add("scoped_packet_target")
    if target_kind == "plan" and plan_target_satisfied(
        ctx,
        target_ref=target_ref,
        plan_target_ref=plan_target_ref,
    ):
        satisfied.add("plan_target")
    if wake_or_attention_satisfied(ctx, active_packet_id=active_packet_id):
        satisfied.add("packet_attention_evidence")
    if completed_handoff_satisfied(ctx, target_ref=target_ref):
        satisfied.add("implementer_handoff")
    if guard_evidence_satisfied(ctx, target_ref=target_ref):
        satisfied.add("guard_bundle_or_attestation")
    if reviewer_proof_satisfied(ctx):
        satisfied.add("reviewer_semantic_review")
    if round_proof_satisfied(ctx, target_ref=target_ref):
        satisfied.add("round_proof")
    return frozenset(satisfied)


__all__ = ["satisfied_proofs"]
