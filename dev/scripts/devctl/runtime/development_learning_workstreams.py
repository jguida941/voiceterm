"""Learning, quality, watcher, and operator workstreams for development mode."""

from __future__ import annotations

from .development_team import (
    DevelopmentAuthorityRequirement,
    DevelopmentEvidenceContract,
    DevelopmentRoutingContract,
    DevelopmentWorkstreamSpec,
)

KNOWLEDGE_SYNTHESIZER_WORKSTREAM = DevelopmentWorkstreamSpec(
    workstream_id="knowledge_synthesizer",
    display_name="Knowledge Synthesizer",
    aliases=("synthesis", "knowledge", "graph-curator", "pointer"),
    runtime_role="subagent",
    plain_language=(
        "turns cited evidence into durable graph, pointer, plan, and guard "
        "inputs without making projections authoritative"
    ),
    phases=("synthesis", "promotion", "projection_refresh"),
    mutation_policy="typed_artifact_only",
    authority=DevelopmentAuthorityRequirement(
        capabilities=("knowledge.synthesize", "pattern.record", "context.write"),
    ),
    evidence=DevelopmentEvidenceContract(
        reads=(
            "ResearchEvidenceBundle",
            "ExternalSourceEvidence",
            "PatternObservation",
            "FindingReview",
            "ContextGraphSnapshot",
            "SystemMapSnapshot",
        ),
        writes=(
            "KnowledgeSynthesisRecord",
            "ContextGraphSeed",
            "PointerRefIndexEntry",
            "GuardPromotionCandidate",
            "PlanRow",
        ),
        emits_packets=("plan_gap_review", "guard_candidate", "system_notice"),
        visible_in=("context-graph", "system-map", "develop next", "startup-context"),
    ),
    routing=DevelopmentRoutingContract(
        route_sources=(
            "ResearchEvidenceBundle",
            "FindingBacklog",
            "ContextGraphSnapshot",
            "SystemMapSnapshot",
            "ConceptIndex",
            "PointerRefIndex",
        ),
        selection_signals=(
            "source_confidence",
            "recurrence_risk",
            "missing_pointer_target",
            "coverage_gap",
            "promotion_ready",
        ),
        graph_views=(
            "context-graph --query <artifact>",
            "ConceptIndex / ZGraph-compatible generated view",
            "PointerRefIndex cited traversal view",
        ),
        dispatch_contracts=("KnowledgeSynthesisRecord", "KnowledgePromotionDecision"),
        fail_closed_when=(
            "source evidence is uncited",
            "canonical sink is not named",
            "projection would become a source of truth",
        ),
    ),
    allowed_actions=("record_synthesis", "route_guard_candidate", "route_plan_gap", "refresh_generated_projection"),
    blocked_actions=("promote_uncited_research", "make_graph_authority", "store_architecture_in_chat"),
)

ARCHITECT_WORKSTREAM = DevelopmentWorkstreamSpec(
    workstream_id="architect",
    display_name="Architect",
    aliases=("architect", "design"),
    runtime_role="reviewer",
    plain_language="turns repeated patterns into contracts and plan structure",
    phases=("pattern_detection", "contract_design", "plan_alignment"),
    mutation_policy="read_only",
    authority=DevelopmentAuthorityRequirement(
        capabilities=("architecture.review", "pattern.record"),
    ),
    evidence=DevelopmentEvidenceContract(
        reads=(
            "FindingBacklog",
            "PatternObservation",
            "KnowledgeSynthesisRecord",
            "ContextGraphSnapshot",
            "PointerRefIndex",
        ),
        writes=("PatternObservation", "PlanRow", "architecture_decision"),
        emits_packets=("plan_gap_review", "decision", "finding"),
        visible_in=("findings-priority", "system-picture", "develop next"),
    ),
    routing=DevelopmentRoutingContract(
        route_sources=("findings-priority", "context-graph", "PlanningIRSnapshot", "KnowledgeSynthesisRecord"),
        selection_signals=("cluster_confidence", "plan_finding_mismatch", "hot_path_count", "knowledge_gap"),
        graph_views=("context-graph --mode diff", "system-map connectivity registry", "PointerRefIndex cited traversal view"),
        dispatch_contracts=("PatternObservation", "PlanRow"),
        fail_closed_when=("pattern has no named consumer",),
    ),
    allowed_actions=("record_pattern", "propose_contract", "route_plan_gap"),
    blocked_actions=("change_runtime_authority_without_plan_row",),
)

QUALITY_ENGINEER_WORKSTREAM = DevelopmentWorkstreamSpec(
    workstream_id="quality_engineer",
    display_name="Quality Engineer",
    aliases=("quality", "guard", "probe"),
    runtime_role="reviewer",
    plain_language="proves guards and probes are precise, useful, and replayable",
    phases=("guard_audit", "probe_audit", "red_team"),
    mutation_policy="fixture_only",
    authority=DevelopmentAuthorityRequirement(capabilities=("guard.audit", "probe.audit")),
    evidence=DevelopmentEvidenceContract(
        reads=("GuardPromotionCandidate", "QualityFeedbackSnapshot"),
        writes=("GuardSmartnessReport", "red_team_fixture_result"),
        emits_packets=("finding", "guard_evidence"),
        visible_in=("governance-quality-feedback", "develop audit-guards"),
    ),
    routing=DevelopmentRoutingContract(
        route_sources=("governance-quality-feedback", "guard promotion queue"),
        selection_signals=("false_positive_rate", "cleanup_rate", "recurrence_risk"),
        dispatch_contracts=("GuardSmartnessReport", "GuardPromotionCandidate"),
        fail_closed_when=("promotion candidate has no replay fixture",),
    ),
    allowed_actions=("seed_fixture", "run_probe", "score_rule"),
    blocked_actions=("promote_without_replay", "hide_false_positive"),
)

