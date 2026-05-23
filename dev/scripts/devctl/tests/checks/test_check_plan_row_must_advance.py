import json
from pathlib import Path

from dev.scripts.checks import check_plan_row_must_advance as guard
from dev.scripts.devctl.tests.checks._test_jsonl_helpers import write_jsonl as _write_jsonl


ROW_ID = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"


def _paths(tmp_path: Path) -> tuple[Path, Path, Path]:
    plan_index = tmp_path / "plan_index.jsonl"
    closure_receipts = tmp_path / "plan_row_closure_receipts.jsonl"
    lifecycle_receipts = tmp_path / "slice_lifecycle_receipts.jsonl"
    closure_receipts.write_text("", encoding="utf-8")
    lifecycle_receipts.write_text("", encoding="utf-8")
    return plan_index, closure_receipts, lifecycle_receipts


def _in_progress_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "contract_id": "PlanRow",
        "row_id": ROW_ID,
        "status": "in_progress",
        "commit_anchor_ref": "",
        "applied_at_utc": "",
        "work_evidence_ids": [
            "plan_source_snapshot:plan-source-a",
            "plan_intent_receipt:plan-ingest-a",
            "typed_action:plan-intent-action-a",
            "command_output:test-python:red-a",
        ],
    }
    row.update(overrides)
    return row


def test_in_progress_row_with_evidence_churn_without_advancement_fails(tmp_path: Path) -> None:
    plan_index, closure_receipts, lifecycle_receipts = _paths(tmp_path)
    _write_jsonl(plan_index, [_in_progress_row()])

    report = guard.build_report(
        row_id=ROW_ID,
        plan_index_path=plan_index,
        closure_receipts_path=closure_receipts,
        lifecycle_receipts_path=lifecycle_receipts,
        evidence_threshold=3,
    )

    assert report["ok"] is False
    assert report["work_evidence_count"] == 4
    assert report["violation_count"] == 1
    assert report["violations"][0]["reason"] == "plan_row_evidence_churn_without_advancement"


def test_row_below_evidence_threshold_passes(tmp_path: Path) -> None:
    plan_index, closure_receipts, lifecycle_receipts = _paths(tmp_path)
    _write_jsonl(
        plan_index,
        [
            _in_progress_row(
                work_evidence_ids=[
                    "plan_source_snapshot:plan-source-a",
                    "plan_intent_receipt:plan-ingest-a",
                ]
            )
        ],
    )

    report = guard.build_report(
        row_id=ROW_ID,
        plan_index_path=plan_index,
        closure_receipts_path=closure_receipts,
        lifecycle_receipts_path=lifecycle_receipts,
        evidence_threshold=3,
    )

    assert report["ok"] is True
    assert report["violation_count"] == 0


def test_row_with_commit_anchor_passes(tmp_path: Path) -> None:
    plan_index, closure_receipts, lifecycle_receipts = _paths(tmp_path)
    _write_jsonl(plan_index, [_in_progress_row(commit_anchor_ref="commit:abc123")])

    report = guard.build_report(
        row_id=ROW_ID,
        plan_index_path=plan_index,
        closure_receipts_path=closure_receipts,
        lifecycle_receipts_path=lifecycle_receipts,
        evidence_threshold=3,
    )

    assert report["ok"] is True
    assert report["has_commit_anchor"] is True


def test_row_with_closure_receipt_passes(tmp_path: Path) -> None:
    plan_index, closure_receipts, lifecycle_receipts = _paths(tmp_path)
    _write_jsonl(plan_index, [_in_progress_row()])
    _write_jsonl(
        closure_receipts,
        [
            {
                "contract_id": "PlanRowClosureReceipt",
                "plan_row_id": ROW_ID,
                "closure_succeeded": True,
            }
        ],
    )

    report = guard.build_report(
        row_id=ROW_ID,
        plan_index_path=plan_index,
        closure_receipts_path=closure_receipts,
        lifecycle_receipts_path=lifecycle_receipts,
        evidence_threshold=3,
    )

    assert report["ok"] is True
    assert report["has_closure_receipt"] is True


def test_row_with_typed_blocker_or_abort_receipt_passes(tmp_path: Path) -> None:
    plan_index, closure_receipts, lifecycle_receipts = _paths(tmp_path)
    _write_jsonl(plan_index, [_in_progress_row()])
    _write_jsonl(
        lifecycle_receipts,
        [
            {
                "contract_id": "SliceBlockedReceipt",
                "plan_row_id": ROW_ID,
                "status": "blocked",
            }
        ],
    )

    report = guard.build_report(
        row_id=ROW_ID,
        plan_index_path=plan_index,
        closure_receipts_path=closure_receipts,
        lifecycle_receipts_path=lifecycle_receipts,
        evidence_threshold=3,
    )

    assert report["ok"] is True
    assert report["has_typed_blocker_or_abort"] is True


def test_missing_or_blank_row_id_fails_closed(tmp_path: Path) -> None:
    plan_index, closure_receipts, lifecycle_receipts = _paths(tmp_path)

    report = guard.build_report(
        row_id="",
        plan_index_path=plan_index,
        closure_receipts_path=closure_receipts,
        lifecycle_receipts_path=lifecycle_receipts,
    )

    assert report["ok"] is False
    assert report["violations"][0]["reason"] == "blank_plan_row_id"
