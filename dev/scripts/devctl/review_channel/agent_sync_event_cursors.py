"""Event cursor helpers for the agent-sync projection."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from .event_models import event_id_rank as _event_id_rank

_LOWER_BOUND_CONSUMPTION_EVENT_TYPES: frozenset[str] = frozenset(
    {"packet_acked", "packet_applied", "packet_dismissed"}
)


def _is_consumption_by_agent(
    event: Mapping[str, object],
    agent_id: str,
    events: list[dict[str, object]],
) -> bool:
    """Return True if this event represents lower-bound consumption by agent."""
    del events
    event_type = str(event.get("event_type") or "")
    if event_type not in _LOWER_BOUND_CONSUMPTION_EVENT_TYPES:
        return False
    metadata = event.get("metadata")
    actor = ""
    if isinstance(metadata, Mapping):
        actor = str(metadata.get("actor") or "").strip()
    if not actor:
        actor = str(event.get("actor") or "").strip()
    return bool(actor) and actor == agent_id


def _max_event_id_where(
    events: Iterable[Mapping[str, object]],
    predicate,
) -> str:
    """Return the max event_id among events matching predicate, or empty string."""
    best_rank = -1
    best_id = ""
    for event in events:
        if not predicate(event):
            continue
        eid = str(event.get("event_id") or "")
        rank = _event_id_rank(eid)
        if rank > best_rank:
            best_rank = rank
            best_id = eid
    return best_id


def _latest_event_id(events: Iterable[Mapping[str, object]]) -> str:
    """Return the max event_id across all events."""
    return _max_event_id_where(events, lambda _e: True)
