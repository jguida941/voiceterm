"""Runtime row readers for watcher lease projection."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime_rows_common import int_or_none, mapping, text, work_board_rows


def watched_actor(review_state: Mapping[str, object], *, actor: str) -> str:
    authority = mapping(review_state.get("authority_snapshot"))
    packet_target = mapping(authority.get("packet_target"))
    target = text(packet_target.get("agent"))
    if target:
        return target
    return "claude" if actor != "claude" else "codex"


def last_seen_event_id(review_state: Mapping[str, object], actor: str) -> str:
    ids = [
        text(row.get("source_event_id"))
        for row in work_board_rows(review_state)
        if text(row.get("actor_id")) == actor
    ]
    ids = [item for item in ids if item]
    return sorted(ids)[-1] if ids else ""


def runtime_actor_idle_seconds(
    review_state: Mapping[str, object],
    actor: str,
) -> int | None:
    idle_values = [
        int_or_none(row.get("idle_seconds"))
        for row in work_board_rows(review_state)
        if text(row.get("actor_id")) == actor
        and text(row.get("confidence_class")) != "stale"
    ]
    idle_values = [value for value in idle_values if value is not None]
    if not idle_values:
        return None
    return min(idle_values)


__all__ = [
    "last_seen_event_id",
    "runtime_actor_idle_seconds",
    "watched_actor",
]
