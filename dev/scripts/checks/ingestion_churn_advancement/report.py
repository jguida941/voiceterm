"""Report assembly + markdown rendering for the ingestion-churn guard."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

try:
    from check_bootstrap import utc_timestamp
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import utc_timestamp

from .feature_proof import feature_proof_row_ids
from .models import (
    COMMAND,
    CONTRACT_ID,
    DEFAULT_CLOSURE_RECEIPTS_PATH,
    DEFAULT_FEATURE_PROOF_DIR,
    DEFAULT_LIFECYCLE_RECEIPTS_PATH,
    DEFAULT_MAX_SNAPSHOTS,
    DEFAULT_PLAN_INDEX_PATH,
    DEFAULT_ROW_ID,
    DEFAULT_SNAPSHOTS_PATH,
    DEFAULT_WINDOW_HOURS,
    DISPLAY_TEXT,
    INGESTION_CHURN_REASON,
    IngestionChurnViolation,
    repo_relative,
)
from .plan_state import (
    blocked_or_aborted_row_ids,
    closure_row_ids,
    has_plan_row_commit_anchor,
    plan_rows_by_id,
)
from .snapshots import snapshot_groups


def build_report(
    *,
    snapshots_path: Path = DEFAULT_SNAPSHOTS_PATH,
    plan_index_path: Path = DEFAULT_PLAN_INDEX_PATH,
    closure_receipts_path: Path = DEFAULT_CLOSURE_RECEIPTS_PATH,
    lifecycle_receipts_path: Path = DEFAULT_LIFECYCLE_RECEIPTS_PATH,
    feature_proof_dir: Path = DEFAULT_FEATURE_PROOF_DIR,
    row_id: str = DEFAULT_ROW_ID,
    all_rows: bool = False,
    window_hours: int = DEFAULT_WINDOW_HOURS,
    max_snapshots: int = DEFAULT_MAX_SNAPSHOTS,
) -> dict[str, object]:
    warnings: list[str] = []
    row_id = row_id.strip()
    plan_rows = plan_rows_by_id(plan_index_path)
    closure_rows = closure_row_ids(closure_receipts_path)
    blocked_or_aborted_rows = blocked_or_aborted_row_ids(lifecycle_receipts_path)
    feature_proof_rows = feature_proof_row_ids(feature_proof_dir)
    groups = tuple(
        snapshot_groups(
            snapshots_path=snapshots_path,
            window_hours=window_hours,
            warnings=warnings,
        )
    )

    group_reports: list[dict[str, object]] = []
    violations: list[IngestionChurnViolation] = []
    for group in groups:
        if not all_rows and group.row_id != row_id:
            continue
        row = plan_rows.get(group.row_id, {})
        has_commit_anchor = has_plan_row_commit_anchor(row)
        has_closure = group.row_id in closure_rows
        has_blocker_or_abort = group.row_id in blocked_or_aborted_rows
        has_proven_fpr = group.row_id in feature_proof_rows
        group_report = {
            "source_ref": group.source_ref,
            "row_id": group.row_id,
            "snapshot_count": len(group.snapshots),
            "action_ids": [
                str(snapshot.get("action_id", ""))
                for snapshot in group.snapshots
                if snapshot.get("action_id")
            ],
            "snapshot_ids": [
                str(snapshot.get("snapshot_id", ""))
                for snapshot in group.snapshots
                if snapshot.get("snapshot_id")
            ],
            "has_plan_row_commit_anchor": has_commit_anchor,
            "has_closure_receipt": has_closure,
            "has_typed_blocker_or_abort": has_blocker_or_abort,
            "has_proven_feature_proof_receipt": has_proven_fpr,
        }
        group_reports.append(group_report)
        if len(group.snapshots) <= max_snapshots:
            continue
        if has_commit_anchor or has_closure or has_blocker_or_abort or has_proven_fpr:
            continue
        violations.append(
            IngestionChurnViolation(
                source_ref=group.source_ref,
                row_id=group.row_id,
                reason=INGESTION_CHURN_REASON,
                snapshot_count=str(len(group.snapshots)),
                detail=(
                    f"{group.source_ref} has {len(group.snapshots)} PlanSourceSnapshot rows "
                    f"for {group.row_id} inside {window_hours}h with no commit anchor, "
                    "PlanRowClosureReceipt, or proven FeatureProofReceipt."
                ),
                remediation=(
                    "Stop re-ingesting the same source until the row is advanced, closed, "
                    "or backed by proven proof evidence."
                ),
            )
        )

    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not violations,
        "display_text": DISPLAY_TEXT if violations else "",
        "snapshots_path": str(repo_relative(snapshots_path)),
        "plan_index_path": str(repo_relative(plan_index_path)),
        "closure_receipts_path": str(repo_relative(closure_receipts_path)),
        "lifecycle_receipts_path": str(repo_relative(lifecycle_receipts_path)),
        "feature_proof_dir": str(repo_relative(feature_proof_dir)),
        "row_id": row_id,
        "all_rows": all_rows,
        "window_hours": window_hours,
        "max_snapshots": max_snapshots,
        "group_count": len(group_reports),
        "groups": group_reports,
        "violation_count": len(violations),
        "violations": [violation.to_dict() for violation in violations],
        "warnings": warnings,
    }


def render_markdown(report: Mapping[str, object]) -> str:
    lines = [f"# {COMMAND}", ""]
    lines.append(f"- ok: {report.get('ok')}")
    lines.append(f"- window_hours: {report.get('window_hours')}")
    lines.append(f"- row_id: `{report.get('row_id')}`")
    lines.append(f"- all_rows: {report.get('all_rows')}")
    lines.append(f"- max_snapshots: {report.get('max_snapshots')}")
    lines.append(f"- group_count: {report.get('group_count')}")
    lines.append(f"- violation_count: {report.get('violation_count')}")
    if report.get("display_text"):
        lines.extend(("", str(report["display_text"])))
    violations = report.get("violations")
    if isinstance(violations, Sequence) and not isinstance(violations, (str, bytes)):
        lines.extend(("", "## Violations", ""))
        for violation in violations:
            if isinstance(violation, Mapping):
                lines.append(
                    f"- {violation.get('source_ref')} / {violation.get('row_id')}: "
                    f"{violation.get('reason')} ({violation.get('detail')})"
                )
    return "\n".join(lines)
