import hashlib
import json
from pathlib import Path

from dev.scripts.checks import check_staging_source_ingested as guard
from dev.scripts.devctl.tests.checks._test_jsonl_helpers import write_jsonl as _write_jsonl


ROW_ID = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"


def test_staging_source_ingested_passes_when_hash_snapshot_and_receipt_match(tmp_path: Path) -> None:
    source = tmp_path / "delete_after_ingest.md"
    source.write_text("# source\n", encoding="utf-8")
    source_hash = "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
    plan_index = tmp_path / "plan_index.jsonl"
    snapshots = tmp_path / "plan_source_snapshots.jsonl"
    receipts = tmp_path / "plan_ingestion_receipts.jsonl"
    _write_jsonl(
        plan_index,
        [
            {
                "contract_id": "PlanRow",
                "row_id": ROW_ID,
                "content_hash": source_hash,
                "provenance": {"source_hash": source_hash},
            }
        ],
    )
    _write_jsonl(
        snapshots,
        [
            {
                "contract_id": "PlanSourceSnapshot",
                "snapshot_id": "plan-source-1",
                "plan_row_id": ROW_ID,
                "source_hash": source_hash,
            }
        ],
    )
    _write_jsonl(
        receipts,
        [
            {
                "contract_id": "PlanIntentIngestionReceipt",
                "receipt_id": "plan-ingest-1",
                "row_ids": [ROW_ID],
                "source_hash": source_hash,
                "source_snapshot_ids": ["plan-source-1"],
                "status": "accepted",
                "composition_disposition_matrix": [
                    {"row_id": ROW_ID, "disposition": "amends_existing_owner_row"}
                ],
            }
        ],
    )

    report = guard.build_report(
        source_path=source,
        row_id=ROW_ID,
        plan_index_path=plan_index,
        snapshots_path=snapshots,
        ingestion_receipts_path=receipts,
    )

    assert report["ok"] is True
    assert report["source_snapshot_id"] == "plan-source-1"
    assert report["ingestion_receipt_id"] == "plan-ingest-1"
    assert report["disposition"] == "amends_existing_owner_row"


def test_staging_source_ingested_fails_on_hash_mismatch(tmp_path: Path) -> None:
    source = tmp_path / "delete_after_ingest.md"
    source.write_text("# changed source\n", encoding="utf-8")
    plan_index = tmp_path / "plan_index.jsonl"
    snapshots = tmp_path / "plan_source_snapshots.jsonl"
    receipts = tmp_path / "plan_ingestion_receipts.jsonl"
    _write_jsonl(
        plan_index,
        [
            {
                "contract_id": "PlanRow",
                "row_id": ROW_ID,
                "content_hash": "sha256:old",
                "provenance": {"source_hash": "sha256:old"},
            }
        ],
    )
    snapshots.write_text("", encoding="utf-8")
    receipts.write_text("", encoding="utf-8")

    report = guard.build_report(
        source_path=source,
        row_id=ROW_ID,
        plan_index_path=plan_index,
        snapshots_path=snapshots,
        ingestion_receipts_path=receipts,
    )

    assert report["ok"] is False
    reasons = {failure["reason"] for failure in report["failures"]}
    assert "plan_row_source_hash_mismatch" in reasons
    assert "plan_source_snapshot_missing" in reasons
