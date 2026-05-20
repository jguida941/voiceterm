from __future__ import annotations
# pyright: reportPrivateUsage=false

import json
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest

from dev.scripts.devctl.commands.vcs.governed_executor_commit_phase import (
    CommitPipelineContext,
    _commit_success_result,
)
from dev.scripts.devctl.runtime.action_contracts import (
    ActionOutcome,
    ActionResult,
    ActionResultFields,
    build_action_result,
)
from dev.scripts.devctl.runtime.commit_receipt import (
    COMMIT_RECEIPT_CONTRACT_ID,
    COMMIT_RECORDED_STATE,
    CommitReceiptStateRequired,
    VALIDATION_PASSED_STATE,
    build_commit_receipt,
    build_feature_lifecycle_proof,
    build_feature_proof_receipt,
    commit_receipt_from_mapping,
    feature_lifecycle_proof_artifact_relpath,
    feature_proof_receipt_artifact_relpath,
    write_commit_receipt_artifact,
    write_feature_lifecycle_proof_artifact,
    write_feature_proof_receipt_artifact,
)
from dev.scripts.devctl.runtime.feature_proof_receipt import (
    FEATURE_PROOF_RECEIPT_ARTIFACT_ROOT,
    FeatureProofReceipt,
    feature_proof_receipt_from_mapping,
    validate_non_trivial_output_proof,
)
from dev.scripts.devctl.runtime.git_mutation_proof_receipt import (
    GIT_MUTATION_PROOF_RECEIPT_STORE_REL,
    GitMutationProofReceipt,
    append_git_mutation_proof_receipt,
    build_commit_git_mutation_proof_receipt,
    read_git_mutation_proof_receipts,
)
from dev.scripts.devctl.runtime.remote_commit_pipeline_models import (
    CommitIntentState,
    PushAuthorizationRecord,
    RemoteCommitPipelineContract,
)
from dev.scripts.devctl.runtime.role_review_lifecycle import (
    RoleReviewAssignmentLifecycle,
    RoleReviewReceipt,
    RoleReviewTimeout,
    role_review_assignment_lifecycle_from_mapping,
)
from dev.scripts.devctl.runtime.validation_contracts import (
    ValidationPlan,
    ValidationReceipt,
)


def test_commit_receipt_bundles_reviewer_ack_and_audit_chain() -> None:
    receipt = build_commit_receipt(
        _pipeline(),
        recorded_at_utc="2026-05-11T23:05:00Z",
        artifact_paths=("dev/reports/review_channel/projections/latest/commit_pipeline.json",),
    )

    assert receipt.contract_id == COMMIT_RECEIPT_CONTRACT_ID
    assert receipt.receipt_id == "commit_receipt:abc123"
    assert receipt.commit_sha == "abc123"
    assert receipt.tree_content_hash == "tree-1"
    assert receipt.plan_row_id == "MP377-COMMIT-RECEIPT-EVIDENCE-CHAIN-S1"
    assert receipt.reviewer_ack_packet_id == "rev_pkt_accept"
    assert receipt.approval_packet_id == "rev_pkt_request"
    assert receipt.audit_synthesis_ref == "validation_receipt:val-1"
    assert receipt.status == COMMIT_RECORDED_STATE
    assert receipt.pre_state == VALIDATION_PASSED_STATE
    assert receipt.post_state == COMMIT_RECORDED_STATE
    assert "commit:abc123" in receipt.evidence_refs
    assert "tree_content_hash:tree-1" in receipt.evidence_refs
    assert "packet:rev_pkt_accept" in receipt.evidence_refs
    assert "validation_receipt:val-1" in receipt.evidence_refs
    assert "guard_action:guard-1" in receipt.evidence_refs


def test_commit_receipt_round_trips_artifact(tmp_path: Path) -> None:
    relpath = write_commit_receipt_artifact(
        tmp_path,
        build_commit_receipt(_pipeline(), recorded_at_utc="2026-05-11T23:05:00Z"),
    )

    assert relpath == "dev/reports/commit_receipts/abc123.json"
    parsed = commit_receipt_from_mapping(json.loads((tmp_path / relpath).read_text()))

    assert parsed.commit_sha == "abc123"
    assert parsed.tree_content_hash == "tree-1"
    assert parsed.reviewer_ack_packet_id == "rev_pkt_accept"
    assert parsed.audit_synthesis_ref == "validation_receipt:val-1"
    assert parsed.pre_state == VALIDATION_PASSED_STATE
    assert parsed.post_state == COMMIT_RECORDED_STATE


def test_commit_git_mutation_proof_verifies_real_head_commit(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / "sample.txt").write_text("sample\n", encoding="utf-8")
    _git(tmp_path, "add", "sample.txt")
    _git(tmp_path, "commit", "-m", "sample")
    head_sha = _git(tmp_path, "rev-parse", "HEAD")

    receipt = build_commit_git_mutation_proof_receipt(
        repo_root=tmp_path,
        claim=GitMutationProofReceipt(
            mutation_kind="commit",
            action_id="vcs.commit.1",
            pipeline_id="pipe-1",
            plan_row_id="MP-TEST",
            expected_sha=head_sha,
            operation_returned_success=True,
        ),
    )
    relpath = append_git_mutation_proof_receipt(tmp_path, receipt)
    restored = read_git_mutation_proof_receipts(tmp_path)

    assert relpath == GIT_MUTATION_PROOF_RECEIPT_STORE_REL
    assert receipt.verified is True
    assert receipt.object_type == "commit"
    assert receipt.observed_local_sha == head_sha
    assert restored[-1].receipt_id == receipt.receipt_id


