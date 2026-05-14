"""Tests for `devctl platform-contracts`."""

from __future__ import annotations

import json
import tempfile
from argparse import Namespace
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from dev.scripts.devctl.commands import platform_contracts
from dev.scripts.devctl.platform.blueprint import build_platform_blueprint


def _build_args(*, format: str) -> Namespace:
    return Namespace(
        format=format,
        output=None,
        pipe_command=None,
        pipe_args=None,
    )


def test_platform_blueprint_contract_ids_are_unique() -> None:
    blueprint = build_platform_blueprint()
    contract_ids = [contract.contract_id for contract in blueprint.shared_contracts]
    assert len(contract_ids) == len(set(contract_ids))
    assert len(blueprint.service_lifecycle) >= 1
    assert len(blueprint.caller_authority) >= 1
    assert "RepoPack" in contract_ids
    assert "TypedAction" in contract_ids
    assert "ControlState" in contract_ids
    assert "ReviewState" in contract_ids
    assert "AgentDispatchRouter" in contract_ids
    assert "DevelopmentModeTopology" in contract_ids
    assert "DevelopmentLoopReport" in contract_ids
    assert "BaselineAuthorityInventoryReceipt" in contract_ids
    assert "PlatformContractRegistryRow" in contract_ids
    assert "PlanSourceSnapshot" in contract_ids
    assert "ReviewerRuntimeContract" in contract_ids
    assert "SessionPosture" in contract_ids
    assert "PacketIntentAnchor" in contract_ids
    assert "RemoteCommitPipelineContract" in contract_ids
    assert "CheckpointBudgetShape" in contract_ids
    assert "CheckpointRepairAuthority" in contract_ids
    assert "PushAuthorizationRecord" in contract_ids
    assert "CheckResult" in contract_ids
    assert "Finding" in contract_ids
    assert "DecisionPacket" in contract_ids
    assert "EvidenceArchivePolicy" in contract_ids
    assert "EvidenceArchiveManifest" in contract_ids
    assert "EvidenceArchiveReceipt" in contract_ids
    assert "SessionActivityEntry" in contract_ids
    assert "SessionActivityLog" in contract_ids
    assert "ReviewerResponseShape" in contract_ids
    assert "RoleInstructionCard" in contract_ids
    assert "RoleGuard" in contract_ids
    assert "CustomRoleDefinition" in contract_ids
    assert "RoleCreationAction" in contract_ids
    assert "PeerHeartbeatEvidence" in contract_ids
    assert "AgentLoopBilateralProtocol" in contract_ids
    assert "PreDecisionComposabilityWindow" in contract_ids
    assert "CommitReceipt" in contract_ids
    assert "GoalProgressReceipt" in contract_ids
    assert "FailurePacket" in contract_ids
    assert "LocalServiceEndpoint" in contract_ids
    assert "CallerAuthorityPolicy" in contract_ids
    assert "GovernedExceptionLifecycle" in contract_ids
    assert "ExceptionReceipt" in contract_ids
    assert "BypassRequest" in contract_ids
    assert "BypassEvaluation" in contract_ids
    assert "BypassReceipt" in contract_ids
    assert "BypassExpiry" in contract_ids
    assert "BypassLifecycle" in contract_ids
    assert "GovernedTransitionModule" in contract_ids
    assert "TransitionContract" in contract_ids
    assert "ResolutionReceipt" in contract_ids
    assert "ExceptionPolicy" in contract_ids
    assert "ExceptionClass" in contract_ids
    assert "ExceptionLifecycleStatus" in contract_ids
    assert "ClosureProof" in contract_ids
    assert "AutoRepairReceipt" in contract_ids
    assert "ManualBypassImportReceipt" in contract_ids
    assert len(blueprint.artifact_schemas) >= 1
    artifact_ids = [schema.contract_id for schema in blueprint.artifact_schemas]
    assert "PlatformContractRegistry" in artifact_ids
    assert "DogfoodSelfCheckReceipt" in artifact_ids
    assert "ReviewerAuditReceipt" in artifact_ids
    assert "SessionActivityLog" in artifact_ids
    assert "CommitReceipt" in artifact_ids
    assert "GoalProgressReceipt" in artifact_ids


