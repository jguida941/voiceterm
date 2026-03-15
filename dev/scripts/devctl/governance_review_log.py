"""Helpers for durable governance finding review logs and summaries."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, deque
from pathlib import Path
from typing import Any

from .governance_review_models import (
    GovernanceReviewBucketStat,
    GovernanceReviewInput,
    GovernanceReviewStats,
)
from .jsonl_support import parse_json_line_dict
from .repo_packs.voiceterm import VOICETERM_PATH_CONFIG, voiceterm_repo_root
from .time_utils import utc_timestamp

DEFAULT_GOVERNANCE_REVIEW_LOG = Path(VOICETERM_PATH_CONFIG.governance_review_log_rel)
DEFAULT_GOVERNANCE_REVIEW_SUMMARY_ROOT = Path(VOICETERM_PATH_CONFIG.governance_review_summary_root_rel)
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
    raw_path: str | Path | None,
    *,
    repo_root: Path | None = None,
) -> Path:
    """Resolve the governance review JSONL path relative to the repo."""
    effective_root = repo_root or voiceterm_repo_root() or Path(".")
    candidate = (
        Path(raw_path).expanduser()
        if raw_path is not None and str(raw_path).strip()
        else effective_root / DEFAULT_GOVERNANCE_REVIEW_LOG
    )
    if not candidate.is_absolute():
        candidate = effective_root / candidate
    return candidate.resolve()


def resolve_governance_review_summary_root(
    raw_path: str | Path | None,
    *,
    repo_root: Path | None = None,
) -> Path:
    """Resolve the governance review summary root relative to the repo."""
    effective_root = repo_root or voiceterm_repo_root() or Path(".")
    candidate = (
        Path(raw_path).expanduser()
        if raw_path is not None and str(raw_path).strip()
        else effective_root / DEFAULT_GOVERNANCE_REVIEW_SUMMARY_ROOT
    )
    if not candidate.is_absolute():
        candidate = effective_root / candidate
    return candidate.resolve()


def build_governance_review_row(
    *,
    review_input: GovernanceReviewInput,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Build one canonical review-log row."""
    effective_root = repo_root or voiceterm_repo_root() or Path(".")
    normalized_signal_type = _require_choice(
        review_input.signal_type,
        VALID_SIGNAL_TYPES,
        field_name="signal_type",
    )
    normalized_verdict = _require_choice(
        review_input.verdict,
        VALID_VERDICTS,
        field_name="verdict",
    )
    normalized_path = _required_text(review_input.file_path, field_name="file_path")
    normalized_check_id = _required_text(review_input.check_id, field_name="check_id")
    normalized_symbol = _optional_text(review_input.symbol)
    normalized_line = _optional_line_number(review_input.line)
    review_finding_id = review_input.finding_id or _default_finding_id(
        repo_name=_optional_text(review_input.repo_name),
        repo_path=_optional_text(review_input.repo_path),
        signal_type=normalized_signal_type,
        check_id=normalized_check_id,
        file_path=normalized_path,
        symbol=normalized_symbol,
        line=normalized_line,
    )
    row: dict[str, Any] = {}
    row["finding_id"] = review_finding_id
    row["timestamp_utc"] = utc_timestamp()
    row["repo_name"] = _optional_text(review_input.repo_name) or effective_root.name
    row["repo_path"] = _optional_text(review_input.repo_path) or str(effective_root)
    row["signal_type"] = normalized_signal_type
    row["check_id"] = normalized_check_id
    row["verdict"] = normalized_verdict
    row["file_path"] = normalized_path
    if normalized_symbol:
        row["symbol"] = normalized_symbol
    if normalized_line is not None:
        row["line"] = normalized_line
    if severity_text := _optional_text(review_input.severity):
        row["severity"] = severity_text
    if risk_text := _optional_text(review_input.risk_type):
        row["risk_type"] = risk_text
    if source_text := _optional_text(review_input.source_command):
        row["source_command"] = source_text
    if mode_text := _optional_text(review_input.scan_mode):
        row["scan_mode"] = mode_text
    if notes_text := _optional_text(review_input.notes):
        row["notes"] = notes_text
    return row


