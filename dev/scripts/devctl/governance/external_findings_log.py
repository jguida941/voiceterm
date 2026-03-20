"""Helpers for imported external-finding ledgers and coverage summaries."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from ..governance.identity import (
    hash_identity_parts,
    normalize_identity_file_path,
    normalize_identity_repo_path,
)
from ..governance.ledger_helpers import (
    append_ledger_rows,
    latest_rows_by_finding,
    optional_line_number,
    optional_text,
    rate,
    read_ledger_rows,
    resolve_ledger_path,
)
from ..jsonl_support import parse_json_line_dict
from ..governance_review_log import read_governance_review_rows
from ..repo_packs import active_path_config
from ..repo_packs.voiceterm import voiceterm_repo_root
from ..time_utils import utc_timestamp
from .external_findings_models import (
    ExternalFindingBucketStat,
    ExternalFindingInput,
    ExternalFindingStats,
)

DEFAULT_EXTERNAL_FINDING_LOG = Path(active_path_config().external_finding_log_rel)
DEFAULT_EXTERNAL_FINDING_SUMMARY_ROOT = Path(active_path_config().external_finding_summary_root_rel)
DEFAULT_MAX_EXTERNAL_FINDING_ROWS = 10_000
DEFAULT_CHECK_ID = "external_audit"
DEFAULT_SIGNAL_TYPE = "audit"
SCHEMA_VERSION = 1
VALID_SIGNAL_TYPES = frozenset({"guard", "probe", "audit"})


def resolve_external_finding_log_path(
    raw_path: str | Path | None = None,
    *,
    repo_root: Path | None = None,
) -> Path:
    """Resolve the imported external-finding JSONL path relative to the repo.

    Uses ``DEFAULT_EXTERNAL_FINDING_LOG`` when *raw_path* is absent.
    """
    resolved = resolve_ledger_path(
        raw_path, default_rel=DEFAULT_EXTERNAL_FINDING_LOG,
        repo_root_fn=voiceterm_repo_root, repo_root=repo_root,
    )
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def resolve_external_finding_summary_root(
    raw_path: str | Path | None = None,
    *,
    repo_root: Path | None = None,
) -> Path:
    """Resolve the imported external-finding summary root relative to the repo.

    Uses ``DEFAULT_EXTERNAL_FINDING_SUMMARY_ROOT`` when *raw_path* is absent.
    """
    resolved = resolve_ledger_path(
        raw_path, default_rel=DEFAULT_EXTERNAL_FINDING_SUMMARY_ROOT,
        repo_root_fn=voiceterm_repo_root, repo_root=repo_root,
    )
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def build_external_finding_row(
    *,
    finding_input: ExternalFindingInput,
) -> dict[str, Any]:
    """Build one canonical imported-finding row."""
    normalized_repo_path = optional_text(finding_input.repo_path)
    normalized_path = normalize_identity_file_path(
        finding_input.file_path,
        repo_path=normalized_repo_path,
    )
    normalized_repo_name = optional_text(finding_input.repo_name)
    if not normalized_repo_name and normalized_repo_path:
        normalized_repo_name = Path(normalized_repo_path).name or None
    if not normalized_repo_name:
        raise ValueError("repo_name or repo_path is required for imported findings")

    normalized_signal_type = _normalize_signal_type(finding_input.signal_type)
    normalized_check_id = optional_text(finding_input.check_id) or DEFAULT_CHECK_ID
    normalized_title = optional_text(finding_input.title)
    normalized_summary = optional_text(finding_input.summary)
    normalized_evidence = optional_text(finding_input.evidence)
    normalized_symbol = optional_text(finding_input.symbol)
    normalized_line = optional_line_number(finding_input.line)
    normalized_end_line = optional_line_number(finding_input.end_line)
    normalized_source_row = optional_line_number(finding_input.source_row)
    finding_id = finding_input.finding_id or _default_finding_id(
        repo_name=normalized_repo_name,
        repo_path=normalize_identity_repo_path(normalized_repo_path),
        signal_type=normalized_signal_type,
        check_id=normalized_check_id,
        file_path=normalized_path,
        symbol=normalized_symbol,
        line=normalized_line,
        title=normalized_title,
        summary=normalized_summary,
        evidence=normalized_evidence,
        source_row=normalized_source_row,
    )

    row: dict[str, Any] = {
        "finding_id": finding_id,
        "timestamp_utc": utc_timestamp(),
        "schema_version": SCHEMA_VERSION,
        "repo_name": normalized_repo_name,
        "signal_type": normalized_signal_type,
        "check_id": normalized_check_id,
        "file_path": normalized_path,
    }
    if normalized_repo_path:
        row["repo_path"] = normalized_repo_path
    if normalized_line is not None:
        row["line"] = normalized_line
    if normalized_end_line is not None:
        row["end_line"] = normalized_end_line
    if normalized_symbol:
        row["symbol"] = normalized_symbol
    if normalized_title:
        row["title"] = normalized_title
    if normalized_summary:
        row["summary"] = normalized_summary
    if normalized_evidence:
        row["evidence"] = normalized_evidence
    if severity_text := optional_text(finding_input.severity):
        row["severity"] = severity_text.lower()
    if risk_text := optional_text(finding_input.risk_type):
        row["risk_type"] = risk_text
    if model_text := optional_text(finding_input.source_model):
        row["source_model"] = model_text
    if command_text := optional_text(finding_input.source_command):
        row["source_command"] = command_text
    if artifact_text := optional_text(finding_input.source_artifact):
        row["source_artifact"] = artifact_text
    if normalized_source_row is not None:
        row["source_row"] = normalized_source_row
    if mode_text := optional_text(finding_input.scan_mode):
        row["scan_mode"] = mode_text
    if run_text := optional_text(finding_input.import_run_id):
        row["import_run_id"] = run_text
    if notes_text := optional_text(finding_input.notes):
        row["notes"] = notes_text
    return row


def append_external_finding_rows(
    rows: list[dict[str, Any]],
    *,
    log_path: Path,
) -> None:
    """Append imported external-finding rows to the JSONL log.

    Validates that each row has a ``finding_id`` before writing.
    """
    for row in rows:
        if "finding_id" not in row:
            raise ValueError("external finding row must contain finding_id")
    append_ledger_rows(rows, log_path=log_path)


def read_external_finding_rows(
    log_path: Path,
    *,
    max_rows: int,
) -> list[dict[str, Any]]:
    """Read imported external-finding rows from JSONL, bounded to recent rows."""
    return read_ledger_rows(
        log_path, max_rows=max_rows, parse_line_fn=parse_json_line_dict,
    )


def build_external_finding_stats(
    rows: list[dict[str, Any]],
    review_rows: list[dict[str, Any]],
) -> ExternalFindingStats:
    """Reduce imported external findings into adjudication-coverage metrics."""
    latest_rows = latest_rows_by_finding(rows)
    latest_reviews = {
        row["finding_id"]: row
        for row in latest_rows_by_finding(review_rows)
        if row.get("finding_id")
    }
    total_findings = len(latest_rows)
    reviewed_rows = [
        latest_reviews[row["finding_id"]]
        for row in latest_rows
        if row.get("finding_id") in latest_reviews
    ]
    verdict_counts = Counter(
        optional_text(row.get("verdict")) or "unknown" for row in reviewed_rows
    )
    repo_names = {
        optional_text(row.get("repo_name")) or "unknown" for row in latest_rows
    }
    import_run_ids = {
        optional_text(row.get("import_run_id")) or ""
        for row in latest_rows
        if optional_text(row.get("import_run_id"))
    }

    reviewed_count = len(reviewed_rows)
    return ExternalFindingStats(
        total_rows=len(rows),
        total_findings=total_findings,
        unique_repo_count=len(repo_names),
        unique_import_run_count=len(import_run_ids),
        reviewed_count=reviewed_count,
        unreviewed_count=max(0, total_findings - reviewed_count),
        adjudication_coverage_pct=rate(reviewed_count, total_findings),
        false_positive_count=verdict_counts["false_positive"],
        fixed_count=verdict_counts["fixed"],
        confirmed_issue_count=verdict_counts["confirmed_issue"],
        deferred_count=verdict_counts["deferred"],
        waived_count=verdict_counts["waived"],
        by_repo=tuple(_bucket_stats(latest_rows, latest_reviews, key_name="repo_name")),
        by_check_id=tuple(
            _bucket_stats(latest_rows, latest_reviews, key_name="check_id")
        ),
    )


def build_external_finding_report(
    *,
    log_path: Path,
    governance_review_log_path: Path,
    max_rows: int,
    max_governance_review_rows: int,
    recent_limit: int = 10,
) -> dict[str, Any]:
    """Build one user-facing imported-finding report payload."""
    rows = read_external_finding_rows(log_path, max_rows=max_rows)
    review_rows = read_governance_review_rows(
        governance_review_log_path,
        max_rows=max_governance_review_rows,
    )
    latest = latest_rows_by_finding(rows)
    recent_findings = latest[-max(1, recent_limit) :]
    return {
        "command": "governance-import-findings",
        "generated_at_utc": utc_timestamp(),
        "log_path": str(log_path),
        "governance_review_log": str(governance_review_log_path),
        "stats": build_external_finding_stats(rows, review_rows).to_dict(),
        "recent_findings": recent_findings,
    }


def _bucket_stats(
    rows: list[dict[str, Any]],
    reviews_by_finding: dict[str, dict[str, Any]],
    *,
    key_name: str,
) -> list[ExternalFindingBucketStat]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        bucket = optional_text(row.get(key_name)) or "unknown"
        grouped.setdefault(bucket, []).append(row)
    ranked = sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))
    stats: list[ExternalFindingBucketStat] = []
    for bucket, bucket_rows in ranked:
        matched_reviews = [
            reviews_by_finding[row["finding_id"]]
            for row in bucket_rows
            if row.get("finding_id") in reviews_by_finding
        ]
        verdict_counts = Counter(
            optional_text(row.get("verdict")) or "unknown" for row in matched_reviews
        )
        stats.append(
            ExternalFindingBucketStat(
                bucket=bucket,
                total_findings=len(bucket_rows),
                reviewed_count=len(matched_reviews),
                adjudication_coverage_pct=rate(
                    len(matched_reviews),
                    len(bucket_rows),
                ),
                false_positive_count=verdict_counts["false_positive"],
                fixed_count=verdict_counts["fixed"],
                confirmed_issue_count=verdict_counts["confirmed_issue"],
                deferred_count=verdict_counts["deferred"],
                waived_count=verdict_counts["waived"],
            )
        )
    return stats


def _default_finding_id(
    *,
    repo_name: str,
    repo_path: str | None,
    signal_type: str,
    check_id: str,
    file_path: str,
    symbol: str | None,
    line: int | None,
    title: str | None,
    summary: str | None,
    evidence: str | None,
    source_row: int | None,
) -> str:
    return hash_identity_parts(
        repo_name,
        repo_path or "",
        signal_type,
        check_id,
        file_path,
        symbol or "",
        str(line or ""),
        title or "",
        summary or "",
        evidence or "",
        str(source_row or ""),
    )


def _normalize_signal_type(value: str | None) -> str:
    text = (optional_text(value) or DEFAULT_SIGNAL_TYPE).lower()
    if text not in VALID_SIGNAL_TYPES:
        allowed = ", ".join(sorted(VALID_SIGNAL_TYPES))
        raise ValueError(f"signal_type must be one of: {allowed}")
    return text
