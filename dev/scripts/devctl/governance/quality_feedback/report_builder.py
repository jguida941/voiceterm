"""Orchestrator — collects data from ledgers, Halstead analysis, and scores."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

from ...governance_review_log import (
    build_governance_review_stats,
    read_governance_review_rows,
    resolve_governance_review_log_path,
)
from ...time_utils import utc_timestamp
from ..external_findings_log import (
    build_external_finding_stats,
    read_external_finding_rows,
    resolve_external_finding_log_path,
)
from .fp_classifier import classify_findings
from .halstead import analyze_directory, summarize_halstead
from .source_counter import count_source_files
from .improvement_tracker import compute_improvement_delta
from .maintainability_score import ScoreInputs, compute_maintainability_score
from .models import (
    FPAnalysis,
    QUALITY_FEEDBACK_CONTRACT_ID,
    QUALITY_FEEDBACK_SCHEMA_VERSION,
    QualityFeedbackSnapshot,
)
from .per_check_score import build_check_quality_scores
from .recommendation_engine import build_recommendations

_DEFAULT_ARTIFACT_DIR = "dev/reports/governance/quality_feedback_latest"


@dataclasses.dataclass(frozen=True)
class ReportBuilderConfig:
    """Optional tuning knobs for the quality feedback report builder."""

    governance_review_log: Path | None = None
    external_finding_log: Path | None = None
    max_review_rows: int = 5_000
    max_external_rows: int = 10_000
    halstead_max_files: int = 5_000
    previous_snapshot: dict[str, Any] | None = None


def build_quality_feedback_report(
    *,
    repo_root: Path,
    repo_name: str,
    config: ReportBuilderConfig | None = None,
) -> QualityFeedbackSnapshot:
    """Build a complete quality feedback snapshot from repo data."""
    return _build_report_from_config(
        repo_root=repo_root,
        repo_name=repo_name,
        cfg=config or ReportBuilderConfig(),
    )


def _build_report_from_config(
    *,
    repo_root: Path,
    repo_name: str,
    cfg: ReportBuilderConfig,
) -> QualityFeedbackSnapshot:
    """Internal builder that works from a resolved config object."""

    # 1. Load governance review data
    review_log_path = (
        cfg.governance_review_log
        or resolve_governance_review_log_path(None, repo_root=repo_root)
    )
    review_rows = read_governance_review_rows(
        review_log_path, max_rows=cfg.max_review_rows
    )
    review_stats = build_governance_review_stats(review_rows)

    # 2. Load external finding data (cross-repo FP evidence)
    ext_log_path = (
        cfg.external_finding_log
        or resolve_external_finding_log_path(None, repo_root=repo_root)
    )
    ext_rows = read_external_finding_rows(
        ext_log_path, max_rows=cfg.max_external_rows
    )
    ext_stats = build_external_finding_stats(ext_rows, review_rows)

    # 3. Run Halstead analysis on the source tree
    halstead_file_metrics = analyze_directory(
        repo_root, max_files=cfg.halstead_max_files
    )
    halstead_summary = summarize_halstead(halstead_file_metrics)

    # 4. Classify false-positive findings
    fp_classifications = classify_findings(review_rows)
    fp_analysis = _build_fp_analysis(fp_classifications)

    # 5. Per-check quality scores
    check_scores = build_check_quality_scores(review_rows)

    # 6. Compute composite maintainability score
    score_inputs = _build_score_inputs(
        repo_root=repo_root,
        review_stats=review_stats,
        ext_stats=ext_stats,
        halstead_summary=halstead_summary,
    )
    maintainability = compute_maintainability_score(score_inputs)

    # 7. Improvement delta vs previous snapshot
    improvement = compute_improvement_delta(
        current_score=maintainability.overall,
        current_check_scores=check_scores,
        previous_snapshot=cfg.previous_snapshot,
    )

    # 8. AI recommendations
    recommendations = build_recommendations(
        maintainability=maintainability,
        halstead_summary=halstead_summary,
        check_scores=check_scores,
        fp_classifications=fp_classifications,
    )

    return QualityFeedbackSnapshot(
        schema_version=QUALITY_FEEDBACK_SCHEMA_VERSION,
        contract_id=QUALITY_FEEDBACK_CONTRACT_ID,
        command="governance-quality-feedback",
        generated_at_utc=utc_timestamp(),
        repo_name=repo_name,
        maintainability=maintainability,
        halstead_summary=halstead_summary,
        false_positive_analysis=fp_analysis,
        check_quality_scores=tuple(check_scores),
        improvement_delta=improvement,
        recommendations=tuple(recommendations),
    )


def _build_fp_analysis(
    classifications: list[Any],
) -> FPAnalysis:
    """Aggregate classified FP findings into the analysis payload."""
    cause_counts: dict[str, int] = {}
    for c in classifications:
        cause_counts[c.root_cause] = cause_counts.get(c.root_cause, 0) + 1

    total = len(classifications)
    by_root_cause = tuple(
        {
            "category": cause,
            "count": count,
            "pct": round((count / max(1, total)) * 100.0, 1),
        }
        for cause, count in sorted(
            cause_counts.items(), key=lambda x: -x[1]
        )
    )

    return FPAnalysis(
        total_fp_count=total,
        by_root_cause=by_root_cause,
        classified_findings=tuple(classifications),
    )


def _build_score_inputs(
    *,
    repo_root: Path,
    review_stats: Any,
    ext_stats: Any,
    halstead_summary: Any,
) -> ScoreInputs:
    """Map loaded statistics into the composite score formula inputs.

    Only dimensions whose real evidence was loaded are marked available.
    Dimensions without evidence (code_shape, duplication, time_to_green)
    remain unavailable until the builder is extended to load that data.
    """
    has_halstead = halstead_summary.files_scanned > 0
    has_review = review_stats.total_findings > 0
    raw_guard_count = _count_guard_checks_raw(review_stats)
    open_guard = _count_open_guard_findings(review_stats)
    open_positive = _count_open_positive_findings(review_stats)
    total_source_files = count_source_files(repo_root)

    return ScoreInputs(
        avg_halstead_mi=halstead_summary.avg_maintainability_index,
        halstead_mi_available=has_halstead,
        cleanup_rate_pct=review_stats.cleanup_rate_pct,
        cleanup_rate_available=has_review,
        open_guard_findings=open_guard,
        guard_count=max(1, raw_guard_count),
        guard_issue_burden_available=raw_guard_count > 0,
        open_positive_findings=open_positive,
        total_source_files=max(1, total_source_files),
        finding_density_available=has_review and total_source_files > 0,
    )


def _count_open_guard_findings(review_stats: Any) -> int:
    """Count guard-signal findings still truly open (not FP, fixed, waived, or deferred)."""
    for bucket in review_stats.by_signal_type:
        if getattr(bucket, "bucket", "") == "guard":
            return max(0, getattr(bucket, "open_finding_count", 0))
    return 0


def _count_guard_checks_raw(review_stats: Any) -> int:
    """Count distinct guard-type check_ids in the review ledger."""
    count = 0
    for bucket in review_stats.by_check_id:
        name = str(getattr(bucket, "bucket", ""))
        if _is_guard_check_id(name):
            count += 1
    return count


def _is_guard_check_id(check_id: str) -> bool:
    """Heuristic: a check_id belongs to the guard signal family."""
    return (
        check_id.endswith("-guard")
        or check_id.startswith("check_")
        or check_id.startswith("check-")
    )


def _count_open_positive_findings(review_stats: Any) -> int:
    """Count positive findings still truly open (not fixed, waived, or deferred)."""
    return max(0, getattr(review_stats, "open_finding_count", 0))


# -- Artifact writer ---------------------------------------------------------


def write_quality_feedback_artifact(
    snapshot: QualityFeedbackSnapshot,
    *,
    output_root: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, str]:
    """Write the snapshot JSON artifact to the standard reports path.

    Returns a dict with ``snapshot_path`` (JSON file) and ``summary_root``
    (the containing directory).
    """
    if output_root is None:
        effective_root = repo_root or Path(".")
        output_root = effective_root / _DEFAULT_ARTIFACT_DIR

    output_root.mkdir(parents=True, exist_ok=True)

    snapshot_path = output_root / "quality_feedback_snapshot.json"
    snapshot_path.write_text(
        json.dumps(snapshot.to_dict(), indent=2),
        encoding="utf-8",
    )

    return {
        "snapshot_path": str(snapshot_path),
        "summary_root": str(output_root),
    }
