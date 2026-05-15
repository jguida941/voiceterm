from pathlib import Path

from dev.scripts.checks.check_feature_has_proof_receipt import (
    evaluate_feature_has_proof_receipt,
)
from dev.scripts.devctl.runtime.feature_proof_receipt import (
    FeatureProofReceipt,
    write_feature_proof_receipt_artifact,
)


def _receipt(commit_sha: str, *, proven: bool = True) -> FeatureProofReceipt:
    return FeatureProofReceipt(
        feature_id="MP-NEW-P207-FEATURE-PROOF-RECEIPT-GUARD-S3",
        commit_sha=commit_sha,
        implementer_actor="codex",
        review_fleet_roles_ran=("FeatureLifecycleProof",),
        review_fleet_actor="claude",
        tests_run=("unit",),
        tests_passed_count=1 if proven else 0,
        tests_failed_count=0,
        connectivity_guards_ran=("check_feature_has_proof_receipt",),
        connectivity_guards_passed=True,
        dogfood_invocation_evidence_ref="test:feature-proof",
        real_life_test_status=(
            "proven_passed" if proven else "not_tested_with_rationale"
        ),
        not_tested_rationale=None if proven else "pre-mandate fixture",
        bypass_audit_trail_refs=("raw_git_bypass_receipt:test",),
        proven_at_utc="2026-05-15T18:30:00Z",
        evidence_artifacts=("dev/state/raw_git_bypass_receipts.jsonl",),
    )


def test_feature_has_proof_receipt_passes_when_all_commits_have_receipts(
    tmp_path: Path,
) -> None:
    write_feature_proof_receipt_artifact(tmp_path, _receipt("abc123"))
    write_feature_proof_receipt_artifact(tmp_path, _receipt("def456"))

    report = evaluate_feature_has_proof_receipt(
        repo_root=tmp_path,
        commit_shas=("abc123", "def456"),
    )

    assert report.ok is True
    assert report.commit_count == 2
    assert report.receipt_count == 2
    assert report.violation_count == 0


def test_feature_has_proof_receipt_fails_on_missing_commit_receipt(
    tmp_path: Path,
) -> None:
    write_feature_proof_receipt_artifact(tmp_path, _receipt("abc123"))

    report = evaluate_feature_has_proof_receipt(
        repo_root=tmp_path,
        commit_shas=("abc123", "def456"),
    )

    assert report.ok is False
    assert report.violation_count == 1
    assert report.violations[0]["commit_sha"] == "def456"
    assert report.violations[0]["reason"] == "missing_feature_proof_receipt"


def test_feature_has_proof_receipt_can_require_proven_passed(tmp_path: Path) -> None:
    write_feature_proof_receipt_artifact(tmp_path, _receipt("abc123", proven=False))

    report = evaluate_feature_has_proof_receipt(
        repo_root=tmp_path,
        commit_shas=("abc123",),
        require_proven_passed=True,
    )

    assert report.ok is False
    assert report.non_proven_count == 1
    assert report.violations[0]["reason"] == "real_life_test_not_proven_passed"
