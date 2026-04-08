"""Quality-related ReviewSnapshot dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class GuardResultRow:
    """One guard's typed pass/fail row."""

    name: str = ""
    ok: bool = True
    exit_code: int = 0
    summary: str = ""
    violations_count: int = 0


@dataclass(frozen=True, slots=True)
class ProbeFindingRow:
    """One probe finding projected into a reviewer-readable row."""

    probe: str = ""
    review_lens: str = ""
    severity: str = ""
    file: str = ""
    line: int = 0
    rule_id: str = ""
    summary: str = ""


@dataclass(frozen=True, slots=True)
class GovernanceFindingRow:
    """One governance-review record rendered for the external audit surface."""

    finding_id: str = ""
    check_id: str = ""
    file_path: str = ""
    symbol: str = ""
    severity: str = ""
    signal_type: str = ""
    verdict: str = ""
    timestamp_utc: str = ""
    notes: str = ""


@dataclass(frozen=True, slots=True)
class SnapshotQualitySignals:
    """Aggregated quality projection: guards, probes, governance findings."""

    ci_bundle_ok: bool = True
    ci_bundle_summary: str = ""
    ci_total_checks: int = 0
    ci_passed_checks: int = 0
    ci_failed_checks: int = 0
    ci_blocking_failures: tuple[GuardResultRow, ...] = ()
    probe_run_state: str = "missing"
    probe_run_mode: str = ""
    probe_generated_at: str = ""
    probe_warning_count: int = 0
    probe_error_count: int = 0
    probe_summary_json_path: str = ""
    probe_summary_md_path: str = ""
    probe_files_scanned: int = 0
    probe_hints_total: int = 0
    probe_hints_by_severity: dict[str, int] = field(default_factory=dict)
    probe_top_findings: tuple[ProbeFindingRow, ...] = ()
    governance_total_findings: int = 0
    governance_open_findings: int = 0
    governance_fixed_count: int = 0
    governance_false_positive_count: int = 0
    governance_recent_findings: tuple[GovernanceFindingRow, ...] = ()
    quality_policy_guard_count: int = 0
    quality_policy_probe_count: int = 0


__all__ = [
    "GovernanceFindingRow",
    "GuardResultRow",
    "ProbeFindingRow",
    "SnapshotQualitySignals",
]
