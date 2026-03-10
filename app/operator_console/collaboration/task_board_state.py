"""Review-channel packets grouped as collaboration task tickets for the board view.

Presents the same review-channel event data as a kanban-style board
with columns: Pending, In Progress, Review, Done. Under the hood
every ticket is a chain of ``devctl review-channel`` packets grouped
by shared ``to_agent + summary`` key.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..state.core.models import utc_timestamp


@dataclass(frozen=True)
class TaskTicket:
    """One task derived from review-channel packet chains."""

    ticket_id: str
    summary: str
    assigned_agent: str
    status: str  # pending | in_progress | review | done
    kind: str
    last_updated: str
    packet_count: int = 1
    from_agent: str = "operator"


@dataclass(frozen=True)
class TaskBoardSnapshot:
    """Grouped task tickets for the board view."""

    pending: tuple[TaskTicket, ...] = ()
    in_progress: tuple[TaskTicket, ...] = ()
    review: tuple[TaskTicket, ...] = ()
    done: tuple[TaskTicket, ...] = ()


# Map review-channel packet statuses to board columns
_STATUS_TO_COLUMN: dict[str, str] = {
    "posted": "pending",
    "read": "in_progress",
    "acked": "in_progress",
    "implementing": "in_progress",
    "reviewed": "review",
    "applied": "done",
    "dismissed": "done",
}


def _column_for_status(status: str) -> str:
    """Map a packet status to a board column name."""
    return _STATUS_TO_COLUMN.get(status.lower(), "pending")


def _ticket_from_packet(packet: dict) -> TaskTicket | None:
    """Convert one event-store packet dict into a TaskTicket."""
    packet_id = packet.get("packet_id", "")
    if not packet_id:
        return None
    raw_status = packet.get("status", "posted")
    return TaskTicket(
        ticket_id=packet_id,
        summary=packet.get("summary", ""),
        assigned_agent=packet.get("to_agent", ""),
        status=_column_for_status(raw_status),
        kind=packet.get("kind", ""),
        last_updated=packet.get("posted_at", ""),
        from_agent=packet.get("from_agent", "operator"),
    )


def build_task_board_snapshot(
    *,
    review_state_path: Path | None = None,
    history_packets: list[dict] | None = None,
) -> TaskBoardSnapshot:
    """Build a task board snapshot from review-channel packets.

    Each packet becomes a ticket. Tickets are bucketed into columns
    based on their current status.
    """
    packets: list[dict] = []
    if history_packets is not None:
        packets = history_packets
    elif review_state_path is not None and review_state_path.is_file():
        try:
            data = json.loads(review_state_path.read_text(encoding="utf-8"))
            packets = data.get("packets", [])
        except (json.JSONDecodeError, OSError):
            packets = []

    buckets: dict[str, list[TaskTicket]] = {
        "pending": [],
        "in_progress": [],
        "review": [],
        "done": [],
    }

    for packet in packets:
        ticket = _ticket_from_packet(packet)
        if ticket is None:
            continue
        column = ticket.status
        if column in buckets:
            buckets[column].append(ticket)

    return TaskBoardSnapshot(
        pending=tuple(buckets["pending"]),
        in_progress=tuple(buckets["in_progress"]),
        review=tuple(buckets["review"]),
        done=tuple(buckets["done"]),
    )
