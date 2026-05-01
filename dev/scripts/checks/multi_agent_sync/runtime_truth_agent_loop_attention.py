"""Agent-sync attention checks for multi-agent runtime truth."""

from __future__ import annotations

from collections.abc import Mapping

from dev.scripts.devctl.runtime.value_coercion import (
    coerce_mapping,
    coerce_text,
)


def agent_sync_attention_scope_errors(
    payload: Mapping[str, object],
    decision_rows: list[Mapping[str, object]],
) -> list[str]:
    """Reject stale agent-level attention when session routes disagree."""
    scoped_by_actor = _scoped_attention_by_actor(decision_rows)
    if not scoped_by_actor:
        return []

    sync_agents = coerce_mapping(coerce_mapping(payload.get("agent_sync")).get("agents"))
    errors: list[str] = []
    for actor, scoped_ids in sorted(scoped_by_actor.items()):
        agent_row = coerce_mapping(sync_agents.get(actor))
        aggregate_attention = coerce_text(agent_row.get("attention_packet_id"))
        if not aggregate_attention:
            continue
        if len(scoped_ids) > 1:
            errors.append(
                "Agent sync exposes an unscoped attention packet while typed "
                f"session routes disagree for {actor}: "
                f"agent_sync={aggregate_attention}; "
                f"session_packets={', '.join(sorted(scoped_ids))}"
            )
        elif aggregate_attention not in scoped_ids:
            errors.append(
                "Agent sync attention packet disagrees with typed session "
                f"route for {actor}: agent_sync={aggregate_attention}; "
                f"session_packet={next(iter(scoped_ids))}"
            )
    return errors


def _scoped_attention_by_actor(
    decision_rows: list[Mapping[str, object]],
) -> dict[str, set[str]]:
    scoped_by_actor: dict[str, set[str]] = {}
    for row in decision_rows:
        actor = coerce_text(row.get("actor_id"))
        packet_id = coerce_text(row.get("attention_packet_id")) or coerce_text(
            row.get("active_packet_id")
        )
        if actor and packet_id:
            scoped_by_actor.setdefault(actor, set()).add(packet_id)
    return scoped_by_actor
