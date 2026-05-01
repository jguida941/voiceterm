"""Scope matching helpers for agent-loop proof evidence."""

from __future__ import annotations

from collections.abc import Mapping

from .agent_loop_proof_context import LoopProofContext
from .value_coercion import coerce_text


def packet_scoped_to_actor(
    ctx: LoopProofContext,
    packet: Mapping[str, object],
) -> bool:
    to_agent = coerce_text(packet.get("to_agent")).lower()
    if to_agent and to_agent != coerce_text(ctx.actor).lower():
        return False
    target_role = coerce_text(packet.get("target_role")).lower()
    if target_role and target_role != coerce_text(ctx.role).lower():
        return False
    target_session = coerce_text(packet.get("target_session_id"))
    return not target_session or not ctx.session or target_session == ctx.session


def row_matches_scope(
    ctx: LoopProofContext,
    row: Mapping[str, object],
    *,
    target_ref: str,
) -> bool:
    actor = coerce_text(row.get("actor_id") or row.get("session_actor_id")).lower()
    if actor and actor != coerce_text(ctx.actor).lower():
        return False
    role = coerce_text(row.get("role") or row.get("session_actor_role")).lower()
    if role and role != coerce_text(ctx.role).lower():
        return False
    session = coerce_text(row.get("session_id") or row.get("target_session_id"))
    if session and ctx.session and session != ctx.session:
        return False
    if target_ref and target_ref not in {
        coerce_text(row.get("target_ref")),
        coerce_text(row.get("packet_id")),
        coerce_text(row.get("handoff_packet_id")),
    }:
        return False
    return True


__all__ = ["packet_scoped_to_actor", "row_matches_scope"]
