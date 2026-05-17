"""Persistence helpers for dogfood run records and coverage reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import get_repo_root
from ..governance.identity import hash_identity_parts
from ..governance.ledger_helpers import (
    append_ledger_rows,
    optional_text,
    read_ledger_rows,
    required_text,
    resolve_ledger_path,
)
from ..governance.review_validation import require_choice
from ..governance.system_catalog import build_system_catalog
from ..governance.script_catalog_registry import CHECK_SCRIPT_FILES, PROBE_SCRIPT_FILES
from ..governance_review.log import (
    build_governance_review_report,
    resolve_governance_review_log_path,
)
from ..jsonl_support import parse_json_line_dict
from ..repo_packs import active_path_config
from ..time_utils import utc_timestamp
from .dogfood_models import (
    DOGFOOD_RECORD_CONTRACT_ID,
    DOGFOOD_RECORD_SCHEMA_VERSION,
    DOGFOOD_REPORT_CONTRACT_ID,
    DOGFOOD_REPORT_SCHEMA_VERSION,
    DOGFOOD_ROLE_TARGET_IDS,
    DOGFOOD_SCENARIO_TARGET_IDS,
    DogfoodCoverageBucket,
    DogfoodGovernanceSummary,
    DogfoodRecord,
    DogfoodRecordInput,
    DogfoodReport,
    VALID_DOGFOOD_STATUSES,
    VALID_DOGFOOD_TARGET_KINDS,
    dogfood_record_from_row,
    normalize_dogfood_text_items,
)

DEFAULT_DOGFOOD_LOG = Path(active_path_config().dogfood_log_rel)
DEFAULT_DOGFOOD_SUMMARY_ROOT = Path(active_path_config().dogfood_summary_root_rel)
DEFAULT_MAX_DOGFOOD_ROWS = 10_000


def resolve_dogfood_log_path(
    raw_path: str | Path | None = None,
    *,
    repo_root: Path | None = None,
) -> Path:
    """Resolve the dogfood JSONL log path relative to the repo root."""
    resolved = resolve_ledger_path(
        raw_path,
        default_rel=DEFAULT_DOGFOOD_LOG,
        repo_root_fn=get_repo_root,
        repo_root=repo_root,
    )
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def resolve_dogfood_summary_root(
    raw_path: str | Path | None = None,
    *,
    repo_root: Path | None = None,
) -> Path:
    """Resolve the dogfood summary artifact root relative to the repo root."""
    resolved = resolve_ledger_path(
        raw_path,
        default_rel=DEFAULT_DOGFOOD_SUMMARY_ROOT,
        repo_root_fn=get_repo_root,
        repo_root=repo_root,
    )
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def build_dogfood_record(
    *,
    record_input: DogfoodRecordInput,
    repo_root: Path | None = None,
) -> DogfoodRecord:
    """Build one canonical dogfood run record."""
    effective_root = repo_root or get_repo_root() or Path(".")
    target_kind = require_choice(
        record_input.target_kind,
        frozenset(VALID_DOGFOOD_TARGET_KINDS),
        field_name="target_kind",
    )
    target_id = required_text(record_input.target_id, field_name="target_id")
    status = require_choice(
        record_input.status,
        frozenset(VALID_DOGFOOD_STATUSES),
        field_name="status",
    )
    timestamp = utc_timestamp()
    campaign_id = optional_text(record_input.campaign_id)
    scenario_id = optional_text(record_input.scenario_id)
    repo_scope = optional_text(record_input.repo_scope)
    repo_label = optional_text(record_input.repo_label)
    topology = optional_text(record_input.topology)
    lane_role = optional_text(record_input.lane_role)
    live_run_refs = normalize_dogfood_text_items(record_input.live_run_refs)
    governance_finding_ids = normalize_dogfood_text_items(
        record_input.governance_finding_ids
    )
    actor = optional_text(record_input.actor)
    provider = optional_text(record_input.provider)
    run_label = optional_text(record_input.run_label)
    source_command = optional_text(record_input.source_command)
    artifact_path = optional_text(record_input.artifact_path)
    notes = optional_text(record_input.notes)
    repo_name = optional_text(record_input.repo_name) or effective_root.name
    repo_path = optional_text(record_input.repo_path) or str(effective_root)
    record_id = "dogfood-" + hash_identity_parts(
        repo_name,
        target_kind,
        target_id,
        status,
        actor,
        provider,
        timestamp,
    )[:12]
    return DogfoodRecord(
        record_id=record_id,
        timestamp_utc=timestamp,
        contract_id=DOGFOOD_RECORD_CONTRACT_ID,
        schema_version=DOGFOOD_RECORD_SCHEMA_VERSION,
        repo_name=repo_name,
        repo_path=repo_path,
        target_kind=target_kind,
        target_id=target_id,
        status=status,
        campaign_id=campaign_id,
        scenario_id=scenario_id,
        repo_scope=repo_scope,
        repo_label=repo_label,
        topology=topology,
        lane_role=lane_role,
        live_run_refs=live_run_refs,
        governance_finding_ids=governance_finding_ids,
        actor=actor,
        provider=provider,
        run_label=run_label,
        source_command=source_command,
        artifact_path=artifact_path,
        notes=notes,
    )


def append_dogfood_record(record: DogfoodRecord, *, log_path: Path) -> None:
    """Append one dogfood record row to the JSONL ledger."""
    append_ledger_rows([record.to_dict()], log_path=log_path)


def read_dogfood_rows(
    log_path: Path,
    *,
    max_rows: int,
) -> list[dict[str, Any]]:
    """Load the bounded dogfood run ledger."""
    return read_ledger_rows(
        log_path,
        max_rows=max_rows,
        parse_line_fn=parse_json_line_dict,
    )


def dogfood_catalog(
    *,
    repo_root: Path | None = None,
) -> dict[str, tuple[str, ...]]:
    """Return the live command/guard/probe/role catalog for coverage."""
    effective_root = repo_root or get_repo_root() or Path(".")
    catalog = build_system_catalog(repo_root=effective_root)
    command_ids = tuple(command.name for command in catalog.commands)
    guard_ids = tuple(CHECK_SCRIPT_FILES)
    probe_ids = tuple(PROBE_SCRIPT_FILES)
    return {
        "command": command_ids,
        "guard": guard_ids,
        "probe": probe_ids,
        "role": DOGFOOD_ROLE_TARGET_IDS,
        "scenario": DOGFOOD_SCENARIO_TARGET_IDS,
    }


def build_dogfood_report(
    *,
    log_path: Path,
    summary_root: Path,
    repo_root: Path | None = None,
    max_rows: int = DEFAULT_MAX_DOGFOOD_ROWS,
    recent_limit: int = 10,
) -> DogfoodReport:
    """Build one typed dogfood coverage report from persisted rows."""
    rows = read_dogfood_rows(log_path, max_rows=max_rows) if log_path.is_file() else []
    recent_rows = list(rows[-recent_limit:])
    recent_rows.reverse()
    coverage = tuple(
        _build_coverage_bucket(
            target_kind=target_kind,
            catalog_ids=target_ids,
            rows=rows,
        )
        for target_kind, target_ids in dogfood_catalog(repo_root=repo_root).items()
    )
    recent_records = tuple(dogfood_record_from_row(row) for row in recent_rows)
    latest_recorded_at_utc = (
        recent_records[0].timestamp_utc if recent_records else ""
    )
    return DogfoodReport(
        contract_id=DOGFOOD_REPORT_CONTRACT_ID,
        schema_version=DOGFOOD_REPORT_SCHEMA_VERSION,
        generated_at_utc=utc_timestamp(),
        log_path=str(log_path),
        summary_root=str(summary_root),
        total_rows=len(rows),
        latest_recorded_at_utc=latest_recorded_at_utc,
        coverage=coverage,
        recent_records=recent_records,
        governance_summary=_build_governance_summary(
            repo_root=repo_root,
            recent_limit=recent_limit,
        ),
    )


def _build_coverage_bucket(
    *,
    target_kind: str,
    catalog_ids: tuple[str, ...],
    rows: list[dict[str, Any]],
) -> DogfoodCoverageBucket:
    latest_by_target: dict[str, dict[str, Any]] = {}
    unknown_ids: list[str] = []
    catalog_set = set(catalog_ids)
    for row in rows:
        if optional_text(row.get("target_kind")) != target_kind:
            continue
        target_id = optional_text(row.get("target_id"))
        if not target_id:
            continue
        latest_by_target[target_id] = row
        if target_id not in catalog_set and target_id not in unknown_ids:
            unknown_ids.append(target_id)

    covered_ids = tuple(
        target_id for target_id in catalog_ids if target_id in latest_by_target
    )
    uncovered_ids = tuple(
        target_id for target_id in catalog_ids if target_id not in latest_by_target
    )
    passed_total = sum(
        1
        for target_id in covered_ids
        if optional_text(latest_by_target[target_id].get("status")) == "passed"
    )
    failed_total = sum(
        1
        for target_id in covered_ids
        if optional_text(latest_by_target[target_id].get("status")) == "failed"
    )
    blocked_total = sum(
        1
        for target_id in covered_ids
        if optional_text(latest_by_target[target_id].get("status")) == "blocked"
    )
    skipped_total = sum(
        1
        for target_id in covered_ids
        if optional_text(latest_by_target[target_id].get("status")) == "skipped"
    )
    catalog_total = len(catalog_ids)
    covered_total = len(covered_ids)
    coverage_pct = round((covered_total / catalog_total) * 100, 2) if catalog_total else 0.0
    return DogfoodCoverageBucket(
        target_kind=target_kind,
        catalog_total=catalog_total,
        covered_total=covered_total,
        coverage_pct=coverage_pct,
        passed_total=passed_total,
        failed_total=failed_total,
        blocked_total=blocked_total,
        skipped_total=skipped_total,
        uncovered_ids=uncovered_ids,
        unknown_ids=tuple(sorted(unknown_ids)),
    )


def _build_governance_summary(
    *,
    repo_root: Path | None,
    recent_limit: int,
) -> DogfoodGovernanceSummary:
    governance_log_path = resolve_governance_review_log_path(repo_root=repo_root)
    if not governance_log_path.is_file():
        return DogfoodGovernanceSummary()
    report = build_governance_review_report(
        log_path=governance_log_path,
        max_rows=5_000,
        recent_limit=recent_limit,
    )
    stats = report.get("stats") or {}
    bucket = next(
        (
            entry
            for entry in stats.get("by_signal_type", [])
            if entry.get("bucket") == "dogfood"
        ),
        {},
    )
    recent_findings = tuple(
        finding
        for finding in report.get("recent_findings", [])
        if finding.get("signal_type") == "dogfood"
    )[:recent_limit]
    return DogfoodGovernanceSummary(
        total_findings=int(bucket.get("total_findings") or 0),
        open_findings=int(bucket.get("open_finding_count") or 0),
        fixed_findings=int(bucket.get("fixed_count") or 0),
        recent_findings=recent_findings,
    )
