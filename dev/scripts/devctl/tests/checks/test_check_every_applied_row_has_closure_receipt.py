import json
from pathlib import Path

from dev.scripts.checks import check_every_applied_row_has_closure_receipt as guard
from dev.scripts.devctl.tests.checks._test_jsonl_helpers import write_jsonl as _write_jsonl


def test_terminal_row_without_closure_receipt_fails(tmp_path: Path) -> None:
    plan_index = tmp_path / "plan_index.jsonl"
    closures = tmp_path / "plan_row_closure_receipts.jsonl"
    fprs = tmp_path / "feature_proof_receipts"
    _write_jsonl(
        plan_index,
        [
            _plan_row(
                row_id="ROW-1",
                status="applied",
                commit_anchor_ref="abc123",
                applied_at_utc="2026-05-21T00:00:00Z",
            )
        ],
    )
    _write_fpr(fprs / "abc123.json", row_id="ROW-1", commit_sha="abc123")

    report = guard.build_report(
        plan_index_path=plan_index,
        closure_receipts_path=closures,
        feature_proof_dir=fprs,
        scope="all",
    )

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "terminal_plan_row_missing_closure_receipt" in reasons


def test_terminal_row_without_proven_feature_proof_fails(tmp_path: Path) -> None:
    plan_index = tmp_path / "plan_index.jsonl"
    closures = tmp_path / "plan_row_closure_receipts.jsonl"
    fprs = tmp_path / "feature_proof_receipts"
    _write_jsonl(
        plan_index,
        [
            _plan_row(
                row_id="ROW-1",
                status="completed",
                commit_anchor_ref="abc123",
                applied_at_utc="2026-05-21T00:00:00Z",
            )
        ],
    )
    _write_jsonl(closures, [_closure(row_id="ROW-1", commit_sha="abc123")])

    report = guard.build_report(
        plan_index_path=plan_index,
        closure_receipts_path=closures,
        feature_proof_dir=fprs,
        scope="all",
    )

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "terminal_plan_row_missing_proven_feature_proof" in reasons


def test_terminal_row_with_closure_and_proven_feature_proof_passes(tmp_path: Path) -> None:
    plan_index = tmp_path / "plan_index.jsonl"
    closures = tmp_path / "plan_row_closure_receipts.jsonl"
    fprs = tmp_path / "feature_proof_receipts"
    _write_jsonl(
        plan_index,
        [
            _plan_row(
                row_id="ROW-1",
                status="closed",
                commit_anchor_ref="abc123",
                applied_at_utc="2026-05-21T00:00:00Z",
            )
        ],
    )
    _write_jsonl(closures, [_closure(row_id="ROW-1", commit_sha="abc123")])
    _write_fpr(fprs / "abc123.json", row_id="ROW-1", commit_sha="abc123")

    report = guard.build_report(
        plan_index_path=plan_index,
        closure_receipts_path=closures,
        feature_proof_dir=fprs,
        scope="all",
    )

    assert report["ok"] is True
    assert report["terminal_row_count"] == 1


def test_open_row_does_not_require_closure_receipt(tmp_path: Path) -> None:
    plan_index = tmp_path / "plan_index.jsonl"
    closures = tmp_path / "plan_row_closure_receipts.jsonl"
    fprs = tmp_path / "feature_proof_receipts"
    _write_jsonl(plan_index, [_plan_row(row_id="ROW-1", status="in_progress")])

    report = guard.build_report(
        plan_index_path=plan_index,
        closure_receipts_path=closures,
        feature_proof_dir=fprs,
        scope="all",
    )

    assert report["ok"] is True
    assert report["terminal_row_count"] == 0


def _plan_row(
    *,
    row_id: str,
    status: str,
    commit_anchor_ref: str = "",
    applied_at_utc: str = "",
) -> dict[str, object]:
    return {
        "contract_id": "PlanRow",
        "row_id": row_id,
        "status": status,
        "commit_anchor_ref": commit_anchor_ref,
        "applied_at_utc": applied_at_utc,
        "work_evidence_ids": [],
    }


def _closure(*, row_id: str, commit_sha: str) -> dict[str, object]:
    return {
        "contract_id": "PlanRowClosureReceipt",
        "plan_row_id": row_id,
        "commit_sha": commit_sha,
        "closure_succeeded": True,
    }


def _write_fpr(path: Path, *, row_id: str, commit_sha: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "contract_id": "FeatureProofReceipt",
                "schema_version": 1,
                "feature_id": row_id,
                "commit_sha": commit_sha,
                "real_life_test_status": "proven_passed",
                "tests_run": [
                    "dev/scripts/devctl/tests/checks/test_example.py::test_example"
                ],
                "evidence_artifacts": [f"plan:{row_id}"],
                "dogfood_invocation_evidence_ref": "command_output:test-python:abc",
            }
        )
        + "\n",
        encoding="utf-8",
    )


