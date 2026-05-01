"""Runtime attention and reviewer proof readers for agent-loop gates."""

from __future__ import annotations

from .agent_loop_proof_context import LoopProofContext
from .agent_loop_proof_rows import reviewer_runtime
from .value_coercion import coerce_mapping, coerce_text


def wake_or_attention_satisfied(
    ctx: LoopProofContext,
    *,
    active_packet_id: str,
) -> bool:
    attention = coerce_mapping(ctx.attention)
    override = ctx.operator_override
    return bool(
        active_packet_id
        or override.active
        or attention.get("wake_required")
        or attention.get("pivot_required")
        or coerce_text(attention.get("latest_attention_packet_id"))
    )


def reviewer_proof_satisfied(ctx: LoopProofContext) -> bool:
    runtime = reviewer_runtime(ctx)
    duty = coerce_mapping(runtime.get("duty_proof"))
    acceptance = coerce_mapping(runtime.get("review_acceptance"))
    source = coerce_text(duty.get("semantic_review_source"))
    if source in {"agent_mind", "agent_mind_auxiliary"}:
        return bool(acceptance.get("review_accepted"))
    return (
        coerce_text(duty.get("state")) == "healthy"
        and bool(duty.get("semantic_review_claimed"))
        and bool(coerce_text(duty.get("reviewed_diff_hash")))
    ) or bool(acceptance.get("review_accepted"))


__all__ = ["reviewer_proof_satisfied", "wake_or_attention_satisfied"]