def test_platform_blueprint_contract_shapes_cover_lifecycle_and_authority() -> None:
    blueprint = build_platform_blueprint()
    contracts_by_id = {
        contract.contract_id: contract for contract in blueprint.shared_contracts
    }
    contract_map = {
        contract.contract_id: {field.name for field in contract.required_fields}
        for contract in blueprint.shared_contracts
    }
    assert "violations" in contract_map["CheckResult"]
    assert "success" in contract_map["CheckResult"]
    assert "steps" in contract_map["CheckResult"]
    assert "shutdown_entrypoints" in contract_map["LocalServiceEndpoint"]
    assert "forbidden_actions" in contract_map["CallerAuthorityPolicy"]
    assert "signals" in contract_map["Finding"]
    assert "correlation_id" in contract_map["Finding"]
    assert "causation_id" in contract_map["Finding"]
    assert "run_id" in contract_map["Finding"]
    assert "validation_plan" in contract_map["DecisionPacket"]
    assert "rule_summary" in contract_map["DecisionPacket"]
    assert "match_evidence" in contract_map["DecisionPacket"]
    assert "rejected_rule_traces" in contract_map["DecisionPacket"]
    assert "retention_days" in contract_map["EvidenceArchivePolicy"]
    assert "archive_after_lifecycle_statuses" in contract_map["EvidenceArchivePolicy"]
    assert "delete_source_after_archive" in contract_map["EvidenceArchivePolicy"]
    assert "entries" in contract_map["EvidenceArchiveManifest"]
    assert "head_sha_at_archive" in contract_map["EvidenceArchiveManifest"]
    assert "source_deleted" in contract_map["EvidenceArchiveReceipt"]
    assert "manifest_path" in contract_map["EvidenceArchiveReceipt"]
    assert "session_id" in contract_map["SessionActivityLog"]
    assert "entries" in contract_map["SessionActivityLog"]
    assert "evidence_archive_ref" in contract_map["SessionActivityLog"]
    assert "activity_type" in contract_map["SessionActivityEntry"]
    assert "packet_refs" in contract_map["SessionActivityEntry"]
    assert "response_mode" in contract_map["ReviewerResponseShape"]
    assert "status_prose_allowed" in contract_map["ReviewerResponseShape"]
    assert "operator_status_source" in contract_map["ReviewerResponseShape"]
    assert "proposed_response_text_observed" in contract_map["ReviewerResponseShape"]
    assert "proposed_response_text_source" in contract_map["ReviewerResponseShape"]
    assert "violations" in contract_map["ReviewerResponseShape"]
    assert "rules" in contract_map["RoleInstructionCard"]
    assert "enforcement_point" in contract_map["RoleGuard"]
    assert "base_workstream_id" in contract_map["CustomRoleDefinition"]
    assert "instruction_cards" in contract_map["RoleCreationAction"]
    assert "validation_errors" in contract_map["RoleCreationAction"]
    assert "heartbeat_packet_id" in contract_map["PeerHeartbeatEvidence"]
    assert "peer_offline" in contract_map["PeerHeartbeatEvidence"]
    assert "property_results" in contract_map["AgentLoopBilateralProtocol"]
    assert "failing_property_ids" in contract_map["AgentLoopBilateralProtocol"]
    assert "lane_resumption_refs" in contract_map["AgentLoopBilateralProtocol"]
    assert "command_evidence_refs" in contract_map["AgentLoopBilateralProtocol"]
    assert "receipt_refs" in contract_map["AgentLoopBilateralProtocol"]
    assert "proof_ref" in contract_map["AgentLoopBilateralProtocol"]
    assert "composability_anchors" in contract_map["PreDecisionComposabilityWindow"]
    assert "duplicate_hunt_ref" in contract_map["PreDecisionComposabilityWindow"]
    assert "commit_blocked" in contract_map["PreDecisionComposabilityWindow"]
    assert "reviewer_ack_packet_id" in contract_map["CommitReceipt"]
    assert "audit_synthesis_ref" in contract_map["CommitReceipt"]
    assert "pre_state" in contract_map["CommitReceipt"]
    assert "post_state" in contract_map["CommitReceipt"]
    assert "evidence_refs" in contract_map["CommitReceipt"]
    assert "progress_percentage_toward_goal" in contract_map["GoalProgressReceipt"]
    assert "continuation_anchor_packet_id" in contract_map["GoalProgressReceipt"]
    assert "latest_progress_packet_id" in contract_map["GoalProgressReceipt"]
    assert "reviewer_runtime" in contract_map["ReviewState"]
    assert "commit_pipeline" in contract_map["ReviewState"]
    assert "push_authorization" in contract_map["ReviewState"]
    assert "authority_snapshot" in contract_map["ReviewState"]
    assert "round_proofs" in contract_map["ReviewState"]
    assert "agent_loop_decisions" in contract_map["ReviewState"]
    assert "agent_dispatch_router" in contract_map["ReviewState"]
    assert "snapshot_id" in contract_map["ReviewState"]
    assert "routes" in contract_map["AgentDispatchRouter"]
    assert "rejected_routes" in contract_map["AgentDispatchRouter"]
    assert "session_nodes" in contract_map["AgentDispatchRouter"]
    assert "work_focus" in contract_map["AgentDispatchRouter"]
    assert "peer_links" in contract_map["AgentDispatchRouter"]
    assert "ambiguous_session_groups" in contract_map["AgentDispatchRouter"]
    assert "governance_debt" in contract_map["AgentDispatchRouter"]
    assert "selected_route_id" in contract_map["AgentDispatchRouter"]
    assert "selected_route_ids" in contract_map["AgentDispatchRouter"]
    assert "router_state" in contract_map["AgentDispatchRouter"]
    assert "workstreams" in contract_map["DevelopmentModeTopology"]
    assert "external_research" in contract_map["DevelopmentModeTopology"]
    assert "knowledge_flow" in contract_map["DevelopmentModeTopology"]
    assert "scaling" in contract_map["DevelopmentModeTopology"]
    assert "topology" in contract_map["DevelopmentLoopReport"]
    assert "next_slice" in contract_map["DevelopmentLoopReport"]
    assert "packet_attention" in contract_map["DevelopmentLoopReport"]
    assert "runtime" in contract_map["DevelopmentLoopReport"]
    assert "peer_minds" in contract_map["DevelopmentLoopReport"]
    assert "reviewer_response_shape" in contract_map["DevelopmentLoopReport"]
    assert "packet_debt_remediation" in contract_map["DevelopmentLoopReport"]
    assert "repo_state_fingerprint" in contract_map["BaselineAuthorityInventoryReceipt"]
    assert "state_store_entries" in contract_map["BaselineAuthorityInventoryReceipt"]
    assert "direct_write_sites" in contract_map["BaselineAuthorityInventoryReceipt"]
    assert "duplicate_system_clusters" in contract_map["BaselineAuthorityInventoryReceipt"]
    assert "registered_contract_id" in contract_map["PlatformContractRegistryRow"]
    assert "entry_kind" in contract_map["PlatformContractRegistryRow"]
    assert "registered_schema_version" in contract_map["PlatformContractRegistryRow"]
    assert "ownership_mode" in contract_map["PlatformContractRegistryRow"]
    assert "action_id" in contract_map["PlanIntentIngestionReceipt"]
    assert "source_snapshot_ids" in contract_map["PlanIntentIngestionReceipt"]
    assert "source_integrity_status" in contract_map["PlanIntentIngestionReceipt"]
    assert "source_completeness_status" in contract_map["PlanIntentIngestionReceipt"]
    assert "source_missing_required_anchors" in contract_map["PlanIntentIngestionReceipt"]
    assert "composition_disposition_matrix" in contract_map["PlanIntentIngestionReceipt"]
    assert "command_manifest_proofs" in contract_map["PlanIntentIngestionReceipt"]
    assert "guard_maturity_records" in contract_map["PlanIntentIngestionReceipt"]
    assert "repo_state_fingerprint" in contract_map["PlanIntentIngestionReceipt"]
    assert "receipt_coverage_inventory" in contract_map["PlanIntentIngestionReceipt"]
    assert "schema_limit_warning" in contract_map["PlanIntentIngestionReceipt"]
    assert "source_text" in contract_map["PlanSourceSnapshot"]
    assert "receipt_id" in contract_map["PlanSourceSnapshot"]
    assert "action_id" in contract_map["PlanSourceSnapshot"]
    assert "retention_status" in contract_map["PlanSourceSnapshot"]
    assert "source_completeness_status" in contract_map["PlanSourceSnapshot"]
    assert "missing_required_anchors" in contract_map["PlanSourceSnapshot"]
    assert "composition_disposition" in contract_map["PlanSourceSnapshot"]
    assert "existing_owner_row_refs" in contract_map["PlanSourceSnapshot"]
    assert "packet_binding_refs" in contract_map["PlanSourceSnapshot"]
    assert "schema_limit_warning" in contract_map["PlanSourceSnapshot"]
    assert "authority_snapshot" in contract_map["SessionCachePacket"]
    assert "session_posture" in contract_map["SessionCachePacket"]
    assert "packet_intent_anchors" in contract_map["SessionCachePacket"]
    assert "runtime_spine_closure" in contract_map["SessionCachePacket"]
    assert "packet_continuity_index" in contract_map["SessionCachePacket"]
    assert "packet_carry_forward_debt" in contract_map["SessionCachePacket"]
    assert "continuity_attention" in contract_map["SessionCachePacket"]
    assert "conductor_visibility" in contract_map["ReviewerRuntimeContract"]
    assert "publish_clear" in contract_map["ReviewerRuntimeContract"]
    assert "session_posture" in contract_map["ReviewerRuntimeContract"]
    assert "actors" in contract_map["SessionPosture"]
    assert "lifecycle_state" in contract_map["PacketIntentAnchor"]
    assert "approval_expires_at_utc" in contract_map["RemoteCommitPipelineContract"]
    assert "approved_target_identity" in contract_map["RemoteCommitPipelineContract"]
    assert "push_authorization" in contract_map["RemoteCommitPipelineContract"]
    assert "tree_hash_match" in contract_map["CheckpointBudgetShape"]
    assert "bootstrap_blocked" in contract_map["CheckpointBudgetShape"]
    assert "next_required_action" in contract_map["CheckpointBudgetShape"]
    assert "next_authorized_action" in contract_map["CheckpointRepairAuthority"]
    assert "validation_receipt_id" in contract_map["CheckpointRepairAuthority"]
    assert "blocked_raw_actions" in contract_map["CheckpointRepairAuthority"]
    assert "authorized_head_sha" in contract_map["PushAuthorizationRecord"]
    assert "approval_mode" in contract_map["PushAuthorizationRecord"]
    assert "snapshot_id" in contract_map["RemoteCommitPipelineContract"]
    assert "exception" in contract_map["GovernedExceptionLifecycle"]
    assert "operator_reason" in contract_map["ExceptionReceipt"]
    assert "remote_ref_verified" in contract_map["ExceptionReceipt"]
    assert "correlation_id" in contract_map["ExceptionReceipt"]
    assert "causation_id" in contract_map["ExceptionReceipt"]
    assert "run_id" in contract_map["ExceptionReceipt"]
    assert "target_surface" in contract_map["BypassRequest"]
    assert "governed_exception_lifecycle_id" in contract_map["BypassEvaluation"]
    assert "requested_authority_scope" in contract_map["BypassReceipt"]
    assert "source" in contract_map["BypassExpiry"]
    assert "governed_exception" in contract_map["BypassLifecycle"]
    assert "module" in contract_map["GovernedTransitionModule"]
    assert "transition_id" in contract_map["TransitionContract"]
    assert "requires" in contract_map["TransitionContract"]
    assert "produces" in contract_map["TransitionContract"]
    assert "validation_receipt_id" in contract_map["ResolutionReceipt"]
    assert "forbidden_exception_classes" in contract_map["ExceptionPolicy"]

    receipt_links = {
        (link.source_field, link.target_contract, link.edge_kind)
        for link in contracts_by_id["PlanIntentIngestionReceipt"].cross_links
    }
    snapshot_links = {
        (link.source_field, link.target_contract, link.edge_kind)
        for link in contracts_by_id["PlanSourceSnapshot"].cross_links
    }
    assert ("action_id", "TypedAction", "receipt_proves") in receipt_links
    assert ("receipt_id", "PlanIntentIngestionReceipt", "related_to") in snapshot_links
    assert ("action_id", "TypedAction", "related_to") in snapshot_links


