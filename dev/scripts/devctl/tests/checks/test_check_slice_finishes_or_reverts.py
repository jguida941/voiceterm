import json
from pathlib import Path

from dev.scripts.checks import check_slice_finishes_or_reverts as guard
from dev.scripts.devctl.tests.checks._test_jsonl_helpers import write_jsonl as _write_jsonl


ROW_ID = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"


def test_half_built_dirty_slice_without_receipt_fails(tmp_path: Path) -> None:
    plan_index = tmp_path / "plan_index.jsonl"
    closure_receipts = tmp_path / "plan_row_closure_receipts.jsonl"
    feature_proof_dir = tmp_path / "feature_proof_receipts"
    abort_receipts = tmp_path / "slice_lifecycle_receipts.jsonl"
    feature_proof_dir.mkdir()
    closure_receipts.write_text("", encoding="utf-8")
    abort_receipts.write_text("", encoding="utf-8")
    _write_jsonl(
        plan_index,
        [
            {
                "contract_id": "PlanRow",
                "row_id": ROW_ID,
                "status": "in_progress",
                "commit_anchor_ref": "",
                "applied_at_utc": "",
                "work_evidence_ids": [
                    "plan_source_snapshot:plan-source-a",
                    "plan_intent_receipt:plan-ingest-a",
                    "typed_action:plan-intent-action-a",
                ],
            }
        ],
    )

    report = guard.build_report(
        row_id=ROW_ID,
        plan_index_path=plan_index,
        closure_receipts_path=closure_receipts,
        feature_proof_dir=feature_proof_dir,
        abort_receipts_path=abort_receipts,
        git_status_output=(
            " M dev/scripts/devctl/runtime/foo.py\n"
            "?? dev/scripts/checks/check_new_half_built.py\n"
        ),
    )

    assert report["ok"] is False
    assert report["dirty_file_count"] == 2
    assert report["violation_count"] == 1
    assert report["violations"][0]["reason"] == "slice_left_half_built_without_receipt"


def test_completed_slice_with_closure_and_proven_fpr_passes(tmp_path: Path) -> None:
    plan_index = tmp_path / "plan_index.jsonl"
    closure_receipts = tmp_path / "plan_row_closure_receipts.jsonl"
    feature_proof_dir = tmp_path / "feature_proof_receipts"
    abort_receipts = tmp_path / "slice_lifecycle_receipts.jsonl"
    feature_proof_dir.mkdir()
    abort_receipts.write_text("", encoding="utf-8")
    _write_jsonl(
        plan_index,
        [
            {
                "contract_id": "PlanRow",
                "row_id": ROW_ID,
                "status": "applied",
                "commit_anchor_ref": "commit:abc123",
                "applied_at_utc": "2026-05-21T23:10:00Z",
                "work_evidence_ids": [],
            }
        ],
    )
    _write_jsonl(
        closure_receipts,
        [
            {
                "contract_id": "PlanRowClosureReceipt",
                "plan_row_id": ROW_ID,
                "closure_succeeded": True,
                "commit_sha": "abc123",
            }
        ],
    )
    (feature_proof_dir / "abc123.json").write_text(
        json.dumps(
            {
                "contract_id": "FeatureProofReceipt",
                "plan_row_id": ROW_ID,
                "real_life_test_status": "proven_passed",
                "tests_run": [
                    "dev/scripts/devctl/tests/checks/"
                    "test_check_slice_finishes_or_reverts.py::"
                    "test_completed_slice_with_closure_and_proven_fpr_passes"
                ],
            }
        ),
        encoding="utf-8",
    )

    report = guard.build_report(
        row_id=ROW_ID,
        plan_index_path=plan_index,
        closure_receipts_path=closure_receipts,
        feature_proof_dir=feature_proof_dir,
        abort_receipts_path=abort_receipts,
        git_status_output="",
    )

    assert report["ok"] is True
    assert report["violation_count"] == 0


