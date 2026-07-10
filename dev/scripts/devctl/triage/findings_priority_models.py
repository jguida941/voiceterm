"""Typed models for findings-priority parsing and ranking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AccumulatedFinding:
    """One normalized finding section from the LIVE_RUN log."""

    qid: str
    heading: str
    severity: str
    severity_rank: int
    raw_severity: str
    status: str
    summary: str
    file_refs: tuple[str, ...]
    resolution_state: str

    def to_dict(self) -> dict[str, Any]:
        return dict(
            qid=self.qid,
            heading=self.heading,
            severity=self.severity,
            severity_rank=self.severity_rank,
            raw_severity=self.raw_severity,
            status=self.status,
            summary=self.summary,
            file_refs=list(self.file_refs),
            resolution_state=self.resolution_state,
        )


@dataclass(frozen=True, slots=True)
class RankedFinding:
    """A normalized finding plus graph-derived priority evidence."""

    rank: int
    qid: str
    heading: str
    severity: str
    severity_rank: int
    status: str
    summary: str
    resolution_state: str
    primary_file: str
    file_refs: tuple[str, ...]
    matched_file_refs: tuple[str, ...]
    max_fan_out: int
    fan_out_by_file: tuple[tuple[str, int], ...]

    def to_dict(self) -> dict[str, Any]:
        return dict(
            rank=self.rank,
            qid=self.qid,
            heading=self.heading,
            severity=self.severity,
            severity_rank=self.severity_rank,
            status=self.status,
            summary=self.summary,
            resolution_state=self.resolution_state,
            primary_file=self.primary_file,
            file_refs=list(self.file_refs),
            matched_file_refs=list(self.matched_file_refs),
            max_fan_out=self.max_fan_out,
            fan_out_by_file=[
                dict(file=file_path, fan_out=fan_out)
                for file_path, fan_out in self.fan_out_by_file
            ],
        )


__all__ = ["AccumulatedFinding", "RankedFinding"]