def test_governed_exception_contracts_declare_semantic_cross_links() -> None:
    blueprint = build_platform_blueprint()
    contract_map = {
        contract.contract_id: contract
        for contract in blueprint.shared_contracts
    }

    lifecycle_links = {
        (link.source_field, link.target_contract, link.edge_kind, link.direction)
        for link in contract_map["GovernedExceptionLifecycle"].cross_links
    }
    receipt_links = {
        (link.source_field, link.target_contract, link.edge_kind, link.direction)
        for link in contract_map["ExceptionReceipt"].cross_links
    }
    resolution_links = {
        (link.source_field, link.target_contract, link.edge_kind)
        for link in contract_map["ResolutionReceipt"].cross_links
    }

    assert ("exception", "ExceptionReceipt", "contains", "forward") in lifecycle_links
    assert (
        "finding_id",
        "FindingBacklog",
        "finding_blocks",
        "reverse",
    ) in lifecycle_links
    assert (
        "finding_id",
        "FindingBacklog",
        "finding_blocks",
        "reverse",
    ) in receipt_links
    assert (
        "exception_lifecycle_id",
        "GovernedExceptionLifecycle",
        "receipt_proves",
    ) in resolution_links
    assert contract_map["ExceptionReceipt"].cross_links[0].target_resolver == (
        "finding_backlog_id"
    )
    lifecycle_resolution = next(
        link
        for link in contract_map["GovernedExceptionLifecycle"].cross_links
        if link.source_field == "resolution_receipt_id"
    )
    assert lifecycle_resolution.target_resolver == "resolution_receipt_id"
    assert lifecycle_resolution.target_id_template == ""
    resolution_closure = next(
        link
        for link in contract_map["ResolutionReceipt"].cross_links
        if link.source_field == "closure_proof_id"
    )
    assert resolution_closure.target_resolver == "closure_proof_id"
    assert resolution_closure.target_id_template == ""
    validation_link = next(
        link
        for link in contract_map["ClosureProof"].cross_links
        if link.target_contract == "ValidationReceipt"
    )
    assert validation_link.required is False
    assert validation_link.validation_policy == (
        "deferred_until_validation_contract_registered"
    )