def test_completed_slice_without_commit_anchor_fails(tmp_path: Path) -> None:
    plan_index = tmp_path / "plan_index.jsonl"
    closure_receipts = tmp_path / "plan_row_closure_receipts.jsonl"
    feature_proof_dir = tmp_path / "feature_proof_receipts"
    abort_receipts = tmp_path / "slice_lifecycle_receipts.jsonl"
    feature_proof_dir.mkdir()
    abort_receipts.write_text("", encoding="utf-8")
    _write_jsonl(
        plan_index,
        [
            {
                "contract_id": "PlanRow",
                "row_id": ROW_ID,
                "status": "completed",
                "commit_anchor_ref": "",
                "applied_at_utc": "2026-05-21T23:10:00Z",
                "work_evidence_ids": [],
            }
        ],
    )
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
    (feature_proof_dir / "abc123.json").write_text(
        json.dumps(
            {
                "contract_id": "FeatureProofReceipt",
                "feature_id": ROW_ID,
                "real_life_test_status": "proven_passed",
                "tests_run": [
                    "dev/scripts/devctl/tests/checks/"
                    "test_check_slice_finishes_or_reverts.py::"
                    "test_completed_slice_without_commit_anchor_fails"
                ],
            }
        ),
        encoding="utf-8",
    )

    report = guard.build_report(
        row_id=ROW_ID,
        plan_index_path=plan_index,
        closure_receipts_path=closure_receipts,
        feature_proof_dir=feature_proof_dir,
        abort_receipts_path=abort_receipts,
        git_status_output="",
    )

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "completed_slice_missing_commit_anchor" in reasons


def test_completed_slice_without_closure_receipt_fails(tmp_path: Path) -> None:
    plan_index = tmp_path / "plan_index.jsonl"
    closure_receipts = tmp_path / "plan_row_closure_receipts.jsonl"
    feature_proof_dir = tmp_path / "feature_proof_receipts"
    abort_receipts = tmp_path / "slice_lifecycle_receipts.jsonl"
    feature_proof_dir.mkdir()
    closure_receipts.write_text("", encoding="utf-8")
    abort_receipts.write_text("", encoding="utf-8")
    _write_jsonl(
        plan_index,
        [
            {
                "contract_id": "PlanRow",
                "row_id": ROW_ID,
                "status": "applied",
                "commit_anchor_ref": "commit:abc123",
                "applied_at_utc": "2026-05-21T23:10:00Z",
                "work_evidence_ids": [],
            }
        ],
    )
    (feature_proof_dir / "abc123.json").write_text(
        json.dumps(
            {
                "contract_id": "FeatureProofReceipt",
                "feature_id": ROW_ID,
                "real_life_test_status": "proven_passed",
                "tests_run": [
                    "dev/scripts/devctl/tests/checks/"
                    "test_check_slice_finishes_or_reverts.py::"
                    "test_completed_slice_without_closure_receipt_fails"
                ],
            }
        ),
        encoding="utf-8",
    )

    report = guard.build_report(
        row_id=ROW_ID,
        plan_index_path=plan_index,
        closure_receipts_path=closure_receipts,
        feature_proof_dir=feature_proof_dir,
        abort_receipts_path=abort_receipts,
        git_status_output="",
    )

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "completed_slice_missing_closure_receipt" in reasons


def test_completed_slice_without_proven_fpr_fails(tmp_path: Path) -> None:
    plan_index = tmp_path / "plan_index.jsonl"
    closure_receipts = tmp_path / "plan_row_closure_receipts.jsonl"
    feature_proof_dir = tmp_path / "feature_proof_receipts"
    abort_receipts = tmp_path / "slice_lifecycle_receipts.jsonl"
    feature_proof_dir.mkdir()
    abort_receipts.write_text("", encoding="utf-8")
    _write_jsonl(
        plan_index,
        [
            {
                "contract_id": "PlanRow",
                "row_id": ROW_ID,
                "status": "closed",
                "commit_anchor_ref": "commit:abc123",
                "applied_at_utc": "2026-05-21T23:10:00Z",
                "work_evidence_ids": [],
            }
        ],
    )
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
        feature_proof_dir=feature_proof_dir,
        abort_receipts_path=abort_receipts,
        git_status_output="",
    )

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "completed_slice_missing_proven_feature_proof" in reasons


