#!/usr/bin/env python3
"""Verify an operator staging source was snapshotted and ingested into a PlanRow."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT, emit_runtime_error, utc_timestamp
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import (
        REPO_ROOT,
        emit_runtime_error,
        utc_timestamp,
    )

try:
    from staging_source_ingested_support import StagingSourceSupport as Support
except ModuleNotFoundError:
    from dev.scripts.checks.staging_source_ingested_support import (
        StagingSourceSupport as Support,
    )


COMMAND = "check_staging_source_ingested"
CONTRACT_ID = "StagingSourceIngestedGuard"
DEFAULT_ROW_ID = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"
DEFAULT_SOURCE_PATH = REPO_ROOT / "delete_after_ingest.md"
DEFAULT_PLAN_INDEX_PATH = REPO_ROOT / "dev/state/plan_index.jsonl"
DEFAULT_SNAPSHOTS_PATH = REPO_ROOT / "dev/state/plan_source_snapshots.jsonl"
DEFAULT_INGESTION_RECEIPTS_PATH = REPO_ROOT / "dev/state/plan_ingestion_receipts.jsonl"


@dataclass(frozen=True, slots=True)
class StagingSourceFailure:
    reason: str
    detail: str
    remediation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def build_report(
    *,
    source_path: Path = DEFAULT_SOURCE_PATH,
    row_id: str = DEFAULT_ROW_ID,
    plan_index_path: Path = DEFAULT_PLAN_INDEX_PATH,
    snapshots_path: Path = DEFAULT_SNAPSHOTS_PATH,
    ingestion_receipts_path: Path = DEFAULT_INGESTION_RECEIPTS_PATH,
) -> dict[str, object]:
    failures: list[StagingSourceFailure] = []
    source_hash = Support.file_hash(source_path)
    row = Support.find_plan_row(plan_index_path, row_id)
    snapshot = Support.find_snapshot(snapshots_path, row_id=row_id, source_hash=source_hash)
    receipt = Support.find_receipt(
        ingestion_receipts_path,
        row_id=row_id,
        source_hash=source_hash,
        snapshot_id=str(snapshot.get("snapshot_id") or ""),
    )

    if not source_hash:
        failures.append(
            StagingSourceFailure(
                reason="staging_source_missing",
                detail=f"source path does not exist or cannot be read: {source_path}",
                remediation="Restore the staging source or pass the archived source path.",
            )
        )
    if not row:
        failures.append(
            StagingSourceFailure(
                reason="plan_row_missing",
                detail=f"PlanRow {row_id!r} was not found.",
                remediation="Ingest the staging source into the existing current PlanRow.",
            )
        )
    elif Support.row_source_hash(row) != source_hash:
        failures.append(
            StagingSourceFailure(
                reason="plan_row_source_hash_mismatch",
                detail=(
                    f"PlanRow source hash {Support.row_source_hash(row)!r} does not match "
                    f"staging source hash {source_hash!r}."
                ),
                remediation="Re-ingest the exact source file or use the matching archived source.",
            )
        )
    if not snapshot:
        failures.append(
            StagingSourceFailure(
                reason="plan_source_snapshot_missing",
                detail="No PlanSourceSnapshot names the row and source hash.",
                remediation="Write a typed PlanSourceSnapshot for this source before deleting it.",
            )
        )
    if not receipt:
        failures.append(
            StagingSourceFailure(
                reason="plan_ingestion_receipt_missing",
                detail="No accepted PlanIntentIngestionReceipt names the row and source hash.",
                remediation="Ingest through the typed plan-intake path and retain the receipt id.",
            )
        )
    return {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "command": COMMAND,
        "timestamp": utc_timestamp(),
        "ok": not failures,
        "source_path": str(Support.repo_relative(source_path)),
        "source_hash": source_hash,
        "row_id": row_id,
        "plan_row_found": bool(row),
        "plan_row_source_hash": Support.row_source_hash(row),
        "source_snapshot_id": str(snapshot.get("snapshot_id") or ""),
        "ingestion_receipt_id": str(receipt.get("receipt_id") or ""),
        "disposition": Support.receipt_disposition(receipt, row_id),
        "failure_count": len(failures),
        "failures": [failure.to_dict() for failure in failures],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    return Support.render_markdown(report, COMMAND)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_PATH)
    parser.add_argument("--row-id", default=DEFAULT_ROW_ID)
    parser.add_argument("--plan-index-path", type=Path, default=DEFAULT_PLAN_INDEX_PATH)
    parser.add_argument("--snapshots-path", type=Path, default=DEFAULT_SNAPSHOTS_PATH)
    parser.add_argument(
        "--ingestion-receipts-path",
        type=Path,
        default=DEFAULT_INGESTION_RECEIPTS_PATH,
    )
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args(argv)
    try:
        report = build_report(
            source_path=args.source,
            row_id=args.row_id,
            plan_index_path=args.plan_index_path,
            snapshots_path=args.snapshots_path,
            ingestion_receipts_path=args.ingestion_receipts_path,
        )
    except Exception as exc:  # pragma: no cover - defensive guard wrapper
        return emit_runtime_error(COMMAND, args.format, str(exc))
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_markdown(report))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
