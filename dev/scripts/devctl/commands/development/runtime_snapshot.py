"""Runtime collaboration snapshot for the typed `/develop` controller."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from .models import DevelopmentRuntimeRow, DevelopmentRuntimeSnapshot
from .session_discovery import discover_sessions_for_runtime

_AUTHORITY_SOURCE = "AgentWorkBoardProjection+AgentSyncProjection"
_DEFAULT_ROW_LIMIT = 8


def runtime_snapshot_from_review_state(
    review_state: Mapping[str, object],
    *,
    repo_root: Path,
    actor: str,
    actor_source: str = "",
    row_limit: int = _DEFAULT_ROW_LIMIT,
) -> DevelopmentRuntimeSnapshot:
    """Project typed shared-work state into a compact `/develop` section."""
    work_board = _mapping(review_state.get("agent_work_board"))
    agent_sync = _mapping(review_state.get("agent_sync"))
    coordination = _mapping(review_state.get("coordination_state"))
    rows = tuple(_runtime_row(row) for row in _row_payloads(work_board))
    ordered_rows = tuple(sorted(rows, key=_row_sort_key)[: max(1, row_limit)])
    session_discovery = discover_sessions_for_runtime(
        repo_root=repo_root,
        registered_sessions=_registered_sessions(rows),
    )
    unregistered_count = sum(1 for row in session_discovery if not row.registered)
    stale_count = sum(1 for row in rows if row.confidence_class == "stale")
    fresh_count = len(rows) - stale_count
    actor_sync = _mapping(_mapping(agent_sync.get("agents")).get(actor))
    pending_packets = _sequence(actor_sync.get("pending_packets_to_me"))
    topology = _text(coordination.get("coordination_topology"))
    authority_mode = _text(coordination.get("authority_mode"))
    return DevelopmentRuntimeSnapshot(
        actor=actor,
        actor_source=actor_source,
        authority_source=_AUTHORITY_SOURCE,
        coordination_topology=topology,
        authority_mode=authority_mode,
        safe_to_fanout=bool(review_state.get("safe_to_fanout")),
        actor_sync_status=_text(actor_sync.get("derived_status")),
        actor_pending_packet_count=len(pending_packets),
        fresh_row_count=fresh_count,
        stale_row_count=stale_count,
        discovered_session_count=len(session_discovery),
        unregistered_session_count=unregistered_count,
        rows=ordered_rows,
        session_discovery=session_discovery,
        summary=_runtime_summary(
            topology=topology,
            pending_packet_count=len(pending_packets),
            stale_row_count=stale_count,
            unregistered_session_count=unregistered_count,
        ),
    )


def _runtime_row(row: Mapping[str, object]) -> DevelopmentRuntimeRow:
    return DevelopmentRuntimeRow(
        actor_id=_text(row.get("actor_id")),
        provider=_text(row.get("provider")),
        role=_text(row.get("role")),
        session_id=_text(row.get("session_id")),
        status=_text(row.get("status")),
        confidence_class=_text(row.get("confidence_class")),
        idle_seconds=_int(row.get("idle_seconds")),
        mutation_mode=_text(row.get("mutation_mode")),
        active_packet_id=_text(row.get("active_packet_id")),
        attention_packet_id=_text(row.get("attention_packet_id")),
        executing_packet_id=_text(row.get("executing_packet_id")),
        plan_row_id=_text(row.get("plan_row_id")),
        source_event_id=_text(row.get("source_event_id")),
        worktree_identity=_text(row.get("worktree_identity")),
        branch=_text(row.get("branch")),
    )


def _runtime_summary(
    *,
    topology: str,
    pending_packet_count: int,
    stale_row_count: int,
    unregistered_session_count: int,
) -> str:
    parts: list[str] = []
    if topology:
        parts.append(f"topology={topology}")
    parts.append(f"actor_pending_packets={pending_packet_count}")
    if stale_row_count:
        parts.append(f"stale_runtime_rows={stale_row_count}")
    if unregistered_session_count:
        parts.append(f"unregistered_sessions={unregistered_session_count}")
    return "; ".join(parts)


def _registered_sessions(
    rows: tuple[DevelopmentRuntimeRow, ...],
) -> set[tuple[str, str]]:
    return {
        (row.provider, row.session_id)
        for row in rows
        if row.provider and row.session_id
    }


def _row_payloads(work_board: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    rows = work_board.get("rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def _row_sort_key(row: DevelopmentRuntimeRow) -> tuple[int, int, str, str]:
    stale_rank = 1 if row.confidence_class == "stale" else 0
    return (stale_rank, row.idle_seconds, row.actor_id, row.session_id)


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(value)
    return ()


def _text(value: object) -> str:
    return str(value or "").strip()


def _int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


__all__ = ["runtime_snapshot_from_review_state"]
