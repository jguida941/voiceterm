from pathlib import Path

from dev.scripts.checks.check_feature_has_proof_receipt import (
    evaluate_feature_has_proof_receipt,
)
from dev.scripts.devctl.runtime.feature_proof_receipt import (
    FeatureProofReceipt,
    write_feature_proof_receipt_artifact,
)


def _receipt(
    commit_sha: str,
    *,
    proven: bool = True,
    tests_run: tuple[str, ...] = ("unit",),
    evidence_artifacts: tuple[str, ...] = ("dev/state/raw_git_bypass_receipts.jsonl",),
    dogfood_invocation_evidence_ref: str = "test:feature-proof",
) -> FeatureProofReceipt:
    return FeatureProofReceipt(
        feature_id="MP-NEW-P207-FEATURE-PROOF-RECEIPT-GUARD-S3",
        commit_sha=commit_sha,
        implementer_actor="codex",
        review_fleet_roles_ran=("FeatureLifecycleProof",),
        review_fleet_actor="claude",
        tests_run=tests_run,
        tests_passed_count=1 if proven else 0,
        tests_failed_count=0,
        connectivity_guards_ran=("check_feature_has_proof_receipt",),
        connectivity_guards_passed=True,
        dogfood_invocation_evidence_ref=dogfood_invocation_evidence_ref,
        real_life_test_status=(
            "proven_passed" if proven else "not_tested_with_rationale"
        ),
        not_tested_rationale=None if proven else "pre-mandate fixture",
        bypass_audit_trail_refs=("raw_git_bypass_receipt:test",),
        proven_at_utc="2026-05-15T18:30:00Z",
        evidence_artifacts=evidence_artifacts,
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


def test_feature_has_proof_receipt_allows_non_proven_for_proof_ledger_commit(
    tmp_path: Path,
) -> None:
    write_feature_proof_receipt_artifact(tmp_path, _receipt("abc123", proven=False))

    report = evaluate_feature_has_proof_receipt(
        repo_root=tmp_path,
        commit_shas=("abc123",),
        commit_paths_by_sha={
            "abc123": (
                "dev/audits/REVIEW_SNAPSHOT.md",
                "dev/state/plan_ingestion_receipts.jsonl",
                "dev/state/plan_row_closure_receipts.jsonl",
            )
        },
        require_proven_passed=True,
    )

    assert report.ok is True
    assert report.non_proven_count == 1
    assert report.violation_count == 0
    assert report.warnings == (
        "proven_passed_not_required_for_proof_ledger_commit:abc123",
    )


def test_feature_has_proof_receipt_still_requires_proven_for_mixed_source_commit(
    tmp_path: Path,
) -> None:
    write_feature_proof_receipt_artifact(tmp_path, _receipt("abc123", proven=False))

    report = evaluate_feature_has_proof_receipt(
        repo_root=tmp_path,
        commit_shas=("abc123",),
        commit_paths_by_sha={
            "abc123": (
                "dev/audits/REVIEW_SNAPSHOT.md",
                "dev/scripts/devctl/runtime/startup_signals.py",
            )
        },
        require_proven_passed=True,
    )

    assert report.ok is False
    assert report.non_proven_count == 1
    assert report.violations[0]["reason"] == "real_life_test_not_proven_passed"


def test_feature_has_proof_receipt_strict_fails_on_empty_commit_range(
    tmp_path: Path,
) -> None:
    report = evaluate_feature_has_proof_receipt(
        repo_root=tmp_path,
        commit_shas=(),
        require_non_empty_range=True,
        require_proven_passed=True,
        require_non_trivial_output_proof=True,
    )

    assert report.ok is False
    assert report.commit_count == 0
    assert report.receipt_count == 0
    assert report.assertions_evaluated_count == 0
    assert report.violations[0]["reason"] == "empty_commit_range"


def test_feature_has_proof_receipt_strict_requires_non_trivial_output_proof(
    tmp_path: Path,
) -> None:
    write_feature_proof_receipt_artifact(tmp_path, _receipt("abc123"))

    report = evaluate_feature_has_proof_receipt(
        repo_root=tmp_path,
        commit_shas=("abc123",),
        require_non_empty_range=True,
        require_proven_passed=True,
        require_non_trivial_output_proof=True,
    )

    assert report.ok is False
    assert report.assertions_evaluated_count == 4
    assert report.violations[0]["reason"] == "non_trivial_output_proof_failed"
    assert "no_real_tests" in report.violations[0]["detail"]
    assert "ref_unresolved:test:feature-proof" in report.violations[0]["detail"]


def test_feature_has_proof_receipt_strict_passes_with_resolved_output_proof(
    tmp_path: Path,
) -> None:
    test_path = tmp_path / "dev/scripts/devctl/tests/test_feature_proof.py"
    test_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.write_text("def test_real_output():\n    assert True\n", encoding="utf-8")
    evidence_path = tmp_path / "dev/reports/command-output/proof.txt"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text("1 passed\n", encoding="utf-8")
    test_ref = f"{test_path.relative_to(tmp_path)}::test_real_output"
    evidence_ref = str(evidence_path.relative_to(tmp_path))
    write_feature_proof_receipt_artifact(
        tmp_path,
        _receipt(
            "abc123",
            tests_run=(test_ref,),
            evidence_artifacts=(evidence_ref,),
            dogfood_invocation_evidence_ref=evidence_ref,
        ),
    )

    report = evaluate_feature_has_proof_receipt(
        repo_root=tmp_path,
        commit_shas=("abc123",),
        require_non_empty_range=True,
        require_proven_passed=True,
        require_non_trivial_output_proof=True,
    )

    assert report.ok is True
    assert report.assertions_evaluated_count == 4
    assert report.violation_count == 0
