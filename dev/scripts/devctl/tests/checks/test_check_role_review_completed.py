from pathlib import Path

from dev.scripts.checks.role_review_completed.command import (
    evaluate_role_review_completed,
    write_remediation_ledger,
)
from dev.scripts.devctl.runtime.feature_proof_receipt import (
    FeatureProofReceipt,
    write_feature_proof_receipt_artifact,
)


def _receipt(
    commit_sha: str,
    *,
    role_review_receipt_refs: tuple[str, ...] = (),
) -> FeatureProofReceipt:
    return FeatureProofReceipt(
        feature_id="MP-NEW-P208-ROLE-REVIEW-COMPLETED-S1",
        commit_sha=commit_sha,
        implementer_actor="codex",
        review_fleet_roles_ran=("GovernanceReceipt",),
        review_fleet_actor="claude",
        tests_run=("dev/scripts/devctl/tests/test_sample.py::test_real",),
        tests_passed_count=1,
        tests_failed_count=0,
        connectivity_guards_ran=("check_role_review_completed",),
        connectivity_guards_passed=True,
        dogfood_invocation_evidence_ref="proof-output.txt",
        real_life_test_status="proven_passed",
        not_tested_rationale=None,
        bypass_audit_trail_refs=(),
        proven_at_utc="2026-05-16T04:00:00Z",
        evidence_artifacts=("proof-output.txt",),
        role_review_receipt_refs=role_review_receipt_refs,
    )


def test_role_review_completed_passes_with_terminal_receipt_ref(
    tmp_path: Path,
) -> None:
    write_feature_proof_receipt_artifact(
        tmp_path,
        _receipt(
            "abc123",
            role_review_receipt_refs=(
                "role_review_receipt:rev_pkt_4151:GovernanceReceipt:claude",
            ),
        ),
    )

    report = evaluate_role_review_completed(repo_root=tmp_path)

    assert report.ok is True
    assert report.scan_count == 1
    assert report.proven_passed_count == 1
    assert report.violation_count == 0


def test_role_review_completed_fails_without_terminal_receipt_ref(
    tmp_path: Path,
) -> None:
    write_feature_proof_receipt_artifact(tmp_path, _receipt("def456"))

    report = evaluate_role_review_completed(repo_root=tmp_path)

    assert report.ok is False
    assert report.scan_count == 1
    assert report.violation_count == 1
    assert (
        "missing_role_review_terminal_ref:GovernanceReceipt"
        in report.failure_reasons
    )


def test_role_review_completed_writes_and_consumes_remediation_ledger(
    tmp_path: Path,
) -> None:
    write_feature_proof_receipt_artifact(tmp_path, _receipt("def456"))
    report = evaluate_role_review_completed(repo_root=tmp_path)

    updated = write_remediation_ledger(report, repo_root=tmp_path)
    suppressed = evaluate_role_review_completed(repo_root=tmp_path)

    ledger = tmp_path / "dev/state/role_review_completed_remediation_findings.jsonl"
    assert updated.remediation_findings_written == 1
    assert ledger.exists()
    assert "RoleReviewCompletedRemediationFinding" in ledger.read_text(
        encoding="utf-8"
    )
    assert suppressed.ok is True
    assert suppressed.violation_count == 0
    assert suppressed.ledgered_violation_count == 1