def append_governance_review_row(
    row: dict[str, Any],
    *,
    log_path: Path,
) -> None:
    """Append one governance review row to the JSONL log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True))
        handle.write("\n")


def read_governance_review_rows(
    log_path: Path,
    *,
    max_rows: int,
) -> list[dict[str, Any]]:
    """Read governance review rows from JSONL, bounded to the most recent rows."""
    rows: deque[dict[str, Any]] = deque(maxlen=max(1, max_rows))
    try:
        with log_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                payload = parse_json_line_dict(line)
                if payload is not None:
                    rows.append(payload)
    except OSError:
        return []
    return list(rows)


def build_governance_review_stats(rows: list[dict[str, Any]]) -> GovernanceReviewStats:
    """Reduce review-log rows into false-positive and cleanup metrics."""
    latest_rows = _latest_rows_by_finding(rows)
    total_findings = len(latest_rows)
    verdict_counts = Counter(_optional_text(row.get("verdict")) or "unknown" for row in latest_rows)
    positive_count = sum(verdict_counts[verdict] for verdict in POSITIVE_VERDICTS)
    fixed_count = verdict_counts["fixed"]
    false_positive_count = verdict_counts["false_positive"]

    return GovernanceReviewStats(
        total_rows=len(rows),
        total_findings=total_findings,
        false_positive_count=false_positive_count,
        false_positive_rate_pct=_rate(false_positive_count, total_findings),
        positive_finding_count=positive_count,
        positive_finding_rate_pct=_rate(positive_count, total_findings),
        fixed_count=fixed_count,
        cleanup_rate_pct=_rate(fixed_count, positive_count),
        deferred_count=verdict_counts["deferred"],
        waived_count=verdict_counts["waived"],
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
    latest_rows = _latest_rows_by_finding(rows)
    recent_findings = latest_rows[-max(1, recent_limit) :]
    report: dict[str, Any] = {}
    report["command"] = "governance-review"
    report["generated_at_utc"] = utc_timestamp()
    report["log_path"] = str(log_path)
    report["stats"] = build_governance_review_stats(rows).to_dict()
    report["recent_findings"] = recent_findings
    return report


def _latest_rows_by_finding(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for row in rows:
        finding_id = _optional_text(row.get("finding_id"))
        if not finding_id:
            continue
        if finding_id not in latest:
            order.append(finding_id)
        latest[finding_id] = row
    return [latest[finding_id] for finding_id in order if finding_id in latest]


def _bucket_stats(
    rows: list[dict[str, Any]],
    *,
    key_name: str,
) -> list[GovernanceReviewBucketStat]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        bucket = _optional_text(row.get(key_name)) or "unknown"
        grouped.setdefault(bucket, []).append(row)
    ranked = sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))
    stats: list[GovernanceReviewBucketStat] = []
    for bucket, bucket_rows in ranked:
        verdict_counts = Counter(_optional_text(row.get("verdict")) or "unknown" for row in bucket_rows)
        positive_count = sum(verdict_counts[verdict] for verdict in POSITIVE_VERDICTS)
        fixed_count = verdict_counts["fixed"]
        false_positive_count = verdict_counts["false_positive"]
        stats.append(
            GovernanceReviewBucketStat(
                bucket=bucket,
                total_findings=len(bucket_rows),
                false_positive_count=false_positive_count,
                false_positive_rate_pct=_rate(false_positive_count, len(bucket_rows)),
                fixed_count=fixed_count,
                cleanup_rate_pct=_rate(fixed_count, positive_count),
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
    raw = "::".join(
        [
            repo_name or "",
            repo_path or "",
            signal_type,
            check_id,
            file_path,
            symbol or "",
            str(line or ""),
        ]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _require_choice(value: str, allowed: frozenset[str], *, field_name: str) -> str:
    text = _required_text(value, field_name=field_name).lower()
    if text not in allowed:
        joined = ", ".join(sorted(allowed))
        raise ValueError(f"{field_name} must be one of: {joined}")
    return text


def _required_text(value: object, *, field_name: str) -> str:
    text = _optional_text(value)
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _optional_line_number(value: object) -> int | None:
    if value in (None, ""):
        return None
    number = int(value)
    if number <= 0:
        raise ValueError("line must be >= 1")
    return number


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)
