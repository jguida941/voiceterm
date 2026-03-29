"""Typed inputs for governance review log construction."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

FINDING_REVIEW_CONTRACT_ID, FINDING_REVIEW_SCHEMA_VERSION = "FindingReview", 2

VALID_FINDING_CLASSES: tuple[str, ...] = (
    "local_defect",
    "contract_mismatch",
    "missing_guard",
    "missing_probe",
    "rule_quality",
    "authority_boundary",
    "workflow_gap",
    "docs_drift",
    "unknown",
)

VALID_RECURRENCE_RISKS: tuple[str, ...] = (
    "one_off",
    "localized",
    "recurring",
    "systemic",
    "unknown",
)

VALID_PREVENTION_SURFACES: tuple[str, ...] = (
    "guard",
    "probe",
    "contract",
    "authority_rule",
    "parity_check",
    "regression_test",
    "docs_only",
    "repo_policy",
    "none",
)


@dataclass(frozen=True)
class GovernanceReviewInput:
    """Normalized command input for one adjudicated finding row."""

    signal_type: str
    check_id: str
    verdict: str
    file_path: str
    symbol: str | None = None
    line: int | None = None
    severity: str | None = None
    risk_type: str | None = None
    source_command: str | None = None
    scan_mode: str | None = None
    repo_name: str | None = None
    repo_path: str | None = None
    notes: str | None = None
    finding_id: str | None = None
    finding_class: str | None = None
    recurrence_risk: str | None = None
    prevention_surface: str | None = None
    waiver_reason: str | None = None
    guidance_id: str | None = None
    guidance_followed: bool | None = None


@dataclass(frozen=True)
class GovernanceReviewBucketStat:
    """One grouped finding-quality metric row."""

    bucket: str
    total_findings: int
    positive_finding_count: int
    open_finding_count: int
    false_positive_count: int
    false_positive_rate_pct: float
    fixed_count: int
    cleanup_rate_pct: float


@dataclass(frozen=True)
class GovernanceReviewStats:
    """Rolled-up governance review metrics for one snapshot."""

    total_rows: int
    total_findings: int
    false_positive_count: int
    false_positive_rate_pct: float
    positive_finding_count: int
    open_finding_count: int
    positive_finding_rate_pct: float
    fixed_count: int
    cleanup_rate_pct: float
    deferred_count: int
    waived_count: int
    unknown_count: int
    by_verdict: tuple[dict[str, Any], ...]
    by_check_id: tuple[GovernanceReviewBucketStat, ...]
    by_signal_type: tuple[GovernanceReviewBucketStat, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert the nested stats payload into plain JSON-friendly dicts."""
        return asdict(self)