def test_platform_contracts_json_output(capsys) -> None:
    exit_code = platform_contracts.run(_build_args(format="json"))
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "platform-contracts"
    assert payload["schema_version"] == 1
    contract_ids = [row["contract_id"] for row in payload["shared_contracts"]]
    artifact_ids = [row["contract_id"] for row in payload["artifact_schemas"]]
    contract_map = {
        row["contract_id"]: {field["name"] for field in row["required_fields"]}
        for row in payload["shared_contracts"]
    }
    assert "CheckResult" in contract_ids
    assert "WorkflowAdapter" in contract_ids
    assert "Finding" in contract_ids
    assert "DecisionPacket" in contract_ids
    assert "ProbeReport" in artifact_ids
    assert "ReviewPacket" in artifact_ids
    assert "DogfoodSelfCheckReceipt" in artifact_ids
    assert "ReviewerAuditReceipt" in artifact_ids
    assert "SystemPicture" in artifact_ids
    assert payload["service_lifecycle"][0]["service_id"] == "voiceterm_daemon"
    assert "shutdown_entrypoints" in contract_map["LocalServiceEndpoint"]
    assert "forbidden_actions" in contract_map["CallerAuthorityPolicy"]
    caller_ids = [row["caller_id"] for row in payload["caller_authority"]]
    assert "human_operator" in caller_ids
    layer_ids = [row["layer_id"] for row in payload["layers"]]
    assert "governance_runtime" in layer_ids
    exception_contract = next(
        row for row in payload["shared_contracts"]
        if row["contract_id"] == "ExceptionReceipt"
    )
    assert exception_contract["cross_links"]
    assert exception_contract["cross_links"][0]["target_contract"] == "FindingBacklog"


def test_platform_contracts_markdown_output(capsys) -> None:
    exit_code = platform_contracts.run(_build_args(format="md"))
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "# devctl platform-contracts" in output
    assert "## Shared Contracts" in output
    assert "## Artifact Schema Matrix" in output
    assert "## Service Lifecycle" in output
    assert "## Caller Authority" in output
    assert "RepoPack" in output
    assert "Current Portability Status" in output


def test_platform_contracts_json_output_path_emits_receipt() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "platform.json"
        args = Namespace(
            format="json",
            output=str(output_path),
            pipe_command=None,
            pipe_args=None,
        )
        stdout = StringIO()
        with redirect_stdout(stdout):
            exit_code = platform_contracts.run(args)
        payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    receipt = json.loads(stdout.getvalue().strip())
    assert receipt["command"] == "platform-contracts"
    assert receipt["artifact"]["path"] == str(output_path)
    assert payload["command"] == "platform-contracts"
