"""Canonical open-findings backlog over governance-review JSONL."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ..governance.ledger_helpers import (
    latest_rows_by_finding,
    optional_line_number,
    optional_text,
)
from ..governance_review_log import (
    append_governance_review_row,
    build_governance_review_row,
    read_governance_review_rows,
)
from ..governance_review_models import GovernanceReviewInput
from .finding_contracts import (
    FINDING_CONTRACT_ID,
    FINDING_SCHEMA_VERSION,
    FindingIdentitySeed,
    FindingRecord,
    build_finding_id,
)
from .review_snapshot_sources import resolve_governance_log_path

_OPEN_VERDICTS = frozenset({"confirmed_issue"})
_SEVERITY_ORDER = ("critical", "high", "medium", "low")


@dataclass(frozen=True, slots=True)
class FindingSeverityCount:
    """One bounded severity bucket in the canonical backlog."""

    severity: str
    count: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FindingBacklog:
    """Single source of truth for latest adjudicated findings."""

    log_path: str
    repo_name: str
    repo_path: str
    total_rows: int = 0
    total_findings: int = 0
    latest_rows: tuple[dict[str, Any], ...] = ()
    open_rows: tuple[dict[str, Any], ...] = ()
    open_findings: tuple[FindingRecord, ...] = ()
    open_severity_counts: tuple[FindingSeverityCount, ...] = ()

    def severity_counts_dict(self) -> dict[str, int]:
        counts = {bucket.severity: bucket.count for bucket in self.open_severity_counts}
        for severity in _SEVERITY_ORDER:
            counts.setdefault(severity, 0)
        return counts

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        payload["log_path"] = self.log_path
        payload["repo_name"] = self.repo_name
        payload["repo_path"] = self.repo_path
        payload["total_rows"] = self.total_rows
        payload["total_findings"] = self.total_findings
        payload["latest_rows"] = list(self.latest_rows)
        payload["open_rows"] = list(self.open_rows)
        payload["open_findings"] = [finding.to_dict() for finding in self.open_findings]
        payload["open_severity_counts"] = [
            bucket.to_dict() for bucket in self.open_severity_counts
        ]
        return payload

    @classmethod
    def from_rows(
        cls,
        *,
        rows: Sequence[Mapping[str, Any]],
        log_path: Path,
        repo_name: str,
        repo_path: str,
    ) -> "FindingBacklog":
        normalized_rows = tuple(
            dict(row) for row in rows if isinstance(row, Mapping)
        )
        latest_rows = tuple(latest_rows_by_finding(list(normalized_rows)))
        open_rows = tuple(
            row for row in latest_rows if optional_text(row.get("verdict")) in _OPEN_VERDICTS
        )
        open_findings = tuple(
            finding
            for finding in (
                _finding_from_review_row(
                    row,
                    repo_name=repo_name,
                    repo_path=repo_path,
                    source_artifact=str(log_path),
                )
                for row in open_rows
            )
            if finding is not None
        )
        severity_counter = Counter(finding.severity for finding in open_findings)
        open_severity_counts = tuple(
            FindingSeverityCount(
                severity=severity,
                count=int(severity_counter.get(severity, 0)),
            )
            for severity in _SEVERITY_ORDER
            if int(severity_counter.get(severity, 0)) > 0
        )
        return cls(
            log_path=str(log_path),
            repo_name=repo_name,
            repo_path=repo_path,
            total_rows=len(normalized_rows),
            total_findings=len(latest_rows),
            latest_rows=latest_rows,
            open_rows=open_rows,
            open_findings=open_findings,
            open_severity_counts=open_severity_counts,
        )

    @classmethod
    def load(
        cls,
        *,
        repo_root: Path,
        governance: object | None,
        max_rows: int = 5_000,
    ) -> "FindingBacklog":
        log_path = resolve_governance_log_path(repo_root, governance)
        rows = read_governance_review_rows(log_path, max_rows=max_rows)
        return cls.from_rows(
            rows=rows,
            log_path=log_path,
            repo_name=repo_root.name,
            repo_path=str(repo_root),
        )


def load_finding_backlog(
    *,
    repo_root: Path,
    governance: object | None,
    max_rows: int = 5_000,
) -> FindingBacklog:
    """Load the canonical finding backlog from the governed review log."""
    return FindingBacklog.load(
        repo_root=repo_root,
        governance=governance,
        max_rows=max_rows,
    )


def load_finding_backlog_from_log(
    *,
    log_path: Path,
    repo_name: str,
    repo_path: str,
    max_rows: int = 5_000,
) -> FindingBacklog:
    """Load the canonical finding backlog from an explicit JSONL path."""
    rows = read_governance_review_rows(log_path, max_rows=max_rows)
    return FindingBacklog.from_rows(
        rows=rows,
        log_path=log_path,
        repo_name=repo_name,
        repo_path=repo_path,
    )


def build_finding_backlog_from_report(
    *,
    report: Mapping[str, Any],
    repo_name: str,
    repo_path: str,
) -> FindingBacklog:
    """Build a backlog from a preloaded governance-review report payload."""
    rows = report.get("recent_findings")
    if not isinstance(rows, list):
        rows = []
    log_path = Path(str(report.get("log_path") or "finding_reviews.jsonl"))
    return FindingBacklog.from_rows(
        rows=rows,
        log_path=log_path,
        repo_name=repo_name,
        repo_path=repo_path,
    )


@dataclass(frozen=True, slots=True)
class FindingBacklogWriteResult:
    """Typed closure from a canonical backlog write.

    Carries the appended JSONL row plus the consumer-side FindingRecord
    projection so callers can verify the write reached the typed backlog
    surface instead of treating the raw row as the only evidence.
    """

    row: dict[str, Any]
    finding: FindingRecord | None
    log_path: str


def record_finding_backlog_row(
    *,
    review_input: GovernanceReviewInput,
    repo_root: Path,
    governance: object | None,
    log_path: Path | None = None,
) -> FindingBacklogWriteResult:
    """Write one governance-review row through the canonical backlog seam.

    Returns a typed FindingBacklogWriteResult so downstream consumers can
    verify the appended row re-projects cleanly through the same reader
    path that load_finding_backlog() uses, closing the write/read loop.
    """
    resolved_log_path = log_path or resolve_governance_log_path(repo_root, governance)
    row = build_governance_review_row(review_input=review_input, repo_root=repo_root)
    append_governance_review_row(row, log_path=resolved_log_path)
    finding = _finding_from_review_row(
        row,
        repo_name=repo_root.name,
        repo_path=str(repo_root),
        source_artifact=str(resolved_log_path),
    )
    return FindingBacklogWriteResult(
        row=row,
        finding=finding,
        log_path=str(resolved_log_path),
    )


def _finding_from_review_row(
    row: Mapping[str, Any],
    *,
    repo_name: str,
    repo_path: str,
    source_artifact: str,
) -> FindingRecord | None:
    file_path = optional_text(row.get("file_path")) or ""
    check_id = optional_text(row.get("check_id")) or ""
    if not file_path or not check_id:
        return None
    signal_type = optional_text(row.get("signal_type")) or "governance-review"
    line = _line_number(row.get("line"))
    finding_id = optional_text(row.get("finding_id")) or build_finding_id(
        FindingIdentitySeed(
            repo_name=repo_name,
            repo_path=repo_path,
            signal_type=signal_type,
            check_id=check_id,
            file_path=file_path,
            symbol=optional_text(row.get("symbol")) or "",
            line=line,
            risk_type=optional_text(row.get("risk_type"))
            or optional_text(row.get("finding_class"))
            or "",
            review_lens=optional_text(row.get("prevention_surface")) or "",
            signals=("confirmed_issue",),
        )
    )
    return FindingRecord(
        schema_version=FINDING_SCHEMA_VERSION,
        contract_id=FINDING_CONTRACT_ID,
        finding_id=finding_id,
        signal_type=signal_type,
        check_id=check_id,
        rule_id=check_id,
        rule_version=1,
        repo_name=optional_text(row.get("repo_name")) or repo_name,
        repo_path=optional_text(row.get("repo_path")) or repo_path,
        file_path=file_path,
        symbol=optional_text(row.get("symbol")) or "",
        line=line,
        severity=optional_text(row.get("severity")) or "medium",
        risk_type=optional_text(row.get("risk_type"))
        or optional_text(row.get("finding_class"))
        or "",
        review_lens=optional_text(row.get("prevention_surface")) or "",
        ai_instruction=optional_text(row.get("notes")) or "",
        signals=("confirmed_issue",),
        source_command=optional_text(row.get("source_command"))
        or "python3 dev/scripts/devctl.py governance-review --format md",
        source_artifact=source_artifact,
    )


def _line_number(value: object) -> int | None:
    try:
        return optional_line_number(value)
    except ValueError:
        return None


__all__ = [
    "FindingBacklog",
    "FindingBacklogWriteResult",
    "FindingSeverityCount",
    "build_finding_backlog_from_report",
    "load_finding_backlog",
    "load_finding_backlog_from_log",
    "record_finding_backlog_row",
]
