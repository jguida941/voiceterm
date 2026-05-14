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
    commit_receipt_from_mapping,
    write_commit_receipt_artifact,
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
    commit_result = persisted[-1].commit_result
    assert commit_result is not None
    assert result.ok is True
    assert receipt_paths == ["dev/reports/commit_receipts/abc123.json"]
    assert (tmp_path / receipt_paths[0]).exists()
    assert receipt_paths[0] in commit_result.artifact_paths


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
