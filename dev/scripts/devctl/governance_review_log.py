"""Helpers for durable governance finding review logs and summaries."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .governance.identity import (
    hash_identity_parts,
    normalize_identity_file_path,
    normalize_identity_repo_path,
)
from .governance.ledger_helpers import (
    append_ledger_rows,
    latest_rows_by_finding,
    optional_line_number,
    optional_text,
    rate,
    read_ledger_rows,
    required_text,
    resolve_ledger_path,
)
from .jsonl_support import parse_json_line_dict
from .governance_review_models import (
    FINDING_REVIEW_CONTRACT_ID,
    FINDING_REVIEW_SCHEMA_VERSION,
    GovernanceReviewBucketStat,
    GovernanceReviewInput,
    GovernanceReviewStats,
    VALID_FINDING_CLASSES,
    VALID_PREVENTION_SURFACES,
    VALID_RECURRENCE_RISKS,
)
from .governance.review_validation import (
    governance_review_row_disposition_errors,
    require_choice,
)
from .repo_packs import active_path_config
from .repo_packs.voiceterm import voiceterm_repo_root
from .time_utils import utc_timestamp

DEFAULT_GOVERNANCE_REVIEW_LOG = Path(active_path_config().governance_review_log_rel)
DEFAULT_GOVERNANCE_REVIEW_SUMMARY_ROOT = Path(active_path_config().governance_review_summary_root_rel)
DEFAULT_MAX_GOVERNANCE_REVIEW_ROWS = 5_000
VALID_SIGNAL_TYPES = frozenset({"guard", "probe", "audit"})
VALID_VERDICTS = frozenset(
    {
        "confirmed_issue",
        "false_positive",
        "fixed",
        "waived",
        "deferred",
        "unknown",
    }
)
POSITIVE_VERDICTS = frozenset({"confirmed_issue", "fixed", "waived", "deferred"})


def resolve_governance_review_log_path(
    raw_path: str | Path | None = None,
    *,
    repo_root: Path | None = None,
) -> Path:
    """Resolve the governance review JSONL path relative to the repo.

    Uses ``DEFAULT_GOVERNANCE_REVIEW_LOG`` when *raw_path* is absent.
    """
    resolved = resolve_ledger_path(
        raw_path, default_rel=DEFAULT_GOVERNANCE_REVIEW_LOG,
        repo_root_fn=voiceterm_repo_root, repo_root=repo_root,
    )
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def resolve_governance_review_summary_root(
    raw_path: str | Path | None = None,
    *,
    repo_root: Path | None = None,
) -> Path:
    """Resolve the governance review summary root relative to the repo.

    Uses ``DEFAULT_GOVERNANCE_REVIEW_SUMMARY_ROOT`` when *raw_path* is absent.
    """
    resolved = resolve_ledger_path(
        raw_path, default_rel=DEFAULT_GOVERNANCE_REVIEW_SUMMARY_ROOT,
        repo_root_fn=voiceterm_repo_root, repo_root=repo_root,
    )
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def build_governance_review_row(
    *,
    review_input: GovernanceReviewInput,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Build one canonical review-log row."""
    effective_root = repo_root or voiceterm_repo_root() or Path(".")
    raw_repo_path = optional_text(review_input.repo_path)
    normalized_signal_type = require_choice(
        review_input.signal_type,
        VALID_SIGNAL_TYPES,
        field_name="signal_type",
    )
    normalized_verdict = require_choice(
        review_input.verdict,
        VALID_VERDICTS,
        field_name="verdict",
    )
    normalized_path = normalize_identity_file_path(
        review_input.file_path,
        repo_root=effective_root,
        repo_path=raw_repo_path,
    )
    normalized_check_id = required_text(review_input.check_id, field_name="check_id")
    normalized_symbol = optional_text(review_input.symbol)
    normalized_line = optional_line_number(review_input.line)
    normalized_finding_class = require_choice(
        review_input.finding_class,
        frozenset(VALID_FINDING_CLASSES),
        field_name="finding_class",
    )
    normalized_recurrence_risk = require_choice(
        review_input.recurrence_risk,
        frozenset(VALID_RECURRENCE_RISKS),
        field_name="recurrence_risk",
    )
    normalized_prevention_surface = require_choice(
        review_input.prevention_surface,
        frozenset(VALID_PREVENTION_SURFACES),
        field_name="prevention_surface",
    )
    review_finding_id = review_input.finding_id or _default_finding_id(
        repo_name=optional_text(review_input.repo_name),
        repo_path=normalize_identity_repo_path(
            raw_repo_path,
            repo_root=effective_root,
        ),
        signal_type=normalized_signal_type,
        check_id=normalized_check_id,
        file_path=normalized_path,
        symbol=normalized_symbol,
        line=normalized_line,
    )
    row: dict[str, Any] = {}
    row["finding_id"] = review_finding_id
    row["timestamp_utc"] = utc_timestamp()
    row["schema_version"] = FINDING_REVIEW_SCHEMA_VERSION
    row["contract_id"] = FINDING_REVIEW_CONTRACT_ID
    row["repo_name"] = optional_text(review_input.repo_name) or effective_root.name
    row["repo_path"] = raw_repo_path or str(effective_root)
    row["signal_type"] = normalized_signal_type
    row["check_id"] = normalized_check_id
    row["verdict"] = normalized_verdict
    row["file_path"] = normalized_path
    row["finding_class"] = normalized_finding_class
    row["recurrence_risk"] = normalized_recurrence_risk
    row["prevention_surface"] = normalized_prevention_surface
    if normalized_symbol:
        row["symbol"] = normalized_symbol
    if normalized_line is not None:
        row["line"] = normalized_line
    if severity_text := optional_text(review_input.severity):
        row["severity"] = severity_text
    if risk_text := optional_text(review_input.risk_type):
        row["risk_type"] = risk_text
    if source_text := optional_text(review_input.source_command):
        row["source_command"] = source_text
    if mode_text := optional_text(review_input.scan_mode):
        row["scan_mode"] = mode_text
    if notes_text := optional_text(review_input.notes):
        row["notes"] = notes_text
    if waiver_reason := optional_text(review_input.waiver_reason):
        row["waiver_reason"] = waiver_reason
    guidance_id = optional_text(review_input.guidance_id)
    guidance_followed = review_input.guidance_followed
    if guidance_id and guidance_followed is None:
        raise ValueError("guidance_followed is required when guidance_id is set")
    if guidance_followed is not None and not guidance_id:
        raise ValueError("guidance_id is required when guidance_followed is set")
    if guidance_id:
        row["guidance_id"] = guidance_id
        row["guidance_followed"] = bool(guidance_followed)
    disposition_errors = governance_review_row_disposition_errors(row)
    if disposition_errors:
        raise ValueError("; ".join(disposition_errors))
    return row


