"""Actor ordering helpers for collaboration-session authority rows."""

from __future__ import annotations


def ordered_actor_ids(inputs: object) -> tuple[str, ...]:
    actor_ids: list[str] = []
    for assignment in inputs.role_assignments:
        _append_actor_id(actor_ids, assignment.agent_id or assignment.provider)
    for participant in inputs.participants:
        _append_actor_id(actor_ids, participant.agent_id or participant.provider)
    return tuple(actor_ids)


def _append_actor_id(actor_ids: list[str], actor_id: str) -> None:
    normalized = str(actor_id or "").strip().lower()
    if normalized and normalized not in actor_ids:
        actor_ids.append(normalized)
