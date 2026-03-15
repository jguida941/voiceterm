"""Review-channel packets grouped as collaboration task tickets for the board view.

Presents the same review-channel event data as a kanban-style board
with columns: Pending, In Progress, Review, Done. Under the hood
every ticket is a chain of ``devctl review-channel`` packets grouped
by shared ``to_agent + summary`` key.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dev.scripts.devctl.runtime import ReviewPacketState

from ..state.review.review_state import load_review_packets


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


def _packet_field(packet: dict[str, object] | ReviewPacketState, field_name: str) -> str:
    if isinstance(packet, ReviewPacketState):
        return str(getattr(packet, field_name, ""))
    return str(packet.get(field_name, ""))


def _ticket_from_packet(
    packet: dict[str, object] | ReviewPacketState,
) -> TaskTicket | None:
    """Convert one event-store packet dict into a TaskTicket."""
    packet_id = _packet_field(packet, "packet_id")
    if not packet_id:
        return None
    raw_status = _packet_field(packet, "status") or "posted"
    return TaskTicket(
        ticket_id=packet_id,
        summary=_packet_field(packet, "summary"),
        assigned_agent=_packet_field(packet, "to_agent"),
        status=_column_for_status(raw_status),
        kind=_packet_field(packet, "kind"),
        last_updated=_packet_field(packet, "posted_at"),
        from_agent=_packet_field(packet, "from_agent") or "operator",
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
    packets: list[dict[str, object] | ReviewPacketState] = []
    if history_packets is not None:
        packets = history_packets
    elif review_state_path is not None and review_state_path.is_file():
        try:
            packets = list(load_review_packets(review_state_path))
        except (OSError, ValueError):
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