DOGFOOD_TESTER_WORKSTREAM = DevelopmentWorkstreamSpec(
    workstream_id="dogfood_tester",
    display_name="Dogfood Tester",
    aliases=("dogfood", "scenario"),
    runtime_role="dashboard",
    plain_language="runs real workflows and records where the platform breaks",
    phases=("scenario", "evidence_capture", "finding_intake"),
    mutation_policy="read_only_by_default",
    authority=DevelopmentAuthorityRequirement(
        capabilities=("dogfood.record", "runtime.observe"),
    ),
    evidence=DevelopmentEvidenceContract(
        reads=("DogfoodScenarioReport", "CommandRunPlan", "AgentSyncProjection"),
        writes=("DogfoodRun", "FindingReview"),
        emits_packets=("finding", "blocked", "question"),
        visible_in=("dogfood", "governance-review", "develop status"),
    ),
    routing=DevelopmentRoutingContract(
        route_sources=("CommandRunPlan", "DogfoodScenarioReport", "AgentSyncProjection"),
        selection_signals=("scenario_id", "packet_outcome", "command_result"),
        dispatch_contracts=("FindingBacklog", "GuardPromotionCandidate"),
        fail_closed_when=("dogfood result cannot be linked to command/packet/role"),
    ),
    allowed_actions=("run_scenario", "record_failure", "record_success"),
    blocked_actions=("treat_dogfood_as_supervisor",),
)

RUNTIME_WATCHER_WORKSTREAM = DevelopmentWorkstreamSpec(
    workstream_id="runtime_watcher",
    display_name="Runtime Watcher",
    aliases=("watcher", "observer", "dashboard"),
    runtime_role="dashboard",
    plain_language="watches packets, sync status, stale actors, and drift",
    phases=("observe", "wake", "blocker_detection"),
    mutation_policy="read_only",
    authority=DevelopmentAuthorityRequirement(capabilities=("runtime.observe", "packet.observe")),
    evidence=DevelopmentEvidenceContract(
        reads=("AgentSyncProjection", "ControlPlaneReadModel", "DashboardSnapshot"),
        writes=("stale_state_report", "wake_recommendation"),
        emits_packets=("blocked", "question", "system_notice"),
        visible_in=("sync-status", "dashboard", "mobile", "develop status"),
    ),
    routing=DevelopmentRoutingContract(
        route_sources=("sync-status --since-event-id", "ControlPlaneReadModel"),
        selection_signals=("stale_seconds", "awaiting_packet_ids", "changed"),
        dispatch_contracts=("AgentSyncProjection", "NextLaneGate"),
        fail_closed_when=("actor activity is inferred only from partner wait state",),
    ),
    allowed_actions=("observe_delta", "recommend_wake", "report_stale"),
    blocked_actions=("infer_activity_from_partner_wait",),
)

OPERATOR_WORKSTREAM = DevelopmentWorkstreamSpec(
    workstream_id="operator",
    display_name="Operator",
    aliases=("operator", "approver", "remote"),
    runtime_role="operator",
    plain_language="approves privileged actions and resolves policy overrides",
    phases=("approval", "override", "publication"),
    mutation_policy="approval_only",
    authority=DevelopmentAuthorityRequirement(
        capabilities=("approval.commit", "approval.push", "override.approve"),
        approval_packet_required=True,
    ),
    evidence=DevelopmentEvidenceContract(
        reads=("approval_request", "OverrideReceipt", "GuardProfile"),
        writes=("approval_packet", "OverrideReceipt"),
        emits_packets=("approval_request", "decision"),
        visible_in=("operator-inbox", "dashboard", "develop status"),
    ),
    routing=DevelopmentRoutingContract(
        route_sources=("operator-inbox", "OverrideReceipt", "CommandRunPlan"),
        selection_signals=("approval_required", "override_type", "risk_level"),
        dispatch_contracts=("OverrideReceipt", "PacketDisposition"),
        fail_closed_when=("approval is chat-only or lacks expiry/scope"),
    ),
    allowed_actions=("approve", "deny", "request_more_evidence"),
    blocked_actions=("edit_files_by_approval_label", "grant_repo_write_without_lease"),
)


def learning_workstreams() -> tuple[DevelopmentWorkstreamSpec, ...]:
    return (
        KNOWLEDGE_SYNTHESIZER_WORKSTREAM,
        ARCHITECT_WORKSTREAM,
        QUALITY_ENGINEER_WORKSTREAM,
        DOGFOOD_TESTER_WORKSTREAM,
        RUNTIME_WATCHER_WORKSTREAM,
        OPERATOR_WORKSTREAM,
    )


__all__ = ["learning_workstreams"]
