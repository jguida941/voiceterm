import json
from pathlib import Path

from dev.scripts.checks import check_receipt_schema_validation as guard


GOOD_SHA = "9b321ff7ae708f6f848fc430ba2e38a69659daae"


def _write_receipt(path: Path, **overrides: object) -> None:
    payload: dict[str, object] = {
        "contract_id": "FeatureProofReceipt",
        "schema_version": 1,
        "feature_id": "MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1",
        "commit_sha": GOOD_SHA,
        "implementer_actor": "codex",
        "review_fleet_roles_ran": ["reviewer"],
        "review_fleet_actor": "claude",
        "tests_run": [
            "dev/scripts/devctl/tests/checks/test_check_receipt_schema_validation.py::test_valid_feature_proof_receipt_passes"
        ],
        "tests_passed_count": 1,
        "tests_failed_count": 0,
        "connectivity_guards_ran": ["check_receipt_schema_validation"],
        "connectivity_guards_passed": True,
        "dogfood_invocation_evidence_ref": "command_output:test-python:abc123",
        "real_life_test_status": "proven_passed",
        "not_tested_rationale": None,
        "bypass_audit_trail_refs": [],
        "proven_at_utc": "2026-05-21T23:40:00Z",
        "evidence_artifacts": ["command_output:test-python:abc123"],
        "role_review_receipt_refs": [],
        "role_review_timeout_refs": [],
    }
    payload.update(overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_valid_feature_proof_receipt_passes(tmp_path: Path) -> None:
    proof_dir = tmp_path / "feature_proof_receipts"
    _write_receipt(proof_dir / f"{GOOD_SHA}.json")

    report = guard.build_report(
        feature_proof_dir=proof_dir,
        repo_root=tmp_path,
        commit_exists=lambda sha: sha == GOOD_SHA,
    )

    assert report["ok"] is True
    assert report["violation_count"] == 0


def test_proven_passed_requires_concrete_pytest_node(tmp_path: Path) -> None:
    proof_dir = tmp_path / "feature_proof_receipts"
    _write_receipt(
        proof_dir / f"{GOOD_SHA}.json",
        tests_run=["python3 dev/scripts/checks/check_receipt_schema_validation.py --format json"],
    )

    report = guard.build_report(
        feature_proof_dir=proof_dir,
        repo_root=tmp_path,
        commit_exists=lambda sha: sha == GOOD_SHA,
    )

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "feature_proof_receipt_proven_passed_without_pytest_node" in reasons


def test_commit_sha_must_resolve(tmp_path: Path) -> None:
    proof_dir = tmp_path / "feature_proof_receipts"
    _write_receipt(proof_dir / "missing.json", commit_sha="deadbeef")

    report = guard.build_report(
        feature_proof_dir=proof_dir,
        repo_root=tmp_path,
        commit_exists=lambda sha: False,
    )

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "feature_proof_receipt_unresolved_commit_sha" in reasons


def test_not_tested_requires_rationale(tmp_path: Path) -> None:
    proof_dir = tmp_path / "feature_proof_receipts"
    _write_receipt(
        proof_dir / f"{GOOD_SHA}.json",
        real_life_test_status="not_tested_with_rationale",
        not_tested_rationale="",
    )

    report = guard.build_report(
        feature_proof_dir=proof_dir,
        repo_root=tmp_path,
        commit_exists=lambda sha: sha == GOOD_SHA,
    )

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "feature_proof_receipt_invalid_schema" in reasons


def test_file_evidence_artifact_must_exist(tmp_path: Path) -> None:
    proof_dir = tmp_path / "feature_proof_receipts"
    _write_receipt(
        proof_dir / f"{GOOD_SHA}.json",
        evidence_artifacts=["dev/reports/missing-output.json"],
    )

    report = guard.build_report(
        feature_proof_dir=proof_dir,
        repo_root=tmp_path,
        commit_exists=lambda sha: sha == GOOD_SHA,
    )

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "feature_proof_receipt_unresolved_evidence_artifact" in reasons


def test_changed_scope_ignores_unchanged_historical_receipts(tmp_path: Path) -> None:
    proof_dir = tmp_path / "feature_proof_receipts"
    _write_receipt(
        proof_dir / f"{GOOD_SHA}.json",
        tests_run=["python3 dev/scripts/checks/check_receipt_schema_validation.py --format json"],
    )

    report = guard.build_report(
        feature_proof_dir=proof_dir,
        repo_root=tmp_path,
        scope="changed",
        changed_paths=(),
        commit_exists=lambda sha: sha == GOOD_SHA,
    )

    assert report["ok"] is True
    assert report["feature_proof_receipt_count"] == 0


def test_changed_scope_validates_changed_receipt(tmp_path: Path) -> None:
    proof_dir = tmp_path / "feature_proof_receipts"
    path = proof_dir / f"{GOOD_SHA}.json"
    _write_receipt(
        path,
        tests_run=["python3 dev/scripts/checks/check_receipt_schema_validation.py --format json"],
    )

    report = guard.build_report(
        feature_proof_dir=proof_dir,
        repo_root=tmp_path,
        scope="changed",
        changed_paths=(path,),
        commit_exists=lambda sha: sha == GOOD_SHA,
    )

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "feature_proof_receipt_proven_passed_without_pytest_node" in reasons


def test_git_status_parser_preserves_leading_dev_path() -> None:
    assert (
        guard._path_from_git_status_line(
            " M dev/reports/feature_proof_receipts/example.json"
        )
        == "dev/reports/feature_proof_receipts/example.json"
    )
