"""Round proof evidence for agent-loop advancement."""

from __future__ import annotations

from .agent_loop_proof_context import LoopProofContext
from .agent_loop_proof_rows import round_proof_rows
from .agent_loop_proof_scope import row_matches_scope
from .value_coercion import coerce_text


def round_proof_satisfied(ctx: LoopProofContext, *, target_ref: str) -> bool:
    for row in round_proof_rows(ctx):
        if not row_matches_scope(ctx, row, target_ref=target_ref):
            continue
        if coerce_text(row.get("status")) in {
            "accepted",
            "satisfied",
            "complete",
            "completed",
        }:
            return True
        if coerce_text(row.get("proof_state")) == "satisfied":
            return True
    return False


__all__ = ["round_proof_satisfied"]
