"""Row readers for agent-loop proof evidence."""

from __future__ import annotations

from collections.abc import Mapping

from .agent_loop_proof_context import LoopProofContext
from .value_coercion import coerce_mapping, coerce_mapping_items


def reviewer_runtime(ctx: LoopProofContext) -> Mapping[str, object]:
    return coerce_mapping(ctx.review_state.get("reviewer_runtime"))


def packet_rows(ctx: LoopProofContext) -> tuple[Mapping[str, object], ...]:
    return coerce_mapping_items(ctx.review_state.get("packets"))


def session_outcome_rows(ctx: LoopProofContext) -> tuple[Mapping[str, object], ...]:
    collaboration = coerce_mapping(ctx.review_state.get("collaboration"))
    return coerce_mapping_items(collaboration.get("session_outcomes"))


def round_proof_rows(ctx: LoopProofContext) -> tuple[Mapping[str, object], ...]:
    return coerce_mapping_items(ctx.review_state.get("round_proofs"))


__all__ = [
    "packet_rows",
    "reviewer_runtime",
    "round_proof_rows",
    "session_outcome_rows",
]
