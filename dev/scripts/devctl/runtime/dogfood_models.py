"""Typed contracts for persisted dogfood coverage and report state."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from ..governance.ledger_helpers import optional_text

DOGFOOD_RECORD_CONTRACT_ID = "DogfoodRun"
DOGFOOD_RECORD_SCHEMA_VERSION = 1
DOGFOOD_REPORT_CONTRACT_ID = "DogfoodReport"
DOGFOOD_REPORT_SCHEMA_VERSION = 1

VALID_DOGFOOD_TARGET_KINDS: tuple[str, ...] = (
    "command",
    "guard",
    "probe",
    "role",
    "scenario",
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
DOGFOOD_SCENARIO_TARGET_IDS: tuple[str, ...] = (
    "plan41-tandem",
)


@dataclass(frozen=True, slots=True)
class DogfoodRecordInput:
    """Normalized input for one persisted dogfood execution record."""

    target_kind: str
    target_id: str
    status: str
    campaign_id: str | None = None
    scenario_id: str | None = None
    repo_scope: str | None = None
    repo_label: str | None = None
    repo_path: str | None = None
    topology: str | None = None
    lane_role: str | None = None
    live_run_refs: tuple[str, ...] = ()
    governance_finding_ids: tuple[str, ...] = ()
    actor: str | None = None
    provider: str | None = None
    run_label: str | None = None
    source_command: str | None = None
    artifact_path: str | None = None
    repo_name: str | None = None
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
    campaign_id: str = ""
    scenario_id: str = ""
    repo_scope: str = ""
    repo_label: str = ""
    topology: str = ""
    lane_role: str = ""
    live_run_refs: tuple[str, ...] = ()
    governance_finding_ids: tuple[str, ...] = ()
    actor: str = ""
    provider: str = ""
    run_label: str = ""
    source_command: str = ""
    artifact_path: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert the record into a JSON-safe payload."""
        payload = asdict(self)
        payload["live_run_refs"] = list(self.live_run_refs)
        payload["governance_finding_ids"] = list(self.governance_finding_ids)
        return payload


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


def normalize_dogfood_text_items(value: object | None) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        candidates = [value]
    elif isinstance(value, (list, tuple, set)):
        candidates = list(value)
    else:
        candidates = [value]
    normalized: list[str] = []
    for candidate in candidates:
        text = optional_text(candidate)
        if text:
            normalized.append(text)
    return tuple(normalized)


def dogfood_record_from_row(row: Mapping[str, object]) -> DogfoodRecord:
    return DogfoodRecord(
        record_id=optional_text(row.get("record_id")),
        timestamp_utc=optional_text(row.get("timestamp_utc")),
        contract_id=optional_text(row.get("contract_id")),
        schema_version=int(row.get("schema_version") or DOGFOOD_RECORD_SCHEMA_VERSION),
        repo_name=optional_text(row.get("repo_name")),
        repo_path=optional_text(row.get("repo_path")),
        target_kind=optional_text(row.get("target_kind")),
        target_id=optional_text(row.get("target_id")),
        status=optional_text(row.get("status")),
        campaign_id=optional_text(row.get("campaign_id")),
        scenario_id=optional_text(row.get("scenario_id")),
        repo_scope=optional_text(row.get("repo_scope")),
        repo_label=optional_text(row.get("repo_label")),
        topology=optional_text(row.get("topology")),
        lane_role=optional_text(row.get("lane_role")),
        live_run_refs=normalize_dogfood_text_items(row.get("live_run_refs")),
        governance_finding_ids=normalize_dogfood_text_items(
            row.get("governance_finding_ids")
        ),
        actor=optional_text(row.get("actor")),
        provider=optional_text(row.get("provider")),
        run_label=optional_text(row.get("run_label")),
        source_command=optional_text(row.get("source_command")),
        artifact_path=optional_text(row.get("artifact_path")),
        notes=optional_text(row.get("notes")),
    )
