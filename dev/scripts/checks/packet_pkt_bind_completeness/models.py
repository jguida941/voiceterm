"""Data models for the packet PKT-BIND completeness guard."""

from __future__ import annotations

from datetime import datetime
from typing import NamedTuple


class TaskStart(NamedTuple):
    line_number: int
    packet_id: str
    timestamp_utc: datetime
    summary: str
    correlation_id: str
    target_ref: str


class PacketBindGap(NamedTuple):
    line_number: int
    packet_id: str
    scope: str
    deadline_reason: str
    age_minutes: int
    detail: str

    def to_dict(self) -> dict[str, object]:
        return {
            "line_number": self.line_number,
            "packet_id": self.packet_id,
            "scope": self.scope,
            "deadline_reason": self.deadline_reason,
            "age_minutes": self.age_minutes,
            "detail": self.detail,
        }
