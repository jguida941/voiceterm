"""Session outcome evidence for agent-loop proof gates."""

from __future__ import annotations

from .agent_loop_proof_context import LoopProofContext
from .agent_loop_proof_rows import session_outcome_rows
from .value_coercion import coerce_text


def completed_handoff_satisfied(ctx: LoopProofContext, *, target_ref: str) -> bool:
    for outcome in session_outcome_rows(ctx):
        if coerce_text(outcome.get("outcome")) != "completed_handoff":
            continue
        if target_ref and target_ref not in {
            coerce_text(outcome.get("handoff_packet_id")),
            coerce_text(outcome.get("target_ref")),
        }:
            continue
        return True
    return False


__all__ = ["completed_handoff_satisfied"]