def test_commit_git_mutation_proof_accepts_reachable_receipt_head_when_allowed(
    tmp_path: Path,
) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / "sample.txt").write_text("sample\n", encoding="utf-8")
    _git(tmp_path, "add", "sample.txt")
    _git(tmp_path, "commit", "-m", "sample")
    content_sha = _git(tmp_path, "rev-parse", "HEAD")
    (tmp_path / "dev/audits").mkdir(parents=True)
    (tmp_path / "dev/audits/REVIEW_SNAPSHOT.md").write_text(
        "# Review Snapshot\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", "dev/audits/REVIEW_SNAPSHOT.md")
    _git(
        tmp_path,
        "commit",
        "-m",
        f"Refresh external review snapshot for {content_sha[:8]}",
    )
    receipt_head = _git(tmp_path, "rev-parse", "HEAD")

    strict_receipt = build_commit_git_mutation_proof_receipt(
        repo_root=tmp_path,
        claim=GitMutationProofReceipt(
            mutation_kind="commit",
            action_id="vcs.commit.1",
            pipeline_id="pipe-1",
            plan_row_id="MP-TEST",
            expected_sha=content_sha,
            operation_returned_success=True,
        ),
    )
    reachable_receipt = build_commit_git_mutation_proof_receipt(
        repo_root=tmp_path,
        claim=GitMutationProofReceipt(
            mutation_kind="commit",
            action_id="vcs.commit.1",
            pipeline_id="pipe-1",
            plan_row_id="MP-TEST",
            expected_sha=content_sha,
            operation_returned_success=True,
        ),
        allow_reachable_head=True,
    )

    assert strict_receipt.verified is False
    assert strict_receipt.failure_reason == "head_does_not_match_expected_sha"
    assert reachable_receipt.verified is True
    assert reachable_receipt.observed_local_sha == receipt_head
    assert f"reachable_head:{receipt_head}" in reachable_receipt.evidence_refs


def test_feature_lifecycle_proof_covers_commit_chain(tmp_path: Path) -> None:
    receipt = build_commit_receipt(_pipeline(), recorded_at_utc="2026-05-11T23:05:00Z")
    proof = build_feature_lifecycle_proof(_pipeline(), receipt)

    assert proof.contract_id == "FeatureLifecycleProof"
    assert proof.feature_id == "MP377-COMMIT-RECEIPT-EVIDENCE-CHAIN-S1"
    assert proof.commit_sha == "abc123"
    assert proof.completeness_score == 1.0
    assert proof.missing_receipt_kinds == ()
    assert {item.receipt_kind for item in proof.receipts} == {
        "validation",
        "commit",
        "review",
        "audit",
        "tree",
    }

    relpath = write_feature_lifecycle_proof_artifact(tmp_path, proof)
    assert relpath == feature_lifecycle_proof_artifact_relpath("abc123")
    parsed = json.loads((tmp_path / relpath).read_text())
    assert parsed["contract_id"] == "FeatureLifecycleProof"
    assert parsed["completeness_score"] == 1.0


def test_feature_proof_receipt_covers_operator_proof_chain(tmp_path: Path) -> None:
    pipeline = _pipeline()
    receipt = build_commit_receipt(pipeline, recorded_at_utc="2026-05-11T23:05:00Z")
    lifecycle_proof = build_feature_lifecycle_proof(pipeline, receipt)
    feature_proof = build_feature_proof_receipt(
        pipeline,
        receipt,
        lifecycle_proof=lifecycle_proof,
        evidence_artifacts=(
            "dev/reports/commit_receipts/abc123.json",
            "dev/reports/feature_lifecycle_proofs/abc123.json",
        ),
    )

    assert feature_proof.contract_id == "FeatureProofReceipt"
    assert feature_proof.schema_version == 1
    assert feature_proof.feature_id == "MP377-COMMIT-RECEIPT-EVIDENCE-CHAIN-S1"
    assert feature_proof.commit_sha == "abc123"
    assert feature_proof.implementer_actor == "devctl"
    assert "review_packet_acknowledged" in feature_proof.review_fleet_roles_ran
    assert feature_proof.review_fleet_actor == "review-channel"
    assert "validation_bundle:runtime" in feature_proof.tests_run
    assert feature_proof.tests_passed_count == 1
    assert feature_proof.tests_failed_count == 0
    assert feature_proof.connectivity_guards_passed is True
    assert feature_proof.real_life_test_status == "not_tested_with_rationale"
    assert feature_proof.not_tested_rationale is not None
    assert "no concrete pytest node" in feature_proof.not_tested_rationale
    assert (
        feature_proof.dogfood_invocation_evidence_ref
        == "dev/reports/feature_lifecycle_proofs/abc123.json"
    )

    relpath = write_feature_proof_receipt_artifact(tmp_path, feature_proof)
    assert relpath == feature_proof_receipt_artifact_relpath("abc123")
    parsed = feature_proof_receipt_from_mapping(
        json.loads((tmp_path / relpath).read_text())
    )
    assert parsed.commit_sha == "abc123"
    assert parsed.real_life_test_status == "not_tested_with_rationale"


