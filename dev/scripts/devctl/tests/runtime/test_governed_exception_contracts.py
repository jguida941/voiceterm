"""Tests for governed exception receipt/lifecycle contracts."""

from __future__ import annotations

from dev.scripts.devctl.runtime.governed_exception_contracts import (
    ExceptionReceipt,
    GovernedExceptionLifecycle,
    validate_exception_receipt,
    validate_governed_exception_lifecycle,
)
from dev.scripts.devctl.runtime.governed_exception_store import (
    load_governed_exception_lifecycles_with_errors,
    pending_governed_exception_lifecycles,
)


def _valid_receipt(**overrides: object) -> ExceptionReceipt:
    values = {
        "receipt_id": "exception:vcs.push:review_snapshot_refresh:58246e50",
        "action_kind": "vcs.push",
        "phase": "preflight",
        "guard_id": "review_snapshot_refresh",
        "exception_class": "review_snapshot_refresh_failure",
        "operator_reason": (
            "ReviewSnapshot refresh failed during governed push preflight and "
            "needs a repair/proof lifecycle."
        ),
        "head": "58246e50",
        "finding_id": "finding:review_snapshot_refresh",
        "authority_evidence_refs": ("authority_snapshot:123",),
        "worktree_safety_evidence_refs": ("orphan_snapshot:123",),
    }
    values.update(overrides)
    return ExceptionReceipt(**values)


def test_valid_exception_receipt_validates() -> None:
    assert validate_exception_receipt(_valid_receipt()) == ()


def test_exception_receipt_scope_round_trips() -> None:
    receipt = _valid_receipt(scope="managed projection refresh")
    payload = receipt.to_dict()
    restored = ExceptionReceipt.from_mapping(payload)

    assert payload["scope"] == "managed projection refresh"
    assert restored.scope == "managed projection refresh"
    assert restored.correlation_id.startswith("corr-")
    assert restored.causation_id.startswith("cause-")
    assert restored.run_id.startswith("run-")


def test_missing_reason_fails_validation() -> None:
    errors = validate_exception_receipt(_valid_receipt(operator_reason=""))
    assert "missing_or_generic_reason" in errors


def test_generic_reason_fails_validation() -> None:
    errors = validate_exception_receipt(_valid_receipt(operator_reason="bypass"))
    assert "missing_or_generic_reason" in errors


def test_missing_head_fails_validation() -> None:
    errors = validate_exception_receipt(_valid_receipt(head=""))
    assert "missing_head" in errors


def test_stale_head_fails_validation() -> None:
    errors = validate_exception_receipt(_valid_receipt(), current_head="abcdef12")
    assert "stale_head" in errors


def test_unknown_exception_class_fails_validation() -> None:
    errors = validate_exception_receipt(_valid_receipt(exception_class="new_unknown"))
    assert "unknown_exception_class" in errors


def test_missing_action_phase_or_guard_fails_validation() -> None:
    errors = validate_exception_receipt(
        _valid_receipt(action_kind="", phase="", guard_id="")
    )
    assert "missing_action_kind" in errors
    assert "missing_phase" in errors
    assert "missing_guard_id" in errors


def test_missing_finding_or_planned_hook_fails_validation() -> None:
    errors = validate_exception_receipt(
        _valid_receipt(finding_id="", planned_finding_ingest_ref="")
    )
    assert "missing_finding_or_planned_finding_ingest" in errors


def test_closed_lifecycle_without_resolution_fails_validation() -> None:
    lifecycle = GovernedExceptionLifecycle(
        lifecycle_id="gel:vcs.push:review_snapshot_refresh:58246e50",
        status="closed",
        exception=_valid_receipt(),
    )
    errors = validate_governed_exception_lifecycle(lifecycle)
    assert "closed_lifecycle_without_resolution" in errors
    assert "closed_lifecycle_without_closure_proof" in errors


def test_closed_lifecycle_with_resolution_id_only_fails_validation() -> None:
    lifecycle = GovernedExceptionLifecycle(
        lifecycle_id="gel:vcs.push:review_snapshot_refresh:58246e50",
        status="closed",
        exception=_valid_receipt(),
        resolution_receipt_id="resolution:only-id",
    )
    errors = validate_governed_exception_lifecycle(lifecycle)
    assert "closed_lifecycle_without_resolution" in errors
    assert "closed_lifecycle_without_closure_proof" in errors


def test_mutation_receipt_without_authority_evidence_fails_validation() -> None:
    errors = validate_exception_receipt(_valid_receipt(authority_evidence_refs=()))
    assert "missing_authority_evidence" in errors


def test_mutation_receipt_without_worktree_evidence_fails_validation() -> None:
    errors = validate_exception_receipt(
        _valid_receipt(worktree_safety_evidence_refs=())
    )
    assert "missing_worktree_or_orphan_evidence" in errors


def test_vcs_push_success_without_remote_ref_proof_fails_validation() -> None:
    errors = validate_exception_receipt(
        _valid_receipt(execution_status="success", remote_ref_verified=False)
    )
    assert "push_success_without_remote_ref_or_post_push_proof" in errors


def test_vcs_push_success_without_post_push_proof_fails_validation() -> None:
    errors = validate_exception_receipt(
        _valid_receipt(execution_status="success", remote_ref_verified=True)
    )
    assert "push_success_without_remote_ref_or_post_push_proof" in errors


def test_pending_store_missing_file_returns_empty_tuple(tmp_path) -> None:
    assert pending_governed_exception_lifecycles(tmp_path / "missing.jsonl") == ()


def test_store_reports_malformed_jsonl_without_dropping_silently(tmp_path) -> None:
    store = tmp_path / "lifecycles.jsonl"
    store.write_text("{bad-json\n", encoding="utf-8")

    result = load_governed_exception_lifecycles_with_errors(store)

    assert result.lifecycles == ()
    assert result.errors
