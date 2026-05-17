"""Tests for checkpoint repair lifecycle promotion."""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

from dev.scripts.devctl.runtime.action_contracts import ActionOutcome, ActionResult
from dev.scripts.devctl.runtime.checkpoint_repair_authority import (
    GOVERNED_CHECKPOINT_COMMIT,
    GUARD_BUNDLE_FAILED,
    REPAIR_VERIFIED,
    build_checkpoint_repair_authority,
    checkpoint_repair_authority_from_pipeline,
)
from dev.scripts.devctl.runtime.remote_commit_pipeline_models import (
    CommitIntentState,
    RemoteCommitPipelineContract,
    remote_commit_pipeline_contract_from_mapping,
)
from dev.scripts.devctl.runtime.startup_repair import build_startup_repair_result
from dev.scripts.devctl.runtime.startup_repair_models import (
    StartupRepairRuntimeInputs,
)
from dev.scripts.devctl.runtime.validation_contracts import ValidationReceipt


def _action_result(*, ok: bool, status: str, reason: str = "") -> ActionResult:
    return ActionResult(
        schema_version=1,
        contract_id="ActionResult",
        action_id="quality.guard_bundle",
        ok=ok,
        status=status,
        reason=reason,
    )


def _failed_pipeline() -> RemoteCommitPipelineContract:
    return RemoteCommitPipelineContract(
        pipeline_id="pipeline-1",
        generation_id="gen-1",
        state="guards_failed",
        blocked_reason=GUARD_BUNDLE_FAILED,
        intent=CommitIntentState(
            staged_tree_hash="tree-1",
            staged_path_count=1,
            staged_paths=("dev/runtime.py",),
        ),
        guard_result=_action_result(
            ok=False,
            status=ActionOutcome.FAIL,
            reason=GUARD_BUNDLE_FAILED,
        ),
    )


def _repaired_pipeline(previous: RemoteCommitPipelineContract) -> RemoteCommitPipelineContract:
    return replace(
        previous,
        state="guards_passed",
        blocked_reason="",
        guard_result=_action_result(ok=True, status=ActionOutcome.PASS),
        validation_receipt=ValidationReceipt(
            receipt_id="validation-1",
            plan_id="plan-1",
            bundle_id="quick",
            staged_tree_hash=previous.intent.staged_tree_hash,
            action_id="quality.guard_bundle",
            status=ActionOutcome.PASS,
            checkpoint_sufficient=True,
        ),
    )


def test_checkpoint_repair_authority_promotes_matching_guard_receipt() -> None:
    authority = build_checkpoint_repair_authority(
        previous_pipeline=_failed_pipeline(),
        repaired_pipeline=_repaired_pipeline(_failed_pipeline()),
    )

    assert authority is not None
    assert authority.original_block_reason == GUARD_BUNDLE_FAILED
    assert authority.result == REPAIR_VERIFIED
    assert authority.next_authorized_action == GOVERNED_CHECKPOINT_COMMIT
    assert authority.validation_receipt_id == "validation-1"
    assert authority.staged_tree_hash == "tree-1"
    assert authority.selected_paths == ("dev/runtime.py",)
    assert "git.commit" in authority.blocked_raw_actions


def test_checkpoint_repair_authority_blocks_stale_validation_receipt() -> None:
    previous = _failed_pipeline()
    stale = replace(
        _repaired_pipeline(previous),
        validation_receipt=replace(
            _repaired_pipeline(previous).validation_receipt,
            staged_tree_hash="tree-2",
        ),
    )

    assert (
        build_checkpoint_repair_authority(
            previous_pipeline=previous,
            repaired_pipeline=stale,
        )
        is None
    )


def test_checkpoint_repair_authority_reads_first_class_pipeline_field() -> None:
    authority = build_checkpoint_repair_authority(
        previous_pipeline=_failed_pipeline(),
        repaired_pipeline=_repaired_pipeline(_failed_pipeline()),
    )
    assert authority is not None
    pipeline = RemoteCommitPipelineContract(
        pipeline_id="pipeline-1",
        checkpoint_repair_authority=authority.to_dict(),
        push_failure_transition={"contract_id": "OtherTransition"},
    )

    restored = checkpoint_repair_authority_from_pipeline(pipeline)

    assert restored is not None
    assert restored.pipeline_id == authority.pipeline_id
    assert restored.validation_receipt_id == authority.validation_receipt_id


def test_checkpoint_repair_authority_keeps_legacy_transition_fallback() -> None:
    authority = build_checkpoint_repair_authority(
        previous_pipeline=_failed_pipeline(),
        repaired_pipeline=_repaired_pipeline(_failed_pipeline()),
    )
    assert authority is not None
    pipeline = RemoteCommitPipelineContract(
        pipeline_id="pipeline-1",
        push_failure_transition=authority.to_dict(),
    )

    restored = checkpoint_repair_authority_from_pipeline(pipeline)

    assert restored is not None
    assert restored.pipeline_id == authority.pipeline_id


def test_remote_commit_pipeline_roundtrips_checkpoint_repair_authority_field() -> None:
    authority = build_checkpoint_repair_authority(
        previous_pipeline=_failed_pipeline(),
        repaired_pipeline=_repaired_pipeline(_failed_pipeline()),
    )
    assert authority is not None
    payload = RemoteCommitPipelineContract(
        pipeline_id="pipeline-1",
        checkpoint_repair_authority=authority.to_dict(),
    ).to_dict()

    restored = remote_commit_pipeline_contract_from_mapping(payload)

    assert (
        restored.checkpoint_repair_authority["contract_id"]
        == "CheckpointRepairAuthority"
    )
    assert restored.push_failure_transition == {}


def test_startup_repair_surfaces_governed_commit_after_verified_repair() -> None:
    authority = build_checkpoint_repair_authority(
        previous_pipeline=_failed_pipeline(),
        repaired_pipeline=_repaired_pipeline(_failed_pipeline()),
    )
    ctx = SimpleNamespace(
        advisory_action="checkpoint_before_continue",
        advisory_reason="staged_index_budget_exceeded",
        governance=SimpleNamespace(
            repo_identity=SimpleNamespace(
                repo_name="VoiceTerm",
                current_branch="feature/test",
            ),
            push_enforcement=SimpleNamespace(
                checkpoint_required=True,
                safe_to_continue_editing=False,
            ),
        ),
        push_decision=SimpleNamespace(
            next_step_command="",
            next_step_summary="Cut a bounded checkpoint.",
        ),
        reviewer_gate=SimpleNamespace(
            effective_reviewer_mode="tools_only",
            reviewer_mode="tools_only",
            bridge_active=False,
        ),
    )

    result = build_startup_repair_result(
        ctx=ctx,
        authority_report={"ok": False},
        startup_receipt_path="dev/reports/startup/latest/receipt.json",
        runtime=StartupRepairRuntimeInputs(checkpoint_repair_authority=authority),
    )

    assert result.next_action == GOVERNED_CHECKPOINT_COMMIT
    assert result.repairable_issue_count == 1
    assert result.checkpoint_repair_authority is not None
    assert result.checkpoint_repair_authority["result"] == REPAIR_VERIFIED
    assert "devctl.py commit" in result.next_command
