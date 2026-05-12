"""Tests for shared runtime action/run/adapter contracts."""

from __future__ import annotations

from dev.scripts.devctl.runtime import (
    ACTION_RESULT_CONTRACT_ID,
    ACTION_RESULT_SCHEMA_VERSION,
    ActionResult,
    ArtifactStore,
    causation_ref,
    correlation_context_for_ref,
    correlation_ref,
    action_result_from_mapping,
    provider_adapter_from_mapping,
    run_ref,
    run_record_from_mapping,
    typed_action_from_mapping,
    workflow_adapter_from_mapping,
)
from dev.scripts.devctl.runtime.action_contracts import ActionOutcome


def test_typed_action_from_mapping_normalizes_payload() -> None:
    action = typed_action_from_mapping(
        {
            "action_id": "review-channel.status",
            "repo_pack_id": "voiceterm",
            "parameters": {"format": "json"},
            "requested_by": "agent",
            "dry_run": "true",
            "correlation_id": "corr-1",
            "causation_id": "cause-1",
            "run_id": "run-1",
        }
    )
    assert action.contract_id == "TypedAction"
    assert action.action_id == "review-channel.status"
    assert action.repo_pack_id == "voiceterm"
    assert action.parameters == {"format": "json"}
    assert action.requested_by == "agent"
    assert action.dry_run is True
    assert action.correlation_id == "corr-1"
    assert action.causation_id == "cause-1"
    assert action.run_id == "run-1"


def test_run_record_from_mapping_normalizes_artifacts_and_findings() -> None:
    record = run_record_from_mapping(
        {
            "run_id": "run-123",
            "action_id": "triage-loop",
            "artifact_paths": ["dev/reports/a.md", "", None],
            "status": "complete",
            "findings_count": "4",
            "correlation_id": "corr-1",
            "causation_id": "cause-1",
        }
    )
    assert record.contract_id == "RunRecord"
    assert record.run_id == "run-123"
    assert record.action_id == "triage-loop"
    assert record.artifact_paths == ("dev/reports/a.md",)
    assert record.status == "complete"
    assert record.findings_count == 4
    assert record.correlation_id == "corr-1"
    assert record.causation_id == "cause-1"


def test_adapter_and_artifact_contracts_normalize_defaults() -> None:
    store = ArtifactStore(
        schema_version=1,
        contract_id="ArtifactStore",
        root="dev/reports",
        retention_policy={"days": 14},
        managed_kinds=("report", "snapshot"),
    )
    provider = provider_adapter_from_mapping(
        {
            "provider_id": "codex",
            "capabilities": ["review", "fix"],
            "launch_mode": "cli",
        }
    )
    workflow = workflow_adapter_from_mapping(
        {
            "adapter_id": "github-actions",
            "transport": "github",
            "allowed_actions": ["dispatch", "status"],
            "available": "false",
        }
    )
    assert store.contract_id == "ArtifactStore"
    assert store.managed_kinds == ("report", "snapshot")
    assert provider.contract_id == "ProviderAdapter"
    assert provider.provider_id == "codex"
    assert provider.available is True
    assert workflow.contract_id == "WorkflowAdapter"
    assert workflow.allowed_actions == ("dispatch", "status")
    assert workflow.available is False


def test_action_result_success() -> None:
    result = ActionResult(
        schema_version=ACTION_RESULT_SCHEMA_VERSION,
        contract_id=ACTION_RESULT_CONTRACT_ID,
        action_id="check",
        ok=True,
        status="complete",
        findings_count=0,
        artifact_paths=("dev/reports/check/latest.json",),
    )
    payload = result.to_dict()
    assert payload["ok"] is True
    assert payload["action_id"] == "check"
    assert payload["status"] == "complete"
    assert payload["findings_count"] == 0
    assert payload["artifact_paths"] == ["dev/reports/check/latest.json"]
    assert payload["retryable"] is False
    assert payload["warnings"] == []


def test_action_result_failure_with_guidance() -> None:
    result = ActionResult(
        schema_version=ACTION_RESULT_SCHEMA_VERSION,
        contract_id=ACTION_RESULT_CONTRACT_ID,
        action_id="check",
        ok=False,
        status="failed",
        reason="code_shape_violation",
        retryable=True,
        operator_guidance="Fix oversized functions, then rerun.",
        reason_chain=("guard_bundle_failed", "code_shape_violation"),
        remediation="split_oversized_functions",
        auto_executable=False,
        errors=(
            {
                "reason": "code_shape_violation",
                "remediation": "split_oversized_functions",
                "auto_executable": False,
            },
        ),
        findings_count=3,
        warnings=("Skipped 2 files due to parse errors.",),
    )
    payload = result.to_dict()
    assert payload["ok"] is False
    assert payload["reason"] == "code_shape_violation"
    assert payload["retryable"] is True
    assert payload["operator_guidance"] == "Fix oversized functions, then rerun."
    assert payload["reason_chain"] == ["guard_bundle_failed", "code_shape_violation"]
    assert payload["remediation"] == "split_oversized_functions"
    assert payload["auto_executable"] is False
    assert payload["errors"][0]["reason"] == "code_shape_violation"
    assert payload["findings_count"] == 3


