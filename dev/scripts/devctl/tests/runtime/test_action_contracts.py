"""Tests for shared runtime action/run/adapter contracts."""

from __future__ import annotations

from dev.scripts.devctl.runtime import (
    ArtifactStore,
    provider_adapter_from_mapping,
    run_record_from_mapping,
    typed_action_from_mapping,
    workflow_adapter_from_mapping,
)


def test_typed_action_from_mapping_normalizes_payload() -> None:
    action = typed_action_from_mapping(
        {
            "action_id": "review-channel.status",
            "repo_pack_id": "voiceterm",
            "parameters": {"format": "json"},
            "requested_by": "agent",
            "dry_run": "true",
        }
    )
    assert action.contract_id == "TypedAction"
    assert action.action_id == "review-channel.status"
    assert action.repo_pack_id == "voiceterm"
    assert action.parameters == {"format": "json"}
    assert action.requested_by == "agent"
    assert action.dry_run is True


def test_run_record_from_mapping_normalizes_artifacts_and_findings() -> None:
    record = run_record_from_mapping(
        {
            "run_id": "run-123",
            "action_id": "triage-loop",
            "artifact_paths": ["dev/reports/a.md", "", None],
            "status": "complete",
            "findings_count": "4",
        }
    )
    assert record.contract_id == "RunRecord"
    assert record.run_id == "run-123"
    assert record.action_id == "triage-loop"
    assert record.artifact_paths == ("dev/reports/a.md",)
    assert record.status == "complete"
    assert record.findings_count == 4


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
