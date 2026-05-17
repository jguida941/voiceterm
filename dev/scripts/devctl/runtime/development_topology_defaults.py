"""Default topology assembly for typed development mode."""

from __future__ import annotations

from .development_core_workstreams import core_workstreams
from .development_learning_workstreams import learning_workstreams
from .development_scaling_defaults import build_development_scaling_contract
from .development_team import (
    DevelopmentExternalResearchContract,
    DevelopmentKnowledgeFlowContract,
    DevelopmentLearningContract,
    DevelopmentModeTopology,
    DevelopmentRoutingContract,
)

GLOBAL_ROUTING = DevelopmentRoutingContract(
    route_sources=(
        "StartupContext",
        "WorkIntakePacket",
        "PlanningIRSnapshot",
        "FindingBacklog",
        "AgentSyncProjection",
        "AuthoritySnapshot",
        "AgentDispatchRouter",
        "SystemMapSnapshot",
        "ContextGraphSnapshot",
        "ConceptIndex",
        "PointerRefIndex",
        "KnowledgeSynthesisRecord",
        "ExternalSourceEvidence",
        "PacketLifecycleHistory",
        "PacketOutcomeLedger",
        "PacketContinuityIndex",
        "PacketCreationBinding",
        "PacketDurableIngestionReceipt",
        "PacketDebtRemediationReport",
    ),
    selection_signals=(
        "top_blocker",
        "implementation_permission",
        "active_target",
        "next_best_slices",
        "open_findings",
        "packet_priority",
        "safe_to_fanout",
        "graph_freshness",
        "coverage_gaps",
        "source_confidence",
        "synthesis_ready",
        "prevention_available",
        "packet_has_plan_or_finding_intent",
        "missing_durable_packet_provenance",
        "outcome_promoted_without_durable_row",
        "clock_expired_without_durable_owner",
    ),
    graph_views=(
        "context-graph --mode bootstrap",
        "context-graph --query <contract-or-file>",
        "system-map --format md",
        "graph-walk from CommandRunPlan",
        "ConceptIndex / ZGraph-compatible generated view",
        "PointerRefIndex cited traversal view",
    ),
    dispatch_contracts=(
        "CommandModeRequest",
        "CommandRunPlan",
        "AgentDispatchRoute",
        "AgentLoopDecision",
        "MutationLease",
        "ResearchRouteGrant",
        "KnowledgePromotionDecision",
        "PacketDisposition",
        "PacketContinuityState",
        "PacketCreationBinding",
        "PacketDurableIngestionReceipt",
        "PacketDebtRemediationReport",
    ),
    fail_closed_when=(
        "runtime evidence is stale or missing",
        "AgentDispatchRouter reports ambiguous session authority",
        "selected work has no plan/finding owner",
        "graph snapshot is stale and no refresh is available",
        "mutation is requested without a session-bound lease",
        "external source evidence lacks provenance or confidence",
        "graph/pointer output is treated as authority instead of projection",
        "packet-carried work has no durable plan/finding/guard/knowledge owner",
        "packet outcome claims promotion but no typed owner cites the packet id",
    ),
)
LEARNING_LOOP = DevelopmentLearningContract(
    issue_sources=(
        "FindingBacklog",
        "review-channel finding packets",
        "dogfood failures",
        "guard/probe failures",
        "runtime watcher stale-state reports",
        "system-map connectivity gaps",
        "external research evidence",
        "context-graph/pointer coverage gaps",
        "packet outcome without durable typed owner",
        "packet-carried plan/finding/guard intent before ingestion",
    ),
    pattern_outputs=(
        "PatternObservation",
        "findings-priority cluster",
        "PlanFindingMismatchRecord",
        "KnowledgeSynthesisRecord",
        "ContextGraphSeed",
        "PacketIngestionGapReport",
    ),
    prevention_outputs=(
        "GuardPromotionCandidate",
        "GuardSmartnessReport",
        "red_team_fixture_result",
        "PlanRow",
        "CandidateInvariant",
        "PointerRefIndexEntry",
        "PacketDurableIngestionReceipt",
    ),
    prompt_inputs=(
        "next_session_prompt",
        "WorkIntakePacket.active_target",
        "SessionPacingState.focus_slice_id",
        "pending GuardPromotionCandidate",
        "ContextPack",
        "KnowledgeSynthesisRecord",
        "PacketDurableIngestionReceipt",
    ),
    success_metrics=(
        "fewer repeated pattern findings",
        "promotion candidate became a real guard/probe/policy check",
        "red-team replay passes",
        "false-positive rate does not rise",
        "context-graph diff shows fewer disconnected patterns",
        "synthesized knowledge appears in startup/context graph queries",
        "packet-carried work has durable typed ownership before TTL expiry",
    ),
)
EXTERNAL_RESEARCH = DevelopmentExternalResearchContract(
    route_grant_required=True,
    allowed_sources=(
        "official documentation",
        "standards documents",
        "release notes and changelogs",
        "primary source repositories",
        "research papers",
        "adopter repo evidence",
        "operator-approved web search results",
    ),
    required_evidence=(
        "source_url_or_repo_ref",
        "retrieved_at",
        "source_kind",
        "confidence",
        "claim_summary",
        "affected_contract_or_plan_ref",
    ),
    synthesis_inputs=("ResearchEvidenceBundle", "ExternalSourceEvidence", "ContextGraphSnapshot", "SystemMapSnapshot", "PlanRow"),
    blocked_uses=(
        "web_search_without_route_grant",
        "uncited_claim_in_plan_or_guard",
        "external_source_as_runtime_authority",
        "vendor_default_as_mutation_authority",
    ),
)
KNOWLEDGE_FLOW = DevelopmentKnowledgeFlowContract(
    artifact_inputs=(
        "ResearchEvidenceBundle",
        "ExternalSourceEvidence",
        "PatternObservation",
        "FindingReview",
        "GuardSmartnessReport",
        "DogfoodRun",
        "RunRecord",
    ),
    canonical_sinks=(
        "MasterPlanStore",
        "FindingBacklog",
        "GuardPromotionQueue",
        "PlatformContractRegistry",
        "SystemCatalog",
    ),
    generated_projections=("ContextGraphSnapshot", "SystemMapSnapshot", "ContextPack", "StartupContext", "DevSessionPack"),
    pointer_surfaces=(
        "PointerRefIndex",
        "ConceptIndex",
        "ZGraph-compatible generated encoding",
        "context-graph query refs",
    ),
    graph_consumers=(
        "context-graph bootstrap/query/diff",
        "graph-walk",
        "system-map connectivity registry",
        "check_runtime_spine_closure",
        "check_platform_contracts",
        "develop next",
    ),
    promotion_gates=(
        "typed provenance present",
        "canonical owner selected",
        "guard/probe replay available when prevention is claimed",
        "plan row or contract row exists before enforcement",
        "generated projections rebuilt from canonical sinks",
    ),
    forbidden_uses=(
        "graph_as_authority_store",
        "pointer_ref_without_canonical_target",
        "chat_memory_as_knowledge_sink",
        "uncited_external_claim_as_guard_rule",
    ),
)


def build_default_development_topology() -> DevelopmentModeTopology:
    """Return the default topology for typed development mode."""
    return DevelopmentModeTopology(
        topology_id="develop-default",
        assignment_policy=(
            "A workstream occupant is selected from actor identity, current "
            "session, AuthoritySnapshot grants, packet route, occupied_lane, "
            "AgentDispatchRouter output, and mutation lease state; a provider "
            "name never grants authority."
        ),
        provider_policy=(
            "Codex, Claude, Cursor, future agents, or humans may occupy any "
            "workstream when typed policy grants that workstream's authority."
        ),
        mutation_policy=(
            "Exactly one Builder may own live-tree mutation at a time, and "
            "only inside a current session-bound mutation lease."
        ),
        global_routing=GLOBAL_ROUTING,
        learning_loop=LEARNING_LOOP,
        external_research=EXTERNAL_RESEARCH,
        knowledge_flow=KNOWLEDGE_FLOW,
        scaling=build_development_scaling_contract(),
        workstreams=(*core_workstreams(), *learning_workstreams()),
    )


__all__ = ["build_default_development_topology"]
