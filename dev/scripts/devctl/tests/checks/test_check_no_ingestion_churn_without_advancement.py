import json
from pathlib import Path

from dev.scripts.checks import check_no_ingestion_churn_without_advancement as guard
from dev.scripts.devctl.tests.checks._test_jsonl_helpers import write_jsonl as _write_jsonl


ROW_ID = "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1"
SOURCE = "delete_after_ingest.md"


def _snapshot(snapshot_id: str, captured_at: str, *, source: str = SOURCE) -> dict[str, object]:
    return {
        "contract_id": "PlanSourceSnapshot",
        "snapshot_id": snapshot_id,
        "action_id": f"plan-intent-action-{snapshot_id}",
        "captured_at_utc": captured_at,
        "source_ref": source,
        "plan_row_id": ROW_ID,
        "composition_disposition": "amends_existing_owner_row",
        "existing_owner_row_refs": [ROW_ID],
    }


def _plan_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "contract_id": "PlanRow",
        "row_id": ROW_ID,
        "status": "in_progress",
        "commit_anchor_ref": "",
        "applied_at_utc": "",
    }
    row.update(overrides)
    return row


def _paths(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    snapshots = tmp_path / "plan_source_snapshots.jsonl"
    plan_index = tmp_path / "plan_index.jsonl"
    closures = tmp_path / "plan_row_closure_receipts.jsonl"
    lifecycle = tmp_path / "slice_lifecycle_receipts.jsonl"
    fprs = tmp_path / "feature_proof_receipts"
    closures.write_text("", encoding="utf-8")
    lifecycle.write_text("", encoding="utf-8")
    fprs.mkdir()
    _write_jsonl(plan_index, [_plan_row()])
    return snapshots, plan_index, closures, lifecycle, fprs


def test_three_same_source_snapshots_without_advancement_fails(tmp_path: Path) -> None:
    snapshots, plan_index, closures, lifecycle, fprs = _paths(tmp_path)
    _write_jsonl(
        snapshots,
        [
            _snapshot("a", "2026-05-21T10:00:00Z"),
            _snapshot("b", "2026-05-21T11:00:00Z"),
            _snapshot("c", "2026-05-21T12:00:00Z"),
        ],
    )

    report = guard.build_report(
        snapshots_path=snapshots,
        plan_index_path=plan_index,
        closure_receipts_path=closures,
        lifecycle_receipts_path=lifecycle,
        feature_proof_dir=fprs,
        window_hours=24,
        max_snapshots=2,
    )

    assert report["ok"] is False
    assert report["violation_count"] == 1
    assert report["violations"][0]["reason"] == "ingestion_churn_without_advancement"
    assert report["violations"][0]["source_ref"] == SOURCE
    assert report["violations"][0]["snapshot_count"] == "3"


def test_two_same_source_snapshots_pass(tmp_path: Path) -> None:
    snapshots, plan_index, closures, lifecycle, fprs = _paths(tmp_path)
    _write_jsonl(
        snapshots,
        [
            _snapshot("a", "2026-05-21T10:00:00Z"),
            _snapshot("b", "2026-05-21T11:00:00Z"),
        ],
    )

    report = guard.build_report(
        snapshots_path=snapshots,
        plan_index_path=plan_index,
        closure_receipts_path=closures,
        lifecycle_receipts_path=lifecycle,
        feature_proof_dir=fprs,
        window_hours=24,
        max_snapshots=2,
    )

    assert report["ok"] is True
    assert report["violation_count"] == 0


def test_plan_row_commit_anchor_breaks_churn(tmp_path: Path) -> None:
    snapshots, plan_index, closures, lifecycle, fprs = _paths(tmp_path)
    _write_jsonl(
        plan_index,
        [_plan_row(commit_anchor_ref="commit:abc123", applied_at_utc="2026-05-21T12:30:00Z")],
    )
    _write_jsonl(
        snapshots,
        [
            _snapshot("a", "2026-05-21T10:00:00Z"),
            _snapshot("b", "2026-05-21T11:00:00Z"),
            _snapshot("c", "2026-05-21T12:00:00Z"),
        ],
    )

    report = guard.build_report(
        snapshots_path=snapshots,
        plan_index_path=plan_index,
        closure_receipts_path=closures,
        lifecycle_receipts_path=lifecycle,
        feature_proof_dir=fprs,
        window_hours=24,
        max_snapshots=2,
    )

    assert report["ok"] is True
    assert report["groups"][0]["has_plan_row_commit_anchor"] is True


def test_closure_receipt_breaks_churn(tmp_path: Path) -> None:
    snapshots, plan_index, closures, lifecycle, fprs = _paths(tmp_path)
    _write_jsonl(
        snapshots,
        [
            _snapshot("a", "2026-05-21T10:00:00Z"),
            _snapshot("b", "2026-05-21T11:00:00Z"),
            _snapshot("c", "2026-05-21T12:00:00Z"),
        ],
    )
    _write_jsonl(
        closures,
        [
            {
                "contract_id": "PlanRowClosureReceipt",
                "plan_row_id": ROW_ID,
                "closure_succeeded": True,
            }
        ],
    )

    report = guard.build_report(
        snapshots_path=snapshots,
        plan_index_path=plan_index,
        closure_receipts_path=closures,
        lifecycle_receipts_path=lifecycle,
        feature_proof_dir=fprs,
        window_hours=24,
        max_snapshots=2,
    )

    assert report["ok"] is True
    assert report["groups"][0]["has_closure_receipt"] is True


def test_typed_blocker_or_abort_breaks_churn(tmp_path: Path) -> None:
    snapshots, plan_index, closures, lifecycle, fprs = _paths(tmp_path)
    _write_jsonl(
        snapshots,
        [
            _snapshot("a", "2026-05-21T10:00:00Z"),
            _snapshot("b", "2026-05-21T11:00:00Z"),
            _snapshot("c", "2026-05-21T12:00:00Z"),
        ],
    )
    _write_jsonl(
        lifecycle,
        [
            {
                "contract_id": "SliceBlockedReceipt",
                "plan_row_id": ROW_ID,
                "status": "blocked",
            }
        ],
    )

    report = guard.build_report(
        snapshots_path=snapshots,
        plan_index_path=plan_index,
        closure_receipts_path=closures,
        lifecycle_receipts_path=lifecycle,
        feature_proof_dir=fprs,
        window_hours=24,
        max_snapshots=2,
    )

    assert report["ok"] is True
    assert report["groups"][0]["has_typed_blocker_or_abort"] is True


def test_proven_feature_proof_breaks_churn(tmp_path: Path) -> None:
    snapshots, plan_index, closures, lifecycle, fprs = _paths(tmp_path)
    _write_jsonl(
        snapshots,
        [
            _snapshot("a", "2026-05-21T10:00:00Z"),
            _snapshot("b", "2026-05-21T11:00:00Z"),
            _snapshot("c", "2026-05-21T12:00:00Z"),
        ],
    )
    (fprs / "abc123.json").write_text(
        json.dumps(
            {
                "contract_id": "FeatureProofReceipt",
                "plan_row_id": ROW_ID,
                "real_life_test_status": "proven_passed",
                "tests_run": [
                    "dev/scripts/devctl/tests/checks/"
                    "test_check_no_ingestion_churn_without_advancement.py::"
                    "test_proven_feature_proof_breaks_churn"
                ],
            }
        ),
        encoding="utf-8",
    )

    report = guard.build_report(
        snapshots_path=snapshots,
        plan_index_path=plan_index,
        closure_receipts_path=closures,
        lifecycle_receipts_path=lifecycle,
        feature_proof_dir=fprs,
        window_hours=24,
        max_snapshots=2,
    )

    assert report["ok"] is True
    assert report["groups"][0]["has_proven_feature_proof_receipt"] is True


def test_default_row_scope_ignores_unrelated_historical_churn(tmp_path: Path) -> None:
    snapshots, plan_index, closures, lifecycle, fprs = _paths(tmp_path)
    unrelated_row = "MP377-UNRELATED-HISTORICAL-S1"
    _write_jsonl(
        plan_index,
        [
            _plan_row(),
            {
                "contract_id": "PlanRow",
                "row_id": unrelated_row,
                "status": "in_progress",
                "commit_anchor_ref": "",
                "applied_at_utc": "",
            },
        ],
    )
    _write_jsonl(
        snapshots,
        [
            _snapshot("a", "2026-05-21T10:00:00Z", source="old.md")
            | {"plan_row_id": unrelated_row, "existing_owner_row_refs": [unrelated_row]},
            _snapshot("b", "2026-05-21T11:00:00Z", source="old.md")
            | {"plan_row_id": unrelated_row, "existing_owner_row_refs": [unrelated_row]},
            _snapshot("c", "2026-05-21T12:00:00Z", source="old.md")
            | {"plan_row_id": unrelated_row, "existing_owner_row_refs": [unrelated_row]},
        ],
    )

    report = guard.build_report(
        snapshots_path=snapshots,
        plan_index_path=plan_index,
        closure_receipts_path=closures,
        lifecycle_receipts_path=lifecycle,
        feature_proof_dir=fprs,
        row_id=ROW_ID,
        window_hours=24,
        max_snapshots=2,
    )

    assert report["ok"] is True
    assert report["group_count"] == 0
