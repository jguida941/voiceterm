"""Coverage for lineage fields on runtime evidence contracts."""

from __future__ import annotations

from dev.scripts.devctl.runtime.validation_contracts import (
    validation_receipt_from_mapping,
)


def test_validation_receipt_derives_correlation_spine_fields() -> None:
    receipt = validation_receipt_from_mapping(
        {
            "receipt_id": "validation-receipt-1",
            "plan_id": "validation-plan-1",
            "bundle_id": "quick",
            "staged_tree_hash": "tree-1",
            "action_id": "quality.guard_bundle",
            "status": "pass",
        }
    )

    assert receipt is not None
    payload = receipt.to_dict()
    assert payload["correlation_id"].startswith("corr-")
    assert payload["causation_id"].startswith("cause-")
    assert payload["run_id"].startswith("run-")


def test_validation_receipt_preserves_existing_correlation_spine_fields() -> None:
    receipt = validation_receipt_from_mapping(
        {
            "receipt_id": "validation-receipt-2",
            "plan_id": "validation-plan-2",
            "correlation_id": "corr-explicit",
            "causation_id": "cause-explicit",
            "run_id": "run-explicit",
        }
    )

    assert receipt is not None
    assert receipt.correlation_id == "corr-explicit"
    assert receipt.causation_id == "cause-explicit"
    assert receipt.run_id == "run-explicit"
