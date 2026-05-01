"""Participant lookup helpers for agent work-board projection."""

from __future__ import annotations

from collections.abc import Mapping


def index_participants_by_role(
    collaboration: Mapping[str, object],
) -> dict[tuple[str, str], Mapping[str, object]]:
    participants = collaboration.get("participants") if collaboration else None
    if not isinstance(participants, list | tuple):
        return {}
    indexed: dict[tuple[str, str], Mapping[str, object]] = {}
    for entry in participants:
        if not isinstance(entry, Mapping):
            continue
        agent_id = str(entry.get("agent_id") or "").strip()
        role = str(entry.get("role") or "").strip()
        if not agent_id:
            continue
        if role:
            indexed[(agent_id, role)] = entry
        indexed.setdefault((agent_id, ""), entry)
    return indexed


def resolve_participant(
    participants_by_role: dict[tuple[str, str], Mapping[str, object]],
    *,
    actor_id: str,
    role: str,
) -> Mapping[str, object] | None:
    if not actor_id:
        return None
    entry = participants_by_role.get((actor_id, role))
    if entry is not None:
        return entry
    return participants_by_role.get((actor_id, ""))
