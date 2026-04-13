"""Typed contracts for persisted dogfood coverage and report state."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

DOGFOOD_RECORD_CONTRACT_ID = "DogfoodRun"
DOGFOOD_RECORD_SCHEMA_VERSION = 1
DOGFOOD_REPORT_CONTRACT_ID = "DogfoodReport"
DOGFOOD_REPORT_SCHEMA_VERSION = 1

VALID_DOGFOOD_TARGET_KINDS: tuple[str, ...] = (
    "command",
    "guard",
    "probe",
    "role",
)
VALID_DOGFOOD_STATUSES: tuple[str, ...] = (
    "passed",
    "failed",
    "blocked",
    "skipped",
)
DOGFOOD_ROLE_TARGET_IDS: tuple[str, ...] = (
    "reviewer",
    "implementer",
    "dashboard",
)


@dataclass(frozen=True, slots=True)
class DogfoodRecordInput:
    """Normalized input for one persisted dogfood execution record."""

    target_kind: str
    target_id: str
    status: str
    actor: str | None = None
    provider: str | None = None
    run_label: str | None = None
    source_command: str | None = None
    artifact_path: str | None = None
    repo_name: str | None = None
    repo_path: str | None = None
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class DogfoodRecord:
    """One durable dogfood run row stored in JSONL."""

    record_id: str
    timestamp_utc: str
    contract_id: str
    schema_version: int
    repo_name: str
    repo_path: str
    target_kind: str
    target_id: str
    status: str
    actor: str = ""
    provider: str = ""
    run_label: str = ""
    source_command: str = ""
    artifact_path: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert the record into a JSON-safe payload."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DogfoodCoverageBucket:
    """Coverage summary for one dogfood target family."""

    target_kind: str
    catalog_total: int
    covered_total: int
    coverage_pct: float
    passed_total: int
    failed_total: int
    blocked_total: int
    skipped_total: int
    uncovered_ids: tuple[str, ...] = ()
    unknown_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["uncovered_ids"] = list(self.uncovered_ids)
        payload["unknown_ids"] = list(self.unknown_ids)
        return payload


@dataclass(frozen=True, slots=True)
class DogfoodGovernanceSummary:
    """Optional dogfood-specific finding summary from governance-review."""

    total_findings: int = 0
    open_findings: int = 0
    fixed_findings: int = 0
    recent_findings: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["recent_findings"] = list(self.recent_findings)
        return payload


@dataclass(frozen=True, slots=True)
class DogfoodReport:
    """Typed rendered summary for dogfood coverage and recent failures."""

    contract_id: str
    schema_version: int
    generated_at_utc: str
    log_path: str
    summary_root: str
    total_rows: int
    latest_recorded_at_utc: str
    coverage: tuple[DogfoodCoverageBucket, ...]
    recent_records: tuple[DogfoodRecord, ...]
    governance_summary: DogfoodGovernanceSummary

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "schema_version": self.schema_version,
            "generated_at_utc": self.generated_at_utc,
            "log_path": self.log_path,
            "summary_root": self.summary_root,
            "total_rows": self.total_rows,
            "latest_recorded_at_utc": self.latest_recorded_at_utc,
            "coverage": [bucket.to_dict() for bucket in self.coverage],
            "recent_records": [record.to_dict() for record in self.recent_records],
            "governance_summary": self.governance_summary.to_dict(),
        }