def test_feature_proof_receipt_includes_selected_pytest_node_ids(
    tmp_path: Path,
) -> None:
    test_relpath = "dev/scripts/devctl/tests/runtime/test_selected.py"
    test_path = tmp_path / test_relpath
    test_path.parent.mkdir(parents=True)
    test_path.write_text(
        "\n".join(
            (
                "def test_selected_path_is_recorded():",
                "    assert True",
                "",
                "class TestSelectedClass:",
                "    def test_method_is_recorded(self):",
                "        assert True",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    _write_json(tmp_path / "dev/reports/commit_receipts/abc123.json")
    _write_json(tmp_path / "dev/reports/feature_lifecycle_proofs/abc123.json")
    pipeline = replace(
        _pipeline(),
        intent=CommitIntentState(
            validation_plan=ValidationPlan(
                plan_id="MP377-COMMIT-RECEIPT-EVIDENCE-CHAIN-S1",
                bundle_id="runtime",
                staged_tree_hash="tree-1",
                selected_paths=(test_relpath,),
            )
        ),
    )
    receipt = build_commit_receipt(pipeline, recorded_at_utc="2026-05-11T23:05:00Z")
    lifecycle_proof = build_feature_lifecycle_proof(pipeline, receipt)

    feature_proof = build_feature_proof_receipt(
        pipeline,
        receipt,
        lifecycle_proof=lifecycle_proof,
        evidence_artifacts=(
            "dev/reports/commit_receipts/abc123.json",
            "dev/reports/feature_lifecycle_proofs/abc123.json",
        ),
        repo_root=tmp_path,
    )

    assert f"{test_relpath}::test_selected_path_is_recorded" in feature_proof.tests_run
    assert (
        f"{test_relpath}::TestSelectedClass::test_method_is_recorded"
        in feature_proof.tests_run
    )
    assert feature_proof.real_life_test_status == "proven_passed"
    assert feature_proof.not_tested_rationale is None
    proof = validate_non_trivial_output_proof(feature_proof, repo_root=tmp_path)
    assert proof.has_real_tests is True


def test_commit_receipt_consumes_role_review_lifecycle_evidence() -> None:
    lifecycle = _role_review_lifecycle()
    pipeline = replace(_pipeline(), role_review_lifecycles=(lifecycle,))
    receipt = build_commit_receipt(
        pipeline,
        recorded_at_utc="2026-05-11T23:05:00Z",
    )
    lifecycle_proof = build_feature_lifecycle_proof(pipeline, receipt)
    feature_proof = build_feature_proof_receipt(
        pipeline,
        receipt,
        lifecycle_proof=lifecycle_proof,
    )

    role_review_ref = "role_review_receipt:rev_pkt_4151:GovernanceReceipt:claude"
    assert receipt.role_review_roles == ("GovernanceReceipt",)
    assert receipt.role_review_receipt_refs == (role_review_ref,)
    assert role_review_ref in receipt.evidence_refs
    assert {item.receipt_kind for item in lifecycle_proof.receipts} >= {
        "role_review"
    }
    assert "GovernanceReceipt" in feature_proof.review_fleet_roles_ran
    assert feature_proof.role_review_receipt_refs == (role_review_ref,)
    assert feature_proof.role_review_timeout_refs == ()


def test_feature_proof_receipt_requires_not_tested_rationale() -> None:
    with pytest.raises(ValueError, match="not_tested_rationale is required"):
        FeatureProofReceipt(
            feature_id="MP-TEST",
            commit_sha="abc123",
            implementer_actor="codex",
            review_fleet_roles_ran=(),
            review_fleet_actor="claude",
            tests_run=(),
            tests_passed_count=0,
            tests_failed_count=0,
            connectivity_guards_ran=(),
            connectivity_guards_passed=False,
            dogfood_invocation_evidence_ref="",
            real_life_test_status="not_tested_with_rationale",
            not_tested_rationale=None,
            bypass_audit_trail_refs=(),
            proven_at_utc="2026-05-15T17:00:00Z",
            evidence_artifacts=(),
        )


def test_role_review_receipt_round_trips_p208_terminal_fields() -> None:
    receipt = RoleReviewReceipt(
        role="ArchitectureReview",
        packet_id="rev_pkt_4151",
        reviewer_actor="claude",
        verdict="approved",
        proof_evidence_refs=("packet:rev_pkt_4151", "test:role-review-node"),
        reviewed_at_utc="2026-05-16T13:00:00Z",
    )

    payload = receipt.to_dict()

    assert payload["contract_id"] == "RoleReviewReceipt"
    assert payload["schema_version"] == 1
    assert payload["role"] == "ArchitectureReview"
    assert payload["packet_id"] == "rev_pkt_4151"
    assert payload["reviewer_actor"] == "claude"
    assert payload["verdict"] == "approved"
    assert payload["proof_evidence_refs"] == [
        "packet:rev_pkt_4151",
        "test:role-review-node",
    ]


def test_role_review_assignment_lifecycle_binds_receipt_to_role_and_packet() -> None:
    receipt = RoleReviewReceipt(
        role="GovernanceReceipt",
        packet_id="rev_pkt_4151",
        reviewer_actor="claude",
        verdict="approved",
        proof_evidence_refs=("packet:rev_pkt_4151",),
        reviewed_at_utc="2026-05-16T13:05:00Z",
    )
    lifecycle = RoleReviewAssignmentLifecycle(
        assignment_id="role-review:rev_pkt_4151:GovernanceReceipt",
        packet_id="rev_pkt_4151",
        assigned_role="GovernanceReceipt",
        assigned_actor="claude",
        assigned_at_utc="2026-05-16T13:00:00Z",
        due_at_utc="2026-05-16T13:10:00Z",
        status="reviewed",
        receipt=receipt,
        timeout=None,
        parent_bypass_lifecycle_ref="gel:bypass:bypass:grant-20260516T054109743503",
        governed_exception_refs=("GovernedExceptionLifecycle:P208",),
        evidence_refs=("packet:rev_pkt_4151",),
    )
    restored = role_review_assignment_lifecycle_from_mapping(lifecycle.to_dict())

    assert restored.contract_id == "RoleReviewAssignmentLifecycle"
    assert restored.receipt is not None
    assert restored.receipt.role == "GovernanceReceipt"
    assert restored.receipt.packet_id == "rev_pkt_4151"
    assert (
        restored.parent_bypass_lifecycle_ref
        == "gel:bypass:bypass:grant-20260516T054109743503"
    )
    assert restored.governed_exception_refs == ("GovernedExceptionLifecycle:P208",)


def test_role_review_assignment_requires_terminal_evidence() -> None:
    with pytest.raises(ValueError, match="reviewed assignments require"):
        RoleReviewAssignmentLifecycle(
            assignment_id="role-review:rev_pkt_4151:DogfoodTest",
            packet_id="rev_pkt_4151",
            assigned_role="DogfoodTest",
            assigned_actor="claude",
            assigned_at_utc="2026-05-16T13:00:00Z",
            due_at_utc="2026-05-16T13:10:00Z",
            status="reviewed",
            receipt=None,
            timeout=None,
            parent_bypass_lifecycle_ref=None,
            governed_exception_refs=(),
            evidence_refs=(),
        )


def test_role_review_assignment_accepts_typed_timeout_fallback() -> None:
    timeout = RoleReviewTimeout(
        role="DogfoodTest",
        packet_id="rev_pkt_4151",
        timed_out_at_utc="2026-05-16T13:11:00Z",
        fallback_authority="gel:bypass:bypass:grant-20260516T054109743503",
    )
    lifecycle = RoleReviewAssignmentLifecycle(
        assignment_id="role-review:rev_pkt_4151:DogfoodTest",
        packet_id="rev_pkt_4151",
        assigned_role="DogfoodTest",
        assigned_actor="claude",
        assigned_at_utc="2026-05-16T13:00:00Z",
        due_at_utc="2026-05-16T13:10:00Z",
        status="timed_out",
        receipt=None,
        timeout=timeout,
        parent_bypass_lifecycle_ref="gel:bypass:bypass:grant-20260516T054109743503",
        governed_exception_refs=("GovernedExceptionLifecycle:P208",),
        evidence_refs=("packet:rev_pkt_4151", "timeout:DogfoodTest"),
    )

    assert lifecycle.timeout is timeout
    assert lifecycle.to_dict()["timeout"] == timeout.to_dict()


def test_non_trivial_output_proof_validates_resolved_pytest_evidence(
    tmp_path: Path,
) -> None:
    evidence = tmp_path / "proof-output.txt"
    evidence.write_text("expected output\n", encoding="utf-8")
    _write_sample_test(tmp_path)
    receipt = FeatureProofReceipt(
        feature_id="MP-TEST",
        commit_sha="abc123",
        implementer_actor="codex",
        review_fleet_roles_ran=("DogfoodTest",),
        review_fleet_actor="claude",
        tests_run=("dev/scripts/devctl/tests/test_sample.py::test_real",),
        tests_passed_count=1,
        tests_failed_count=0,
        connectivity_guards_ran=("check_non_trivial_output_proof",),
        connectivity_guards_passed=True,
        dogfood_invocation_evidence_ref="proof-output.txt",
        real_life_test_status="proven_passed",
        not_tested_rationale=None,
        bypass_audit_trail_refs=(),
        proven_at_utc="2026-05-16T04:00:00Z",
        evidence_artifacts=("proof-output.txt",),
        role_review_receipt_refs=(
            "role_review_receipt:rev_pkt_4151:DogfoodTest:claude",
        ),
    )

    proof = validate_non_trivial_output_proof(receipt, repo_root=tmp_path)

    assert proof.ok is True
    assert proof.failure_reasons == ()


def test_non_trivial_output_proof_rejects_unresolved_pytest_node(
    tmp_path: Path,
) -> None:
    evidence = tmp_path / "proof-output.txt"
    evidence.write_text("expected output\n", encoding="utf-8")
    _write_sample_test(tmp_path)
    receipt = FeatureProofReceipt(
        feature_id="MP-TEST",
        commit_sha="abc123",
        implementer_actor="codex",
        review_fleet_roles_ran=("DogfoodTest",),
        review_fleet_actor="claude",
        tests_run=("dev/scripts/devctl/tests/test_sample.py::test_missing",),
        tests_passed_count=1,
        tests_failed_count=0,
        connectivity_guards_ran=("check_non_trivial_output_proof",),
        connectivity_guards_passed=True,
        dogfood_invocation_evidence_ref="proof-output.txt",
        real_life_test_status="proven_passed",
        not_tested_rationale=None,
        bypass_audit_trail_refs=(),
        proven_at_utc="2026-05-16T04:00:00Z",
        evidence_artifacts=("proof-output.txt",),
        role_review_receipt_refs=(
            "role_review_receipt:rev_pkt_4151:DogfoodTest:claude",
        ),
    )

    proof = validate_non_trivial_output_proof(receipt, repo_root=tmp_path)

    assert proof.has_real_tests is False
    assert "no_real_tests" in proof.failure_reasons
    assert proof.ok is False


def test_non_trivial_output_proof_resolves_pytest_node_in_test_command(
    tmp_path: Path,
) -> None:
    evidence = tmp_path / "proof-output.txt"
    evidence.write_text("expected output\n", encoding="utf-8")
    _write_sample_test(tmp_path)
    node = "dev/scripts/devctl/tests/test_sample.py::test_real"
    receipt = FeatureProofReceipt(
        feature_id="MP-TEST",
        commit_sha="abc123",
        implementer_actor="codex",
        review_fleet_roles_ran=("DogfoodTest",),
        review_fleet_actor="claude",
        tests_run=(
            f"python3 dev/scripts/devctl.py test-python --suite devctl --path {node}",
        ),
        tests_passed_count=1,
        tests_failed_count=0,
        connectivity_guards_ran=("check_non_trivial_output_proof",),
        connectivity_guards_passed=True,
        dogfood_invocation_evidence_ref="proof-output.txt",
        real_life_test_status="proven_passed",
        not_tested_rationale=None,
        bypass_audit_trail_refs=(),
        proven_at_utc="2026-05-16T04:00:00Z",
        evidence_artifacts=("proof-output.txt",),
        role_review_receipt_refs=(
            "role_review_receipt:rev_pkt_4151:DogfoodTest:claude",
        ),
    )

    proof = validate_non_trivial_output_proof(receipt, repo_root=tmp_path)

    assert proof.has_real_tests is True
    assert proof.ok is True


def test_non_trivial_output_proof_requires_terminal_role_review_ref(
    tmp_path: Path,
) -> None:
    evidence = tmp_path / "proof-output.txt"
    evidence.write_text("expected output\n", encoding="utf-8")
    receipt = FeatureProofReceipt(
        feature_id="MP-TEST",
        commit_sha="abc123",
        implementer_actor="codex",
        review_fleet_roles_ran=("DogfoodTest",),
        review_fleet_actor="claude",
        tests_run=("dev/scripts/devctl/tests/test_sample.py::test_real",),
        tests_passed_count=1,
        tests_failed_count=0,
        connectivity_guards_ran=("check_non_trivial_output_proof",),
        connectivity_guards_passed=True,
        dogfood_invocation_evidence_ref="proof-output.txt",
        real_life_test_status="proven_passed",
        not_tested_rationale=None,
        bypass_audit_trail_refs=(),
        proven_at_utc="2026-05-16T04:00:00Z",
        evidence_artifacts=("proof-output.txt",),
    )

    proof = validate_non_trivial_output_proof(receipt, repo_root=tmp_path)

    assert proof.role_review_terminal_refs_present is False
    assert (
        "missing_role_review_terminal_ref:DogfoodTest" in proof.failure_reasons
    )
    assert proof.ok is False


def test_non_trivial_output_proof_flags_circular_shell_only_evidence(
    tmp_path: Path,
) -> None:
    receipt = FeatureProofReceipt(
        feature_id="MP-TEST",
        commit_sha="abc123",
        implementer_actor="codex",
        review_fleet_roles_ran=("DogfoodTest",),
        review_fleet_actor="claude",
        tests_run=("python3 dev/scripts/checks/check_feature_has_proof_receipt.py",),
        tests_passed_count=1,
        tests_failed_count=0,
        connectivity_guards_ran=("check_non_trivial_output_proof",),
        connectivity_guards_passed=True,
        dogfood_invocation_evidence_ref=FEATURE_PROOF_RECEIPT_ARTIFACT_ROOT,
        real_life_test_status="proven_passed",
        not_tested_rationale=None,
        bypass_audit_trail_refs=(),
        proven_at_utc="2026-05-16T04:00:00Z",
        evidence_artifacts=(FEATURE_PROOF_RECEIPT_ARTIFACT_ROOT,),
    )

    proof = validate_non_trivial_output_proof(receipt, repo_root=tmp_path)

    assert proof.ok is False
    assert "no_real_tests" in proof.failure_reasons
    assert any(reason.startswith("circular_ref:") for reason in proof.failure_reasons)


def test_non_trivial_output_proof_resolves_pytest_node_ref(
    tmp_path: Path,
) -> None:
    test_path = tmp_path / "dev/scripts/devctl/tests/test_sample.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text("def test_real():\n    assert True\n", encoding="utf-8")
    receipt = FeatureProofReceipt(
        feature_id="MP-TEST",
        commit_sha="abc123",
        implementer_actor="codex",
        review_fleet_roles_ran=("DogfoodTest",),
        review_fleet_actor="claude",
        tests_run=("dev/scripts/devctl/tests/test_sample.py::test_real",),
        tests_passed_count=1,
        tests_failed_count=0,
        connectivity_guards_ran=("check_non_trivial_output_proof",),
        connectivity_guards_passed=True,
        dogfood_invocation_evidence_ref=(
            "dev/scripts/devctl/tests/test_sample.py::test_real"
        ),
        real_life_test_status="proven_passed",
        not_tested_rationale=None,
        bypass_audit_trail_refs=(),
        proven_at_utc="2026-05-16T04:00:00Z",
        evidence_artifacts=("dev/scripts/devctl/tests/test_sample.py",),
        role_review_receipt_refs=(
            "role_review_receipt:rev_pkt_4151:DogfoodTest:claude",
        ),
    )

    proof = validate_non_trivial_output_proof(receipt, repo_root=tmp_path)

    assert proof.ref_resolves is True
    assert proof.ok is True


def test_non_trivial_output_proof_allows_distinct_fpr_artifact_ref(
    tmp_path: Path,
) -> None:
    _write_sample_test(tmp_path)
    other_ref = (
        tmp_path
        / FEATURE_PROOF_RECEIPT_ARTIFACT_ROOT
        / "other-commit.json"
    )
    other_ref.parent.mkdir(parents=True)
    other_ref.write_text("{}\n", encoding="utf-8")
    receipt = FeatureProofReceipt(
        feature_id="MP-TEST",
        commit_sha="abc123",
        implementer_actor="codex",
        review_fleet_roles_ran=("DogfoodTest",),
        review_fleet_actor="claude",
        tests_run=("dev/scripts/devctl/tests/test_sample.py::test_real",),
        tests_passed_count=1,
        tests_failed_count=0,
        connectivity_guards_ran=("check_non_trivial_output_proof",),
        connectivity_guards_passed=True,
        dogfood_invocation_evidence_ref=(
            f"{FEATURE_PROOF_RECEIPT_ARTIFACT_ROOT}/other-commit.json"
        ),
        real_life_test_status="proven_passed",
        not_tested_rationale=None,
        bypass_audit_trail_refs=(),
        proven_at_utc="2026-05-16T04:00:00Z",
        evidence_artifacts=(
            f"{FEATURE_PROOF_RECEIPT_ARTIFACT_ROOT}/other-commit.json",
        ),
        role_review_receipt_refs=(
            "role_review_receipt:rev_pkt_4151:DogfoodTest:claude",
        ),
    )

    proof = validate_non_trivial_output_proof(receipt, repo_root=tmp_path)

    assert proof.not_circular is True
    assert proof.ok is True


def test_build_feature_proof_receipt_rejects_unresolved_new_refs(tmp_path: Path) -> None:
    pipeline = _pipeline()
    receipt = build_commit_receipt(pipeline, recorded_at_utc="2026-05-11T23:05:00Z")

    with pytest.raises(ValueError, match="non_trivial_output_proof_ref_failure"):
        build_feature_proof_receipt(
            pipeline,
            receipt,
            evidence_artifacts=("missing-proof-output.txt",),
            repo_root=tmp_path,
        )


def test_commit_receipt_rejects_commit_after_failed_validation() -> None:
    pipeline = _pipeline()
    assert pipeline.validation_receipt is not None
    failed = replace(
        pipeline,
        validation_receipt=replace(
            pipeline.validation_receipt,
            status=ActionOutcome.FAIL,
            post_state="validation_failed",
        ),
    )

    with pytest.raises(CommitReceiptStateRequired):
        build_commit_receipt(failed)


def test_governed_commit_success_emits_commit_receipt_artifact(tmp_path: Path) -> None:
    persisted: list[RemoteCommitPipelineContract] = []
    completed = _pipeline()
    pipeline_artifact = (
        tmp_path / "dev/reports/review_channel/projections/latest/commit_pipeline.json"
    )
    pipeline_artifact.parent.mkdir(parents=True)
    pipeline_artifact.write_text("{}", encoding="utf-8")
    context = CommitPipelineContext(
        repo_root=tmp_path,
        review_channel_path=None,
        load_pipeline=lambda: completed,
        persist_pipeline=lambda pipeline: [],
        persist_pipeline_contract_only=lambda pipeline: _persist(persisted, pipeline),
        event_packets_loader=lambda: (),
        pipeline_artifact_relpath=(
            "dev/reports/review_channel/projections/latest/commit_pipeline.json"
        ),
        result_builder=_result,
    )

    with patch(
        "dev.scripts.devctl.commands.vcs.governed_executor_commit_proof."
        "build_commit_git_mutation_proof_receipt",
        return_value=GitMutationProofReceipt(
            receipt_id="git_mutation_proof:commit:abc123",
            mutation_kind="commit",
            expected_sha="abc123",
            observed_local_sha="abc123",
            object_type="commit",
            verified=True,
            status="verified",
        ),
    ):
        result = _commit_success_result(
            action_id="vcs.commit.1",
            context=context,
            completed=completed,
        )

    receipt_paths = [
        path for path in result.artifact_paths if path.startswith("dev/reports/commit_receipts/")
    ]
    proof_paths = [
        path
        for path in result.artifact_paths
        if path.startswith("dev/reports/feature_lifecycle_proofs/")
    ]
    feature_proof_paths = [
        path
        for path in result.artifact_paths
        if path.startswith("dev/reports/feature_proof_receipts/")
    ]
    git_mutation_proof_paths = [
        path
        for path in result.artifact_paths
        if path == GIT_MUTATION_PROOF_RECEIPT_STORE_REL
    ]
    commit_result = persisted[-1].commit_result
    assert commit_result is not None
    assert result.ok is True
    assert receipt_paths == ["dev/reports/commit_receipts/abc123.json"]
    assert proof_paths == ["dev/reports/feature_lifecycle_proofs/abc123.json"]
    assert feature_proof_paths == ["dev/reports/feature_proof_receipts/abc123.json"]
    assert git_mutation_proof_paths == [GIT_MUTATION_PROOF_RECEIPT_STORE_REL]
    assert (tmp_path / receipt_paths[0]).exists()
    assert (tmp_path / proof_paths[0]).exists()
    assert (tmp_path / feature_proof_paths[0]).exists()
    assert (tmp_path / GIT_MUTATION_PROOF_RECEIPT_STORE_REL).exists()
    assert receipt_paths[0] in commit_result.artifact_paths
    assert proof_paths[0] in commit_result.artifact_paths
    assert feature_proof_paths[0] in commit_result.artifact_paths


def test_governed_commit_success_emits_content_receipts_for_managed_receipt_head(
    tmp_path: Path,
) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")
    _git(tmp_path, "commit", "-m", "content")
    content_sha = _git(tmp_path, "rev-parse", "HEAD")
    (tmp_path / "dev/audits").mkdir(parents=True)
    (tmp_path / "dev/audits/REVIEW_SNAPSHOT.md").write_text(
        "# Review Snapshot\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", "dev/audits/REVIEW_SNAPSHOT.md")
    _git(
        tmp_path,
        "commit",
        "-m",
        f"Refresh external review snapshot for {content_sha[:8]}",
    )
    receipt_sha = _git(tmp_path, "rev-parse", "HEAD")
    completed = replace(
        _pipeline(),
        commit_sha=receipt_sha,
        push_authorization=replace(
            _pipeline().push_authorization,
            authorized_head_sha=receipt_sha,
        ),
    )
    pipeline_artifact = (
        tmp_path / "dev/reports/review_channel/projections/latest/commit_pipeline.json"
    )
    pipeline_artifact.parent.mkdir(parents=True)
    pipeline_artifact.write_text("{}", encoding="utf-8")
    persisted: list[RemoteCommitPipelineContract] = []
    context = CommitPipelineContext(
        repo_root=tmp_path,
        review_channel_path=None,
        load_pipeline=lambda: completed,
        persist_pipeline=lambda pipeline: [],
        persist_pipeline_contract_only=lambda pipeline: _persist(persisted, pipeline),
        event_packets_loader=lambda: (),
        pipeline_artifact_relpath=(
            "dev/reports/review_channel/projections/latest/commit_pipeline.json"
        ),
        result_builder=_result,
    )

    result = _commit_success_result(
        action_id="vcs.commit.1",
        context=context,
        completed=completed,
    )

    assert result.ok is True
    assert f"dev/reports/commit_receipts/{content_sha}.json" in result.artifact_paths
    assert f"dev/reports/commit_receipts/{receipt_sha}.json" in result.artifact_paths
    assert (
        f"dev/reports/feature_proof_receipts/{content_sha}.json"
        in result.artifact_paths
    )
    assert (
        f"dev/reports/feature_proof_receipts/{receipt_sha}.json"
        in result.artifact_paths
    )
    receipts = read_git_mutation_proof_receipts(tmp_path)
    assert any(
        receipt.expected_sha == content_sha
        and receipt.observed_local_sha == receipt_sha
        and receipt.verified
        for receipt in receipts
    )
    assert any(
        receipt.expected_sha == receipt_sha and receipt.verified
        for receipt in receipts
    )


def test_governed_commit_success_fails_typed_when_mutation_proof_store_fails(
    tmp_path: Path,
) -> None:
    persisted: list[RemoteCommitPipelineContract] = []
    completed = _pipeline()
    context = CommitPipelineContext(
        repo_root=tmp_path,
        review_channel_path=None,
        load_pipeline=lambda: completed,
        persist_pipeline=lambda pipeline: [],
        persist_pipeline_contract_only=lambda pipeline: _persist(persisted, pipeline),
        event_packets_loader=lambda: (),
        pipeline_artifact_relpath=(
            "dev/reports/review_channel/projections/latest/commit_pipeline.json"
        ),
        result_builder=_result,
    )

    with (
        patch(
            "dev.scripts.devctl.commands.vcs.governed_executor_commit_proof."
            "build_commit_git_mutation_proof_receipt",
            return_value=GitMutationProofReceipt(
                receipt_id="git_mutation_proof:commit:abc123",
                mutation_kind="commit",
                expected_sha="abc123",
                observed_local_sha="abc123",
                object_type="commit",
                verified=True,
                status="verified",
            ),
        ),
        patch(
            "dev.scripts.devctl.commands.vcs.governed_executor_commit_proof."
            "append_git_mutation_proof_receipt",
            side_effect=OSError("store locked"),
        ),
    ):
        result = _commit_success_result(
            action_id="vcs.commit.1",
            context=context,
            completed=completed,
        )

    assert result.ok is False
    assert result.reason == "commit_proof_write_failed"
    assert any(
        warning.startswith("git_mutation_proof_write_failed:")
        for warning in result.warnings
    )
    assert persisted[-1].state == "push_blocked"
    assert persisted[-1].blocked_reason == "commit_proof_write_failed"


def _pipeline() -> RemoteCommitPipelineContract:
    return RemoteCommitPipelineContract(
        pipeline_id="pipe-1",
        state="commit_recorded",
        intent=CommitIntentState(
            validation_plan=ValidationPlan(
                plan_id="MP377-COMMIT-RECEIPT-EVIDENCE-CHAIN-S1",
                bundle_id="runtime",
                staged_tree_hash="tree-1",
            )
        ),
        guard_action_id="guard-1",
        validation_receipt=ValidationReceipt(
            receipt_id="val-1",
            plan_id="MP377-COMMIT-RECEIPT-EVIDENCE-CHAIN-S1",
            bundle_id="runtime",
            status="pass",
            post_state=VALIDATION_PASSED_STATE,
        ),
        approval_packet_id="rev_pkt_request",
        decision_packet_id="rev_pkt_accept",
        approval_state="approved",
        commit_action_id="vcs.commit.1",
        commit_result=_result(
            action_id="vcs.commit.1",
            ok=True,
            status=ActionOutcome.PASS,
            reason="commit_recorded",
        ),
        commit_sha="abc123",
        push_authorization=PushAuthorizationRecord(
            authorization_id="push-auth-1",
            pipeline_id="pipe-1",
            generation_id="gen-1",
            authorized_head_sha="abc123",
            request_packet_id="rev_pkt_request",
            decision_packet_id="rev_pkt_accept",
            guard_action_id="guard-1",
        ),
        generation_id="gen-1",
    )


def _write_json(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}\n", encoding="utf-8")


def _write_sample_test(repo_root: Path) -> None:
    test_path = repo_root / "dev/scripts/devctl/tests/test_sample.py"
    test_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.write_text("def test_real():\n    assert True\n", encoding="utf-8")


def _init_git_repo(repo_root: Path) -> None:
    _git(repo_root, "init")
    _git(repo_root, "config", "user.email", "test@example.com")
    _git(repo_root, "config", "user.name", "Test User")


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return result.stdout.strip()


def _role_review_lifecycle() -> RoleReviewAssignmentLifecycle:
    receipt = RoleReviewReceipt(
        role="GovernanceReceipt",
        packet_id="rev_pkt_4151",
        reviewer_actor="claude",
        verdict="approved",
        proof_evidence_refs=("packet:rev_pkt_4151", "pytest::role-review"),
        reviewed_at_utc="2026-05-16T13:05:00Z",
    )
    return RoleReviewAssignmentLifecycle(
        assignment_id="role-review:rev_pkt_4151:GovernanceReceipt",
        packet_id="rev_pkt_4151",
        assigned_role="GovernanceReceipt",
        assigned_actor="claude",
        assigned_at_utc="2026-05-16T13:00:00Z",
        due_at_utc="2026-05-16T13:10:00Z",
        status="reviewed",
        receipt=receipt,
        timeout=None,
        parent_bypass_lifecycle_ref="gel:bypass:bypass:grant-20260516T054109743503",
        governed_exception_refs=("governed_exception:P208",),
        evidence_refs=("packet:rev_pkt_4151",),
    )


def _persist(
    persisted: list[RemoteCommitPipelineContract],
    pipeline: RemoteCommitPipelineContract,
) -> list[str]:
    persisted.append(pipeline)
    return []


def _result(**kwargs: object) -> ActionResult:
    warnings_value = kwargs.get("warnings")
    artifact_paths_value = kwargs.get("artifact_paths")
    return build_action_result(
        ActionResultFields(
            action_id=str(kwargs["action_id"]),
            ok=bool(kwargs["ok"]),
            status=str(kwargs.get("status") or ActionOutcome.UNKNOWN),
            reason=str(kwargs.get("reason") or ""),
            operator_guidance=str(kwargs.get("operator_guidance") or ""),
            warnings=_string_tuple(warnings_value),
            artifact_paths=_string_tuple(artifact_paths_value),
        )
    )


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    items = cast(list[object] | tuple[object, ...], value)
    return tuple(str(item) for item in items)
