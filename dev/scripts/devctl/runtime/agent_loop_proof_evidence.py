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
from .value_coercion import (
    coerce_bool,
    coerce_mapping as _mapping,
    coerce_text as _text,
)


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
    if peer_digest_sidecar_observation_satisfied(ctx):
        satisfied.add("peer_digest_sidecar_observation")
    if completed_handoff_satisfied(ctx, target_ref=target_ref):
        satisfied.add("implementer_handoff")
    if guard_evidence_satisfied(ctx, target_ref=target_ref):
        satisfied.add("guard_bundle_or_attestation")
    if reviewer_proof_satisfied(ctx):
        satisfied.add("reviewer_semantic_review")
    if round_proof_satisfied(ctx, target_ref=target_ref):
        satisfied.add("round_proof")
    return frozenset(satisfied)


def peer_digest_sidecar_observation_satisfied(ctx: LoopProofContext) -> bool:
    """Return True when the actor has a current peer digest observation."""
    minds = _mapping(ctx.review_state.get("agent_minds"))
    actor_mind = _mapping(minds.get(ctx.actor))
    awareness = _mapping(actor_mind.get("peer_awareness"))
    if not awareness:
        return False
    if coerce_bool(awareness.get("due")):
        return False
    return bool(_text(awareness.get("last_peer_poll_at_utc")))


__all__ = ["peer_digest_sidecar_observation_satisfied", "satisfied_proofs"]
