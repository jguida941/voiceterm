"""Typed contract stubs promoted from the R98 packet-ingest mandate."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class LifecycleReceipt:
    receipt_kind: str
    actor: str
    executed_at_utc: str
    evidence_ref: str
    proof_summary: str
    schema_version: int = 1
    contract_id: str = "LifecycleReceipt"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FeatureLifecycleProof:
    feature_id: str
    commit_sha: str
    receipts: tuple[LifecycleReceipt, ...]
    completeness_score: float
    missing_receipt_kinds: tuple[str, ...]
    schema_version: int = 1
    contract_id: str = "FeatureLifecycleProof"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["receipts"] = [receipt.to_dict() for receipt in self.receipts]
        payload["missing_receipt_kinds"] = list(self.missing_receipt_kinds)
        return payload


@dataclass(frozen=True, slots=True)
class RoleCapability:
    capability_id: str
    role_id: str
    command_refs: tuple[str, ...]
    authority_scope: str
    evidence_required: tuple[str, ...]
    schema_version: int = 1
    contract_id: str = "RoleCapability"


@dataclass(frozen=True, slots=True)
class RoleCapabilityRegistry:
    registry_id: str
    capabilities: tuple[RoleCapability, ...]
    source_refs: tuple[str, ...]
    missing_capability_count: int
    schema_version: int = 1
    contract_id: str = "RoleCapabilityRegistry"


@dataclass(frozen=True, slots=True)
class ToggleReceipt:
    toggle_id: str
    mode_axis: str
    previous_state: str
    new_state: str
    actor: str
    changed_at_utc: str
    evidence_ref: str
    invariant_scope: str
    schema_version: int = 1
    contract_id: str = "ToggleReceipt"


@dataclass(frozen=True, slots=True)
class ModeChangeReceipt:
    mode_axis: str
    previous_mode: str
    new_mode: str
    actor: str
    changed_at_utc: str
    evidence_ref: str
    gate_effect: str
    schema_version: int = 1
    contract_id: str = "ModeChangeReceipt"


@dataclass(frozen=True, slots=True)
class AgentMindConsumptionReceipt:
    consumer_actor: str
    provider_agent: str
    consumed_at_utc: str
    cursor: str
    event_count: int
    derived_actions: tuple[str, ...]
    schema_version: int = 1
    contract_id: str = "AgentMindConsumptionReceipt"


@dataclass(frozen=True, slots=True)
class StalledQueueFinding:
    finding_id: str
    row_id: str
    queued_since_utc: str
    age_days: int
    priority: str
    recommended_action: str
    schema_version: int = 1
    contract_id: str = "StalledQueueFinding"


@dataclass(frozen=True, slots=True)
class QueueBypassReasoning:
    row_id: str
    bypass_reason: str
    actor: str
    decided_at_utc: str
    expires_at_utc: str
    evidence_ref: str
    schema_version: int = 1
    contract_id: str = "QueueBypassReasoning"


@dataclass(frozen=True, slots=True)
class PacketReadReceipt:
    packet_id: str
    reader_actor: str
    read_at_utc: str
    body_hash: str
    source_ref: str
    schema_version: int = 1
    contract_id: str = "PacketReadReceipt"


@dataclass(frozen=True, slots=True)
class PacketUrgencyClassification:
    packet_id: str
    urgency: str
    classified_at_utc: str
    classifier_actor: str
    rationale: str
    schema_version: int = 1
    contract_id: str = "PacketUrgencyClassification"


@dataclass(frozen=True, slots=True)
class PacketSupersessionLink:
    packet_id: str
    supersedes_packet_ids: tuple[str, ...]
    superseded_by_packet_id: str
    rationale: str
    schema_version: int = 1
    contract_id: str = "PacketSupersessionLink"


@dataclass(frozen=True, slots=True)
class RelationshipGraph:
    graph_id: str
    node_refs: tuple[str, ...]
    edge_refs: tuple[str, ...]
    generated_at_utc: str
    source_refs: tuple[str, ...]
    schema_version: int = 1
    contract_id: str = "RelationshipGraph"


@dataclass(frozen=True, slots=True)
class PacketADRReceipt:
    packet_id: str
    decision_id: str
    precedent_packet_ids: tuple[str, ...]
    status: str
    rationale: str
    schema_version: int = 1
    contract_id: str = "PacketADRReceipt"


@dataclass(frozen=True, slots=True)
class CharterDelivery:
    charter_id: str
    contract_ids: tuple[str, ...]
    delivered_at_utc: str
    evidence_refs: tuple[str, ...]
    schema_version: int = 1
    contract_id: str = "CharterDelivery"


@dataclass(frozen=True, slots=True)
class WorkflowStep:
    capability_id: str
    execution_order: int
    requires_agent_mind_signal: tuple[str, ...]
    produces_typed_evidence_kinds: tuple[str, ...]
    schema_version: int = 1
    contract_id: str = "WorkflowStep"


@dataclass(frozen=True, slots=True)
class AgentWorkflowSpec:
    workflow_id: str
    target_role_id: str
    command_sequence: tuple[WorkflowStep, ...]
    coordination_with: tuple[str, ...]
    user_customization_points: tuple[str, ...]
    schema_version: int = 1
    contract_id: str = "AgentWorkflowSpec"


@dataclass(frozen=True, slots=True)
class ContinuousImprovementMode:
    mode_id: str
    enabled: bool
    scan_commands: tuple[str, ...]
    promotion_rules: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    schema_version: int = 1
    contract_id: str = "ContinuousImprovementMode"


@dataclass(frozen=True, slots=True)
class RuntimeErrorReceipt:
    error_id: str
    error_class: str
    source_path: str
    occurred_at_utc: str
    finding_ref: str
    traceback_ref: str
    schema_version: int = 1
    contract_id: str = "RuntimeErrorReceipt"


@dataclass(frozen=True, slots=True)
class TypedOutputHumanSummary:
    output_ref: str
    human_summary: str
    ok: bool
    risk: str
    generated_at_utc: str
    schema_version: int = 1
    contract_id: str = "TypedOutputHumanSummary"


@dataclass(frozen=True, slots=True)
class ContractRef:
    contract_id_ref: str
    schema_version_ref: int
    owner_path: str
    relation: str
    schema_version: int = 1
    contract_id: str = "ContractRef"


@dataclass(frozen=True, slots=True)
class ComposesWith:
    source_contract_id: str
    target_contract_id: str
    composition_kind: str
    compatibility_rule: str
    evidence_ref: str
    schema_version: int = 1
    contract_id: str = "ComposesWith"


@dataclass(frozen=True, slots=True)
class AssistantGuideMode:
    mode_id: str
    enabled: bool
    guide_surface_refs: tuple[str, ...]
    context_resolver_ref: str
    evidence_ref: str
    schema_version: int = 1
    contract_id: str = "AssistantGuideMode"


@dataclass(frozen=True, slots=True)
class PlatformGuide:
    guide_id: str
    source_contract_refs: tuple[str, ...]
    generated_at_utc: str
    surface_refs: tuple[str, ...]
    freshness_ref: str
    schema_version: int = 1
    contract_id: str = "PlatformGuide"


@dataclass(frozen=True, slots=True)
class GovernanceCompatibilityClaim:
    invariant_id: str
    claim_status: str
    evidence_ref: str
    schema_version: int = 1
    contract_id: str = "GovernanceCompatibilityClaim"


@dataclass(frozen=True, slots=True)
class SkillManifest:
    skill_id: str
    skill_name: str
    source: str
    version: str
    declared_capabilities: tuple[str, ...]
    declared_governance_compatibility: tuple[GovernanceCompatibilityClaim, ...]
    skill_entry_point: str
    validation_status: str
    schema_version: int = 1
    contract_id: str = "SkillManifest"


@dataclass(frozen=True, slots=True)
class SkillLoadReceipt:
    skill_id: str
    load_outcome: str
    governance_check_findings: tuple[str, ...]
    actor: str
    loaded_at_utc: str
    expiry_at_utc: str
    schema_version: int = 1
    contract_id: str = "SkillLoadReceipt"


@dataclass(frozen=True, slots=True)
class SkillCompatibilityValidator:
    validator_id: str
    skill_id: str
    invariant_refs: tuple[str, ...]
    verdict: str
    findings: tuple[str, ...]
    schema_version: int = 1
    contract_id: str = "SkillCompatibilityValidator"


@dataclass(frozen=True, slots=True)
class MandatoryIngestBeforeImplementInvariant:
    invariant_id: str
    required_mapping_store: str
    enforcement_surface: str
    toggle_scope: str
    severity_policy: str
    schema_version: int = 1
    contract_id: str = "MandatoryIngestBeforeImplementInvariant"


@dataclass(frozen=True, slots=True)
class PacketPlanIngestionMapping:
    packet_id: str
    plan_row_id: str
    mapped_at_utc: str
    actor: str
    source_hash: str
    schema_version: int = 1
    contract_id: str = "PacketPlanIngestionMapping"
