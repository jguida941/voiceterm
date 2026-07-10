"""Tests for git branch/tag operation receipts."""

from __future__ import annotations

from dev.scripts.devctl.runtime.git_operation_receipts import (
    BranchOperation,
    BranchOperationReceipt,
    GitOperationStatus,
    TagOperation,
    TagReceipt,
    append_git_operation_receipt,
    build_branch_operation_receipt,
    build_tag_receipt,
    read_branch_operation_receipts,
    read_tag_receipts,
)


def test_tag_receipt_round_trips_through_store(tmp_path) -> None:
    store = tmp_path / "git_operation_receipts.jsonl"
    receipt = build_tag_receipt(
        tag_name="v1.2.3",
        operation=TagOperation.CREATE,
        target_sha="abc123",
        previous_target_sha="",
        tagger_actor="codex",
        executed_at_utc="2026-05-17T05:44:00Z",
        evidence_refs=("packet:rev_pkt_4289",),
    )

    append_git_operation_receipt(store, receipt)

    rows = read_tag_receipts(store)
    assert rows == (receipt,)
    payload = rows[0].to_dict()
    assert payload["contract_id"] == "TagReceipt"
    assert payload["operation"] == "create"
    assert payload["status"] == "recorded"


def test_branch_operation_receipt_round_trips_through_store(tmp_path) -> None:
    store = tmp_path / "git_operation_receipts.jsonl"
    receipt = build_branch_operation_receipt(
        branch_name="feature/example",
        operation=BranchOperation.UPDATE,
        previous_ref="abc123",
        new_ref="def456",
        remote_name="origin",
        executed_by_actor="codex",
        executed_at_utc="2026-05-17T05:45:00Z",
        evidence_refs=("packet:rev_pkt_4289",),
    )

    append_git_operation_receipt(store, receipt)

    rows = read_branch_operation_receipts(store)
    assert rows == (receipt,)
    payload = rows[0].to_dict()
    assert payload["contract_id"] == "BranchOperationReceipt"
    assert payload["operation"] == "update"
    assert payload["status"] == "recorded"


def test_receipts_normalize_mappings() -> None:
    tag = TagReceipt.from_mapping(
        {
            "receipt_id": "tag-1",
            "tag_name": "v1.2.3",
            "operation": "delete",
            "target_sha": "",
            "status": "superseded",
        }
    )
    branch = BranchOperationReceipt.from_mapping(
        {
            "receipt_id": "branch-1",
            "branch_name": "feature/example",
            "operation": "checkout",
            "new_ref": "def456",
            "status": "failed",
        }
    )

    assert tag.operation is TagOperation.DELETE
    assert tag.status is GitOperationStatus.SUPERSEDED
    assert branch.operation is BranchOperation.CHECKOUT
    assert branch.status is GitOperationStatus.FAILED