def test_dirty_blocked_slice_with_typed_blocker_receipt_passes(tmp_path: Path) -> None:
    plan_index = tmp_path / "plan_index.jsonl"
    closure_receipts = tmp_path / "plan_row_closure_receipts.jsonl"
    feature_proof_dir = tmp_path / "feature_proof_receipts"
    abort_receipts = tmp_path / "slice_lifecycle_receipts.jsonl"
    feature_proof_dir.mkdir()
    closure_receipts.write_text("", encoding="utf-8")
    _write_jsonl(
        plan_index,
        [
            {
                "contract_id": "PlanRow",
                "row_id": ROW_ID,
                "status": "in_progress",
                "commit_anchor_ref": "",
                "applied_at_utc": "",
                "work_evidence_ids": ["plan_source_snapshot:plan-source-a"],
            }
        ],
    )
    _write_jsonl(
        abort_receipts,
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
        feature_proof_dir=feature_proof_dir,
        abort_receipts_path=abort_receipts,
        git_status_output=" M dev/scripts/devctl/runtime/foo.py\n",
    )

    assert report["ok"] is True
    assert report["has_slice_abort_or_block_receipt"] is True


def test_proven_fpr_without_closure_or_commit_anchor_still_fails(tmp_path: Path) -> None:
    plan_index = tmp_path / "plan_index.jsonl"
    closure_receipts = tmp_path / "plan_row_closure_receipts.jsonl"
    feature_proof_dir = tmp_path / "feature_proof_receipts"
    abort_receipts = tmp_path / "slice_lifecycle_receipts.jsonl"
    feature_proof_dir.mkdir()
    closure_receipts.write_text("", encoding="utf-8")
    abort_receipts.write_text("", encoding="utf-8")
    _write_jsonl(
        plan_index,
        [
            {
                "contract_id": "PlanRow",
                "row_id": ROW_ID,
                "status": "in_progress",
                "commit_anchor_ref": "",
                "applied_at_utc": "",
                "work_evidence_ids": ["feature_proof_receipt:fake"],
            }
        ],
    )
    (feature_proof_dir / "fake.json").write_text(
        json.dumps(
            {
                "contract_id": "FeatureProofReceipt",
                "feature_id": ROW_ID,
                "real_life_test_status": "proven_passed",
                "tests_run": [
                    "dev/scripts/devctl/tests/checks/"
                    "test_check_slice_finishes_or_reverts.py::"
                    "test_proven_fpr_without_closure_or_commit_anchor_still_fails"
                ],
            }
        ),
        encoding="utf-8",
    )

    report = guard.build_report(
        row_id=ROW_ID,
        plan_index_path=plan_index,
        closure_receipts_path=closure_receipts,
        feature_proof_dir=feature_proof_dir,
        abort_receipts_path=abort_receipts,
        git_status_output=" M dev/scripts/devctl/runtime/foo.py\n",
    )

    assert report["ok"] is False
    assert report["violations"][0]["reason"] == "slice_left_half_built_without_receipt"


def test_missing_or_blank_plan_row_fails_closed(tmp_path: Path) -> None:
    report = guard.build_report(
        row_id="",
        plan_index_path=tmp_path / "plan_index.jsonl",
        closure_receipts_path=tmp_path / "plan_row_closure_receipts.jsonl",
        feature_proof_dir=tmp_path / "feature_proof_receipts",
        abort_receipts_path=tmp_path / "slice_lifecycle_receipts.jsonl",
        git_status_output="",
    )

    assert report["ok"] is False
    assert report["violations"][0]["reason"] == "blank_plan_row_id"
