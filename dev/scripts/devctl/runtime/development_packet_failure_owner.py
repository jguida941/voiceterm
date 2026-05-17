"""Known packet-failure class ownership for ``/develop``."""

from __future__ import annotations

from collections.abc import Mapping

from .master_plan_contract import PlanRow

CLOCK_EXPIRED_WITHOUT_DISPOSITION = "clock_expired_without_disposition"
PACKET_INTAKE_CLASS_OWNER_ROWS = (
    "MP377-P0-PACKET-INTAKE-SCHEDULER-S1",
    "MP377-GUARDIR-PACKET-DURABLE-INGESTION",
)


def class_owner_by_packet_failure(rows: tuple[PlanRow, ...]) -> dict[str, str]:
    """Return plan rows that own known packet failure classes."""
    owner_row = _preferred_owner_row(rows)
    if not owner_row:
        return {}
    return {CLOCK_EXPIRED_WITHOUT_DISPOSITION: owner_row}


def packet_failure_class(packet: Mapping[str, object]) -> str:
    """Return an archive failure class from a packet disposition."""
    disposition = packet.get("disposition")
    if not isinstance(disposition, Mapping):
        return ""
    classification = _text(disposition.get("archive_classification"))
    if classification:
        return classification
    return _resolution_anchor_classification(disposition)


def _resolution_anchor_classification(disposition: Mapping[str, object]) -> str:
    resolution_anchor = _text(disposition.get("resolution_anchor"))
    prefix = "archive_classification:"
    if resolution_anchor.startswith(prefix):
        return resolution_anchor[len(prefix) :]
    return ""


def _preferred_owner_row(rows: tuple[PlanRow, ...]) -> str:
    available = {
        row.row_id: _text(row.status).lower()
        for row in rows
        if row.row_id in PACKET_INTAKE_CLASS_OWNER_ROWS
    }
    for row_id in PACKET_INTAKE_CLASS_OWNER_ROWS:
        status = available.get(row_id)
        if status and status not in {"done", "closed", "completed", "superseded"}:
            return row_id
    return ""


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "CLOCK_EXPIRED_WITHOUT_DISPOSITION",
    "PACKET_INTAKE_CLASS_OWNER_ROWS",
    "class_owner_by_packet_failure",
    "packet_failure_class",
]
