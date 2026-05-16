from __future__ import annotations
# pyright: reportPrivateUsage=false

import json
from dataclasses import replace
from pathlib import Path
from typing import cast

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
from dev.scripts.devctl.runtime.remote_commit_pipeline_models import (
    CommitIntentState,
    PushAuthorizationRecord,
    RemoteCommitPipelineContract,
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
    assert "GovernanceReceipt" in feature_proof.review_fleet_roles_ran
    assert feature_proof.review_fleet_actor == "review-channel"
    assert "validation_bundle:runtime" in feature_proof.tests_run
    assert feature_proof.tests_passed_count == 1
    assert feature_proof.tests_failed_count == 0
    assert feature_proof.connectivity_guards_passed is True
    assert feature_proof.real_life_test_status == "proven_passed"
    assert feature_proof.not_tested_rationale is None
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
    assert parsed.real_life_test_status == "proven_passed"


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


def test_non_trivial_output_proof_validates_resolved_pytest_evidence(
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

    assert proof.ok is True
    assert proof.failure_reasons == ()


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
    )

    proof = validate_non_trivial_output_proof(receipt, repo_root=tmp_path)

    assert proof.ref_resolves is True
    assert proof.ok is True


def test_non_trivial_output_proof_allows_distinct_fpr_artifact_ref(
    tmp_path: Path,
) -> None:
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
    commit_result = persisted[-1].commit_result
    assert commit_result is not None
    assert result.ok is True
    assert receipt_paths == ["dev/reports/commit_receipts/abc123.json"]
    assert proof_paths == ["dev/reports/feature_lifecycle_proofs/abc123.json"]
    assert feature_proof_paths == ["dev/reports/feature_proof_receipts/abc123.json"]
    assert (tmp_path / receipt_paths[0]).exists()
    assert (tmp_path / proof_paths[0]).exists()
    assert (tmp_path / feature_proof_paths[0]).exists()
    assert receipt_paths[0] in commit_result.artifact_paths
    assert proof_paths[0] in commit_result.artifact_paths
    assert feature_proof_paths[0] in commit_result.artifact_paths


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
