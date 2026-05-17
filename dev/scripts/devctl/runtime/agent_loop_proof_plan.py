"""MasterPlan/PlanRow proof readers for agent-loop policy."""

from __future__ import annotations

from collections.abc import Mapping

from .agent_loop_proof_context import LoopProofContext
from .value_coercion import (
    coerce_mapping,
    coerce_mapping_items,
    coerce_string_items,
    coerce_text,
)


def plan_row_satisfied(ctx: LoopProofContext, *, target_ref: str) -> bool:
    """Return true only when a typed PlanRow owns the requested target."""
    ref = coerce_text(target_ref)
    if not ref:
        return False
    for row in _plan_rows(ctx):
        if ref in _row_refs(row):
            return True
    return False


def _plan_rows(ctx: LoopProofContext) -> tuple[Mapping[str, object], ...]:
    master_plan = coerce_mapping(ctx.master_plan)
    rows = coerce_mapping_items(master_plan.get("rows"))
    if rows:
        return rows
    review_master_plan = coerce_mapping(ctx.review_state.get("master_plan"))
    return coerce_mapping_items(review_master_plan.get("rows"))


def _row_refs(row: Mapping[str, object]) -> frozenset[str]:
    refs = {
        coerce_text(row.get("row_id")),
        coerce_text(row.get("target_ref")),
    }
    refs.update(coerce_string_items(row.get("anchor_refs")))
    return frozenset(ref for ref in refs if ref)


__all__ = ["plan_row_satisfied"]