def append_governance_review_row(
    row: dict[str, Any],
    *,
    log_path: Path,
) -> None:
    """Append one governance review row to the JSONL log.

    Wraps the generic ledger writer with single-row list coercion so callers
    do not have to wrap individual rows in a list themselves.
    """
    if "finding_id" not in row:
        raise ValueError("governance review row must contain finding_id")
    append_ledger_rows([row], log_path=log_path)


def read_governance_review_rows(
    log_path: Path,
    *,
    max_rows: int,
) -> list[dict[str, Any]]:
    """Read governance review rows from JSONL, bounded to the most recent rows."""
    return read_ledger_rows(
        log_path, max_rows=max_rows, parse_line_fn=parse_json_line_dict,
    )


def build_governance_review_stats(rows: list[dict[str, Any]]) -> GovernanceReviewStats:
    """Reduce review-log rows into false-positive and cleanup metrics."""
    latest_rows = latest_rows_by_finding(rows)
    total_findings = len(latest_rows)
    verdict_counts = Counter(optional_text(row.get("verdict")) or "unknown" for row in latest_rows)
    positive_count = sum(verdict_counts[verdict] for verdict in POSITIVE_VERDICTS)
    fixed_count = verdict_counts["fixed"]
    false_positive_count = verdict_counts["false_positive"]

    deferred_count = verdict_counts["deferred"]
    waived_count = verdict_counts["waived"]
    open_count = max(0, positive_count - fixed_count - waived_count - deferred_count)

    return GovernanceReviewStats(
        total_rows=len(rows),
        total_findings=total_findings,
        false_positive_count=false_positive_count,
        false_positive_rate_pct=rate(false_positive_count, total_findings),
        positive_finding_count=positive_count,
        open_finding_count=open_count,
        positive_finding_rate_pct=rate(positive_count, total_findings),
        fixed_count=fixed_count,
        cleanup_rate_pct=rate(fixed_count, positive_count),
        deferred_count=deferred_count,
        waived_count=waived_count,
        unknown_count=verdict_counts["unknown"],
        by_verdict=tuple({"verdict": verdict, "count": count} for verdict, count in verdict_counts.most_common()),
        by_check_id=tuple(_bucket_stats(latest_rows, key_name="check_id")),
        by_signal_type=tuple(_bucket_stats(latest_rows, key_name="signal_type")),
    )


def build_governance_review_report(
    *,
    log_path: Path,
    max_rows: int,
    recent_limit: int = 10,
) -> dict[str, Any]:
    """Build one user-facing governance review report payload."""
    rows = read_governance_review_rows(log_path, max_rows=max_rows)
    latest = latest_rows_by_finding(rows)
    recent_findings = latest[-max(1, recent_limit) :]
    report: dict[str, Any] = {}
    report["command"] = "governance-review"
    report["generated_at_utc"] = utc_timestamp()
    report["log_path"] = str(log_path)
    report["stats"] = build_governance_review_stats(rows).to_dict()
    report["recent_findings"] = recent_findings
    return report


def _bucket_stats(
    rows: list[dict[str, Any]],
    *,
    key_name: str,
) -> list[GovernanceReviewBucketStat]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        bucket = optional_text(row.get(key_name)) or "unknown"
        grouped.setdefault(bucket, []).append(row)
    ranked = sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))
    stats: list[GovernanceReviewBucketStat] = []
    for bucket, bucket_rows in ranked:
        verdict_counts = Counter(optional_text(row.get("verdict")) or "unknown" for row in bucket_rows)
        positive_count = sum(verdict_counts[verdict] for verdict in POSITIVE_VERDICTS)
        fixed_count = verdict_counts["fixed"]
        false_positive_count = verdict_counts["false_positive"]
        waived_count = verdict_counts["waived"]
        deferred_count = verdict_counts["deferred"]
        stats.append(
            GovernanceReviewBucketStat(
                bucket=bucket,
                total_findings=len(bucket_rows),
                positive_finding_count=positive_count,
                open_finding_count=max(0, positive_count - fixed_count - waived_count - deferred_count),
                false_positive_count=false_positive_count,
                false_positive_rate_pct=rate(false_positive_count, len(bucket_rows)),
                fixed_count=fixed_count,
                cleanup_rate_pct=rate(fixed_count, positive_count),
            )
        )
    return stats


def _default_finding_id(
    *,
    repo_name: str | None,
    repo_path: str | None,
    signal_type: str,
    check_id: str,
    file_path: str,
    symbol: str | None,
    line: int | None,
) -> str:
    return hash_identity_parts(
        repo_name or "",
        repo_path or "",
        signal_type,
        check_id,
        file_path,
        symbol or "",
        str(line or ""),
    )
