"""Report section helpers for event-backed sync-status output."""

from __future__ import annotations

from ...review_channel.event_models import event_id_rank as _event_id_rank


def diff_window(*, args, sync: dict[str, object], agents_block: dict[str, object]):
    since_event_id = (getattr(args, "since_event_id", None) or "").strip()
    if not since_event_id:
        return None
    return {
        "from_event_id": since_event_id,
        "to_event_id": str(sync.get("source_latest_event_id") or ""),
        "advanced_agents": [
            aid
            for aid, row in agents_block.items()
            if _row_advanced_past_cursor(row, since_event_id)
        ],
    }


def work_board_section(
    work_board: dict[str, object],
    *,
    target_agent: str,
) -> dict[str, object]:
    return {
        "schema_version": int(work_board.get("schema_version") or 0),
        "contract_id": str(work_board.get("contract_id") or ""),
        "source_latest_event_id": str(work_board.get("source_latest_event_id") or ""),
        "event_index": str(work_board.get("event_index") or ""),
        "projection_refresh_seq": int(work_board.get("projection_refresh_seq") or 0),
        "refreshed_at_utc": str(work_board.get("refreshed_at_utc") or ""),
        "rows": _filter_work_board_rows(
            work_board.get("rows") or [],
            target_agent=target_agent,
        ),
        "barriers": list(work_board.get("barriers") or []),
    }


def coordination_section(coordination: dict[str, object]) -> dict[str, object]:
    return {
        "contract_id": str(coordination.get("contract_id") or ""),
        "schema_version": int(coordination.get("schema_version") or 0),
        "coordination_topology": str(
            coordination.get("coordination_topology") or "unknown"
        ),
        "legacy_topology_label": str(
            coordination.get("legacy_topology_label") or ""
        ),
        "authority_mode": str(coordination.get("authority_mode") or "unknown"),
        "recovery_eligibility": str(
            coordination.get("recovery_eligibility") or "unknown"
        ),
        "legacy_reviewer_mode": str(coordination.get("legacy_reviewer_mode") or ""),
        "legacy_authority_label": str(
            coordination.get("legacy_authority_label") or ""
        ),
        "observed_runtime": dict(coordination.get("observed_runtime") or {}),
        "notes": list(coordination.get("notes") or []),
    }


def _filter_work_board_rows(
    rows: list[object],
    *,
    target_agent: str,
) -> list[object]:
    if not target_agent:
        return list(rows)
    return [
        row
        for row in rows
        if isinstance(row, dict) and str(row.get("actor_id") or "") == target_agent
    ]


def _row_advanced_past_cursor(row: object, since_event_id: str) -> bool:
    if not isinstance(row, dict):
        return False
    cursor_rank = _event_id_rank(since_event_id)
    emit_rank = _event_id_rank(str(row.get("last_packet_emitted_event_id") or ""))
    consumed_rank = _event_id_rank(
        str(row.get("last_consumed_event_id_lower_bound") or "")
    )
    return emit_rank > cursor_rank or consumed_rank > cursor_rank
