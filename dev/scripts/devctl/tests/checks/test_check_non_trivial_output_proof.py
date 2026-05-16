from pathlib import Path

from dev.scripts.checks.non_trivial_output_proof.command import (
    evaluate_non_trivial_output_proof,
    write_remediation_ledger,
)
from dev.scripts.devctl.runtime.feature_proof_receipt import (
    FEATURE_PROOF_RECEIPT_ARTIFACT_ROOT,
    FeatureProofReceipt,
    write_feature_proof_receipt_artifact,
)


def _receipt(
    commit_sha: str,
    *,
    evidence_ref: str = "proof-output.txt",
    tests_run: tuple[str, ...] = ("dev/scripts/devctl/tests/test_sample.py::test_real",),
) -> FeatureProofReceipt:
    return FeatureProofReceipt(
        feature_id="MP-NEW-P230-OUTPUT-TRUTH-SPINE-S1",
        commit_sha=commit_sha,
        implementer_actor="codex",
        review_fleet_roles_ran=("DogfoodTest",),
        review_fleet_actor="claude",
        tests_run=tests_run,
        tests_passed_count=1,
        tests_failed_count=0,
        connectivity_guards_ran=("check_non_trivial_output_proof",),
        connectivity_guards_passed=True,
        dogfood_invocation_evidence_ref=evidence_ref,
        real_life_test_status="proven_passed",
        not_tested_rationale=None,
        bypass_audit_trail_refs=(),
        proven_at_utc="2026-05-16T04:00:00Z",
        evidence_artifacts=(evidence_ref,),
        role_review_receipt_refs=(
            "role_review_receipt:rev_pkt_4151:DogfoodTest:claude",
        ),
    )


def test_non_trivial_output_proof_guard_passes_on_resolved_real_test(
    tmp_path: Path,
) -> None:
    (tmp_path / "proof-output.txt").write_text("expected output\n", encoding="utf-8")
    _write_test_file(tmp_path)
    write_feature_proof_receipt_artifact(tmp_path, _receipt("abc123"))

    report = evaluate_non_trivial_output_proof(repo_root=tmp_path)

    assert report.ok is True
    assert report.scan_count == 1
    assert report.proven_passed_count == 1
    assert report.assertions_evaluated_count == 4
    assert report.failure_reasons == ()


def test_non_trivial_output_proof_guard_fails_closed_on_trivial_receipt(
    tmp_path: Path,
) -> None:
    write_feature_proof_receipt_artifact(
        tmp_path,
        _receipt(
            "def456",
            evidence_ref=FEATURE_PROOF_RECEIPT_ARTIFACT_ROOT,
            tests_run=("python3 dev/scripts/checks/check_feature_has_proof_receipt.py",),
        ),
    )

    report = evaluate_non_trivial_output_proof(repo_root=tmp_path)

    assert report.ok is False
    assert report.scan_count == 1
    assert report.assertions_evaluated_count == 4
    assert report.violation_count == 1
    assert "no_real_tests" in report.failure_reasons
    assert any(
        reason.startswith("circular_ref:")
        for reason in report.violations[0]["failure_reasons"]
    )


def test_non_trivial_output_proof_guard_writes_remediation_ledger(
    tmp_path: Path,
) -> None:
    write_feature_proof_receipt_artifact(
        tmp_path,
        _receipt("def456", evidence_ref="missing-output.txt"),
    )
    report = evaluate_non_trivial_output_proof(repo_root=tmp_path)

    updated = write_remediation_ledger(report, repo_root=tmp_path)

    ledger = tmp_path / "dev/state/non_trivial_output_proof_remediation_findings.jsonl"
    assert updated.remediation_findings_written == 1
    assert ledger.exists()
    assert "NonTrivialOutputProofRemediationFinding" in ledger.read_text(
        encoding="utf-8"
    )


def test_non_trivial_output_proof_guard_rejects_fake_pytest_node(
    tmp_path: Path,
) -> None:
    (tmp_path / "proof-output.txt").write_text("expected output\n", encoding="utf-8")
    _write_test_file(tmp_path)
    write_feature_proof_receipt_artifact(
        tmp_path,
        _receipt(
            "badnode",
            tests_run=("dev/scripts/devctl/tests/test_sample.py::test_missing",),
        ),
    )

    report = evaluate_non_trivial_output_proof(repo_root=tmp_path)

    assert report.ok is False
    assert report.violation_count == 1
    assert "no_real_tests" in report.failure_reasons


def _write_test_file(repo_root: Path) -> None:
    test_path = repo_root / "dev/scripts/devctl/tests/test_sample.py"
    test_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.write_text("def test_real():\n    assert True\n", encoding="utf-8")