def test_action_result_from_mapping_coerces_types() -> None:
    result = action_result_from_mapping(
        {
            "action_id": "probe-report",
            "ok": "true",
            "status": "complete",
            "findings_count": "7",
            "warnings": ["skipped test files"],
            "errors": [
                {
                    "reason": "host_process_cleanup_post_age_out",
                    "auto_executable": True,
                }
            ],
            "reason_chain": ["guard_bundle_failed", "host-process-cleanup-post"],
            "remediation": "host_process_cleanup_post_age_retry",
            "auto_executable": "true",
            "artifact_paths": ["dev/reports/probes/latest/review_packet.json"],
        }
    )
    assert result.contract_id == ACTION_RESULT_CONTRACT_ID
    assert result.ok is True
    assert result.findings_count == 7
    assert result.warnings == ("skipped test files",)
    assert result.errors[0]["reason"] == "host_process_cleanup_post_age_out"
    assert result.reason_chain == ("guard_bundle_failed", "host-process-cleanup-post")
    assert result.remediation == "host_process_cleanup_post_age_retry"
    assert result.auto_executable is True
    assert result.artifact_paths == ("dev/reports/probes/latest/review_packet.json",)


def test_action_result_roundtrip() -> None:
    """ActionResult.to_dict() output can be parsed back by action_result_from_mapping()."""
    original = ActionResult(
        schema_version=ACTION_RESULT_SCHEMA_VERSION,
        contract_id=ACTION_RESULT_CONTRACT_ID,
        action_id="governance-review",
        ok=True,
        status="recorded",
        findings_count=1,
        artifact_paths=("dev/reports/governance/latest/summary.md",),
        correlation_id="corr-1",
        causation_id="cause-1",
        run_id="run-1",
    )
    roundtripped = action_result_from_mapping(original.to_dict())
    assert roundtripped.action_id == original.action_id
    assert roundtripped.ok == original.ok
    assert roundtripped.findings_count == original.findings_count
    assert roundtripped.artifact_paths == original.artifact_paths
    assert roundtripped.correlation_id == original.correlation_id
    assert roundtripped.causation_id == original.causation_id
    assert roundtripped.run_id == original.run_id


def test_correlation_context_refs_are_stable() -> None:
    context = correlation_context_for_ref(
        "typed_action",
        "review-channel.post",
        causation_kind="packet",
        causation_ref_value="rev_pkt_1",
        run_kind="session",
        run_ref_value="session-1",
    )

    assert context.correlation_id.startswith("corr-")
    assert context.causation_id.startswith("cause-")
    assert context.run_id.startswith("run-")
    assert correlation_ref(context.correlation_id).startswith("correlation_ref:")
    assert causation_ref(context.causation_id).startswith("causation_ref:")
    assert run_ref(context.run_id).startswith("run_ref:")


def test_action_outcome_constants_are_consistent() -> None:
    assert ActionOutcome.PASS == "pass"
    assert ActionOutcome.FAIL == "fail"
    assert ActionOutcome.UNKNOWN == "unknown"
    assert ActionOutcome.DEFER == "defer"
    assert len(ActionOutcome.ALL) == 4


def test_action_result_defaults_to_unknown() -> None:
    result = ActionResult(
        schema_version=1,
        contract_id="ActionResult",
        action_id="test",
        ok=False,
    )
    assert result.status == ActionOutcome.UNKNOWN


def test_action_result_accepts_defer() -> None:
    result = ActionResult(
        schema_version=1,
        contract_id="ActionResult",
        action_id="test",
        ok=False,
        status=ActionOutcome.DEFER,
    )
    assert result.status == ActionOutcome.DEFER
    assert result.status in ActionOutcome.ALL


def test_action_result_unknown_roundtrips() -> None:
    result = ActionResult(
        schema_version=1,
        contract_id="ActionResult",
        action_id="test",
        ok=False,
        status=ActionOutcome.UNKNOWN,
    )
    roundtripped = action_result_from_mapping(result.to_dict())
    assert roundtripped.status == ActionOutcome.UNKNOWN


def test_action_result_defer_roundtrips() -> None:
    result = ActionResult(
        schema_version=1,
        contract_id="ActionResult",
        action_id="test",
        ok=False,
        status=ActionOutcome.DEFER,
    )
    roundtripped = action_result_from_mapping(result.to_dict())
    assert roundtripped.status == ActionOutcome.DEFER
