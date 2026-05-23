#!/usr/bin/env python3
"""Backward-compat shim -- use `ingestion_churn_advancement.command`."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable ingestion-churn guard entrypoint during package extraction
# shim-expiry: 2026-12-31
# shim-target: dev/scripts/checks/ingestion_churn_advancement/command.py
if __package__:
    from .ingestion_churn_advancement.command import main
    from .ingestion_churn_advancement.feature_proof import (
        feature_proof_row_ids as _feature_proof_row_ids,
        feature_proof_row_refs as _feature_proof_row_refs,
    )
    from .ingestion_churn_advancement.jsonl import iter_jsonl as _iter_jsonl
    from .ingestion_churn_advancement.models import (
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
        SnapshotGroup,
        repo_relative as _repo_relative,
    )
    from .ingestion_churn_advancement.plan_state import (
        blocked_or_aborted_row_ids as _blocked_or_aborted_row_ids,
        closure_row_ids as _closure_row_ids,
        has_plan_row_commit_anchor as _has_plan_row_commit_anchor,
        plan_rows_by_id as _plan_rows_by_id,
    )
    from .ingestion_churn_advancement.report import build_report, render_markdown
    from .ingestion_churn_advancement.snapshots import (
        snapshot_groups as _snapshot_groups,
        snapshot_row_id as _snapshot_row_id,
    )
    from .ingestion_churn_advancement.time_window import (
        parse_timestamp as _parse_timestamp,
        within_latest_window as _within_latest_window,
    )
else:
    from ingestion_churn_advancement.command import main
    from ingestion_churn_advancement.feature_proof import (
        feature_proof_row_ids as _feature_proof_row_ids,
        feature_proof_row_refs as _feature_proof_row_refs,
    )
    from ingestion_churn_advancement.jsonl import iter_jsonl as _iter_jsonl
    from ingestion_churn_advancement.models import (
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
        SnapshotGroup,
        repo_relative as _repo_relative,
    )
    from ingestion_churn_advancement.plan_state import (
        blocked_or_aborted_row_ids as _blocked_or_aborted_row_ids,
        closure_row_ids as _closure_row_ids,
        has_plan_row_commit_anchor as _has_plan_row_commit_anchor,
        plan_rows_by_id as _plan_rows_by_id,
    )
    from ingestion_churn_advancement.report import build_report, render_markdown
    from ingestion_churn_advancement.snapshots import (
        snapshot_groups as _snapshot_groups,
        snapshot_row_id as _snapshot_row_id,
    )
    from ingestion_churn_advancement.time_window import (
        parse_timestamp as _parse_timestamp,
        within_latest_window as _within_latest_window,
    )
if __name__ == "__main__":
    raise SystemExit(main())
