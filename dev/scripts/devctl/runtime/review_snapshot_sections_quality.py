"""Quality section builders for ReviewSnapshot."""

from __future__ import annotations

from collections.abc import Mapping

from .review_snapshot_models_quality import (
    GovernanceFindingRow,
    ProbeFindingRow,
    SnapshotQualitySignals,
)
from .review_snapshot_utils import as_list, as_mapping, coerce_int


def build_quality(
    *,
    governance_summary: Mapping[str, object],
    probe_summary: Mapping[str, object],
) -> SnapshotQualitySignals:
    """Return quality signals aggregated from governance + probe reports."""
    gov_stats = as_mapping(governance_summary.get("stats"))
    probe_block = as_mapping(probe_summary.get("summary"))
    hints_by_severity_raw = as_mapping(probe_block.get("hints_by_severity"))
    probe_artifacts = as_mapping(probe_summary.get("artifact_paths"))
    probe_errors = as_list(probe_summary.get("errors"))
    probe_warnings = as_list(probe_summary.get("warnings"))
    return SnapshotQualitySignals(
        ci_bundle_ok=bool(governance_summary.get("ok", True)),
        ci_bundle_summary="",
        ci_total_checks=0,
        ci_passed_checks=0,
        ci_failed_checks=0,
        ci_blocking_failures=(),
        probe_run_state=_probe_run_state(probe_summary, probe_errors),
        probe_run_mode=str(probe_summary.get("mode") or ""),
        probe_generated_at=str(
            probe_summary.get("generated_at")
            or probe_summary.get("generated_at_utc")
            or ""
        ),
        probe_warning_count=len(probe_warnings),
        probe_error_count=len(probe_errors),
        probe_summary_json_path=str(probe_artifacts.get("summary_json") or ""),
        probe_summary_md_path=str(probe_artifacts.get("summary_md") or ""),
        probe_files_scanned=coerce_int(probe_block.get("files_scanned")),
        probe_hints_total=coerce_int(probe_block.get("risk_hints")),
        probe_hints_by_severity={
            str(k): coerce_int(v) for k, v in hints_by_severity_raw.items()
        },
        probe_top_findings=_build_probe_findings(probe_summary),
        governance_total_findings=coerce_int(gov_stats.get("total_findings")),
        governance_open_findings=coerce_int(gov_stats.get("open_finding_count")),
        governance_fixed_count=coerce_int(gov_stats.get("fixed_count")),
        governance_false_positive_count=coerce_int(
            gov_stats.get("false_positive_count")
        ),
        governance_recent_findings=_build_governance_findings(governance_summary),
        quality_policy_guard_count=0,
        quality_policy_probe_count=0,
    )


def _probe_run_state(
    probe_summary: Mapping[str, object],
    errors: list[object],
) -> str:
    if not probe_summary:
        return "missing"
    if errors:
        return "errors_present"
    return "ok"


def _build_probe_findings(
    probe_summary: Mapping[str, object],
) -> tuple[ProbeFindingRow, ...]:
    rows: list[ProbeFindingRow] = []
    for hint in as_list(probe_summary.get("enriched_hints"))[:10]:
        row = as_mapping(hint)
        rows.append(
            ProbeFindingRow(
                probe=str(row.get("probe") or ""),
                review_lens=str(row.get("review_lens") or ""),
                severity=str(row.get("severity") or ""),
                file=str(row.get("file") or row.get("file_path") or ""),
                line=coerce_int(row.get("line")),
                rule_id=str(row.get("rule_id") or ""),
                summary=str(row.get("summary") or row.get("message") or ""),
            )
        )
    return tuple(rows)


def _build_governance_findings(
    governance_summary: Mapping[str, object],
) -> tuple[GovernanceFindingRow, ...]:
    rows: list[GovernanceFindingRow] = []
    for row in as_list(governance_summary.get("recent_findings"))[:15]:
        mapping = as_mapping(row)
        rows.append(
            GovernanceFindingRow(
                finding_id=str(mapping.get("finding_id") or ""),
                check_id=str(mapping.get("check_id") or ""),
                file_path=str(mapping.get("file_path") or ""),
                symbol=str(mapping.get("symbol") or ""),
                severity=str(mapping.get("severity") or ""),
                signal_type=str(mapping.get("signal_type") or ""),
                verdict=str(mapping.get("verdict") or ""),
                timestamp_utc=str(mapping.get("timestamp_utc") or ""),
                notes=str(mapping.get("notes") or ""),
            )
        )
    return tuple(rows)


__all__ = ["build_quality"]
