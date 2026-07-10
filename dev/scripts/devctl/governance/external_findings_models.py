"""Typed models for imported external governance findings."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ExternalFindingInput:
    """Normalized input for one imported raw finding row."""

    file_path: str
    repo_name: str | None = None
    repo_path: str | None = None
    check_id: str | None = None
    signal_type: str | None = None
    title: str | None = None
    summary: str | None = None
    evidence: str | None = None
    severity: str | None = None
    risk_type: str | None = None
    symbol: str | None = None
    line: int | None = None
    end_line: int | None = None
    source_model: str | None = None
    source_command: str | None = None
    source_artifact: str | None = None
    source_row: int | None = None
    scan_mode: str | None = None
    import_run_id: str | None = None
    notes: str | None = None
    finding_id: str | None = None


@dataclass(frozen=True)
class ExternalFindingBucketStat:
    """One grouped imported-finding metric row."""

    bucket: str
    total_findings: int
    reviewed_count: int
    adjudication_coverage_pct: float
    false_positive_count: int
    fixed_count: int
    confirmed_issue_count: int
    deferred_count: int
    waived_count: int


@dataclass(frozen=True)
class ExternalFindingStats:
    """Rolled-up imported-finding corpus metrics for one snapshot."""

    total_rows: int
    total_findings: int
    unique_repo_count: int
    unique_import_run_count: int
    reviewed_count: int
    unreviewed_count: int
    adjudication_coverage_pct: float
    false_positive_count: int
    fixed_count: int
    confirmed_issue_count: int
    deferred_count: int
    waived_count: int
    by_repo: tuple[ExternalFindingBucketStat, ...]
    by_check_id: tuple[ExternalFindingBucketStat, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert nested stats into plain JSON-friendly dicts."""
        return asdict(self)
