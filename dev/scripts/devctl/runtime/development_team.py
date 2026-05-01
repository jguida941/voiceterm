"""Typed `/develop` topology and routing contracts.

The development controller is not a fixed team roster. It is a compiler from a
developer request to typed work routing:

``request -> graph/system discovery -> plan/finding slice -> authority route
-> workstream assignment -> evidence -> learning feedback``.

This file names the user-facing workstreams and the machine contracts that make
them safe. Provider names are deliberately compatibility labels only; Codex,
Claude, future agents, and humans can occupy any workstream when typed runtime
authority grants the matching capabilities for the current session.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

DEVELOPMENT_MODE_CONTRACT_ID = "DevelopmentModeTopology"
DEVELOPMENT_MODE_SCHEMA_VERSION = 1
DEVELOPMENT_TEAM_CONTRACT_ID = DEVELOPMENT_MODE_CONTRACT_ID


@dataclass(frozen=True, slots=True)
class DevelopmentAuthorityRequirement:
    """Typed proof required before an actor may occupy a workstream."""

    capabilities: tuple[str, ...] = ()
    lease_kind: str = "none"
    exclusive: bool = False
    approval_packet_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["capabilities"] = list(self.capabilities)
        return payload


@dataclass(frozen=True, slots=True)
class DevelopmentEvidenceContract:
    """Typed read/write/packet contract for one workstream."""

    reads: tuple[str, ...] = ()
    writes: tuple[str, ...] = ()
    emits_packets: tuple[str, ...] = ()
    visible_in: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in ("reads", "writes", "emits_packets", "visible_in"):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True, slots=True)
class DevelopmentRoutingContract:
    """How `/develop` decides where work goes."""

    route_sources: tuple[str, ...]
    selection_signals: tuple[str, ...]
    graph_views: tuple[str, ...] = ()
    dispatch_contracts: tuple[str, ...] = ()
    fail_closed_when: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "route_sources",
            "selection_signals",
            "graph_views",
            "dispatch_contracts",
            "fail_closed_when",
        ):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True, slots=True)
class DevelopmentLearningContract:
    """How issues become future prevention instead of chat memory."""

    issue_sources: tuple[str, ...]
    pattern_outputs: tuple[str, ...]
    prevention_outputs: tuple[str, ...]
    prompt_inputs: tuple[str, ...]
    success_metrics: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "issue_sources",
            "pattern_outputs",
            "prevention_outputs",
            "prompt_inputs",
            "success_metrics",
        ):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True, slots=True)
class DevelopmentExternalResearchContract:
    """Boundaries for web/vendor/library research in development mode."""

    route_grant_required: bool
    allowed_sources: tuple[str, ...]
    required_evidence: tuple[str, ...]
    synthesis_inputs: tuple[str, ...]
    blocked_uses: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "allowed_sources",
            "required_evidence",
            "synthesis_inputs",
            "blocked_uses",
        ):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True, slots=True)
class DevelopmentKnowledgeFlowContract:
    """How durable knowledge artifacts feed graph, plan, and guard systems."""

    artifact_inputs: tuple[str, ...]
    canonical_sinks: tuple[str, ...]
    generated_projections: tuple[str, ...]
    pointer_surfaces: tuple[str, ...]
    graph_consumers: tuple[str, ...]
    promotion_gates: tuple[str, ...]
    forbidden_uses: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "artifact_inputs",
            "canonical_sinks",
            "generated_projections",
            "pointer_surfaces",
            "graph_consumers",
            "promotion_gates",
            "forbidden_uses",
        ):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True, slots=True)
class DevelopmentWorkstreamSpec:
    """One user-facing job mapped to typed runtime authority and routing."""

    workstream_id: str
    display_name: str
    aliases: tuple[str, ...]
    runtime_role: str
    plain_language: str
    phases: tuple[str, ...]
    mutation_policy: str
    authority: DevelopmentAuthorityRequirement
    evidence: DevelopmentEvidenceContract
    routing: DevelopmentRoutingContract
    allowed_actions: tuple[str, ...] = ()
    blocked_actions: tuple[str, ...] = ()
    assignment_rule: str = "any_actor_with_matching_authority"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["aliases"] = list(self.aliases)
        payload["phases"] = list(self.phases)
        payload["authority"] = self.authority.to_dict()
        payload["evidence"] = self.evidence.to_dict()
        payload["routing"] = self.routing.to_dict()
        payload["allowed_actions"] = list(self.allowed_actions)
        payload["blocked_actions"] = list(self.blocked_actions)
        return payload


@dataclass(frozen=True, slots=True)
class DevelopmentModeTopology:
    """Provider-neutral `/develop` topology."""

    topology_id: str
    workstreams: tuple[DevelopmentWorkstreamSpec, ...]
    global_routing: DevelopmentRoutingContract
    learning_loop: DevelopmentLearningContract
    external_research: DevelopmentExternalResearchContract
    knowledge_flow: DevelopmentKnowledgeFlowContract
    assignment_policy: str
    provider_policy: str
    mutation_policy: str
    default_worker_fanout: int = 0
    schema_version: int = DEVELOPMENT_MODE_SCHEMA_VERSION
    contract_id: str = DEVELOPMENT_MODE_CONTRACT_ID

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "schema_version": self.schema_version,
            "topology_id": self.topology_id,
            "assignment_policy": self.assignment_policy,
            "provider_policy": self.provider_policy,
            "mutation_policy": self.mutation_policy,
            "default_worker_fanout": self.default_worker_fanout,
            "global_routing": self.global_routing.to_dict(),
            "learning_loop": self.learning_loop.to_dict(),
            "external_research": self.external_research.to_dict(),
            "knowledge_flow": self.knowledge_flow.to_dict(),
            "workstreams": [item.to_dict() for item in self.workstreams],
        }


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
        global_routing=_global_routing(),
        learning_loop=_learning_loop(),
        external_research=_external_research(),
        knowledge_flow=_knowledge_flow(),
        workstreams=(
            _coordinator(),
            _builder(),
            _reviewer(),
            _plan_intake_steward(),
            _researcher(),
            _knowledge_synthesizer(),
            _architect(),
            _quality_engineer(),
            _dogfood_tester(),
            _runtime_watcher(),
            _operator(),
        ),
    )


def _global_routing() -> DevelopmentRoutingContract:
    return DevelopmentRoutingContract(
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
            "PacketDurableIngestionReceipt",
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
            "PacketDurableIngestionReceipt",
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


def _learning_loop() -> DevelopmentLearningContract:
    return DevelopmentLearningContract(
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


def _external_research() -> DevelopmentExternalResearchContract:
    return DevelopmentExternalResearchContract(
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
        synthesis_inputs=(
            "ResearchEvidenceBundle",
            "ExternalSourceEvidence",
            "ContextGraphSnapshot",
            "SystemMapSnapshot",
            "PlanRow",
        ),
        blocked_uses=(
            "web_search_without_route_grant",
            "uncited_claim_in_plan_or_guard",
            "external_source_as_runtime_authority",
            "vendor_default_as_mutation_authority",
        ),
    )


def _knowledge_flow() -> DevelopmentKnowledgeFlowContract:
    return DevelopmentKnowledgeFlowContract(
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
        generated_projections=(
            "ContextGraphSnapshot",
            "SystemMapSnapshot",
            "ContextPack",
            "StartupContext",
            "DevSessionPack",
        ),
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


def _coordinator() -> DevelopmentWorkstreamSpec:
    return DevelopmentWorkstreamSpec(
        workstream_id="coordinator",
        display_name="Coordinator",
        aliases=("conductor", "coordinator"),
        runtime_role="dashboard",
        plain_language="chooses the next bounded step and routes packets",
        phases=("intake", "slice_selection", "phase_selection"),
        mutation_policy="read_only",
        authority=DevelopmentAuthorityRequirement(
            capabilities=("runtime.observe", "plan.select", "packet.route"),
        ),
        evidence=DevelopmentEvidenceContract(
            reads=(
                "StartupContext",
                "ControlPlaneReadModel",
                "PlanningIRSnapshot",
                "AgentSyncProjection",
            ),
            writes=("DevelopmentLoopReport", "CommandRunPlan"),
            emits_packets=("instruction", "question", "blocked"),
            visible_in=("develop status", "dashboard", "claude-loop"),
        ),
        routing=DevelopmentRoutingContract(
            route_sources=("WorkIntakePacket", "PlanningIRSnapshot", "AgentDispatchRouter"),
            selection_signals=("top_blocker", "next_best_slices", "safe_to_fanout"),
            dispatch_contracts=("CommandRunPlan", "AgentDispatchRoute"),
            fail_closed_when=("no selected plan/finding owner",),
        ),
        allowed_actions=("select_next_slice", "route_packet", "pause", "resume"),
        blocked_actions=("edit_files", "stage", "commit", "push"),
    )


def _builder() -> DevelopmentWorkstreamSpec:
    return DevelopmentWorkstreamSpec(
        workstream_id="builder",
        display_name="Builder",
        aliases=("implementer", "coder", "editor"),
        runtime_role="implementer",
        plain_language="owns scoped code changes when a mutation lease exists",
        phases=("implement", "test", "handoff"),
        mutation_policy="exclusive_live_tree_lease",
        authority=DevelopmentAuthorityRequirement(
            capabilities=("repo.stage", "repo.commit"),
            lease_kind="live_tree",
            exclusive=True,
            approval_packet_required=True,
        ),
        evidence=DevelopmentEvidenceContract(
            reads=("AgentDispatchRoute", "MutationLease", "GuardProfile"),
            writes=("source_diff", "RunRecord", "completion_packet"),
            emits_packets=("handoff", "action_request", "guard_evidence"),
            visible_in=("agent-sync", "agent work-board", "develop status"),
        ),
        routing=DevelopmentRoutingContract(
            route_sources=("AgentDispatchRouter", "AuthoritySnapshot", "MutationLease"),
            selection_signals=("required_capabilities", "path_scope", "target_revision"),
            dispatch_contracts=("AgentDispatchRoute", "AgentLoopDecision"),
            fail_closed_when=("lease is absent", "path scope overlaps another live writer"),
        ),
        allowed_actions=("edit_files", "run_checks", "prepare_handoff"),
        blocked_actions=("edit_without_lease", "self_accept_review", "push"),
    )


def _reviewer() -> DevelopmentWorkstreamSpec:
    return DevelopmentWorkstreamSpec(
        workstream_id="reviewer",
        display_name="Reviewer",
        aliases=("reviewer", "review"),
        runtime_role="reviewer",
        plain_language="accepts or rejects changes, packets, and guard proof",
        phases=("review", "acceptance", "blocker_resolution"),
        mutation_policy="read_only",
        authority=DevelopmentAuthorityRequirement(
            capabilities=("review.finding", "review.checkpoint", "review.accept"),
        ),
        evidence=DevelopmentEvidenceContract(
            reads=("completion_packet", "RunRecord", "GuardSmartnessReport"),
            writes=("review_packet", "FindingReview"),
            emits_packets=("finding", "decision", "approval_request"),
            visible_in=("review-channel status", "dashboard", "develop status"),
        ),
        routing=DevelopmentRoutingContract(
            route_sources=("AgentSyncProjection", "packet lifecycle", "RunRecord"),
            selection_signals=("completion_packet", "guard_attestation", "open_findings"),
            dispatch_contracts=("PacketDisposition", "FindingReview"),
            fail_closed_when=("completion lacks guard evidence",),
        ),
        allowed_actions=("review", "record_finding", "accept", "request_changes"),
        blocked_actions=("edit_reviewed_diff", "grant_mutation_by_role_label"),
    )


def _plan_intake_steward() -> DevelopmentWorkstreamSpec:
    return DevelopmentWorkstreamSpec(
        workstream_id="plan_intake_steward",
        display_name="Plan Intake Steward",
        aliases=(
            "intake",
            "plan-ingest",
            "state-ingest",
            "packet-ingest",
            "provenance",
            "packet",
        ),
        runtime_role="dashboard",
        plain_language=(
            "promotes packet-carried work into durable plan, finding, guard, "
            "and knowledge state with packet ids kept as provenance"
        ),
        phases=("intent_classification", "durable_ingestion", "provenance_audit"),
        mutation_policy="typed_state_only",
        authority=DevelopmentAuthorityRequirement(
            capabilities=(
                "packet.observe",
                "plan.ingest",
                "finding.ingest",
                "guard.queue",
            ),
        ),
        evidence=DevelopmentEvidenceContract(
            reads=(
                "ReviewState",
                "PacketLifecycleHistory",
                "PacketOutcomeLedger",
                "PacketContinuityIndex",
                "PacketPlanContext",
                "AgentSyncProjection",
            ),
            writes=(
                "PlanRow",
                "FindingReview",
                "GuardPromotionCandidate",
                "KnowledgeSynthesisRecord",
                "ContextGraphSeed",
                "PacketDurableIngestionReceipt",
                "PacketIngestionGapReport",
            ),
            emits_packets=("blocked", "finding", "system_notice"),
            visible_in=(
                "sync-status",
                "review-channel history",
                "MasterPlan",
                "FindingBacklog",
                "claude-loop",
                "develop status",
            ),
        ),
        routing=DevelopmentRoutingContract(
            route_sources=(
                "review-channel history",
                "sync-status --since-event-id",
                "PacketLifecycleHistory",
                "PacketOutcomeLedger",
                "PacketPlanContext",
            ),
            selection_signals=(
                "packet_has_plan_or_finding_intent",
                "missing_durable_packet_provenance",
                "outcome_promoted_without_durable_row",
                "packet_ttl_remaining_seconds",
                "clock_expired_without_durable_owner",
                "multiple_sessions_claim_same_packet",
            ),
            dispatch_contracts=(
                "PlanRow",
                "FindingReview",
                "GuardPromotionCandidate",
                "PacketDurableIngestionReceipt",
            ),
            fail_closed_when=(
                "packet outcome claims promoted_to_finding but no durable row references the packet id",
                "plan/finding/guard packet is near TTL without an ingestion receipt",
                "a packet is being treated as the source of truth",
            ),
        ),
        allowed_actions=(
            "classify_packet_intent",
            "write_plan_row",
            "record_finding_review",
            "queue_guard_candidate",
            "link_packet_provenance",
        ),
        blocked_actions=(
            "packet_as_source_of_truth",
            "expire_before_durable_ingestion",
            "post_rescue_without_ingestion",
            "treat_ack_as_work_completion",
            "drop_expired_packet_silently",
        ),
    )


def _researcher() -> DevelopmentWorkstreamSpec:
    return DevelopmentWorkstreamSpec(
        workstream_id="researcher",
        display_name="Researcher",
        aliases=("research", "investigator"),
        runtime_role="subagent",
        plain_language="answers bounded questions without changing the live tree",
        phases=("research", "explain", "draft"),
        mutation_policy="read_only_or_isolated_worktree",
        authority=DevelopmentAuthorityRequirement(
            capabilities=("context.read", "packet.execute", "research.external"),
            lease_kind="optional_isolated_worktree",
        ),
        evidence=DevelopmentEvidenceContract(
            reads=(
                "ContextGraphSnapshot",
                "SystemCatalog",
                "source_files",
                "ResearchRouteGrant",
            ),
            writes=("ResearchEvidenceBundle", "ExternalSourceEvidence", "draft_patch"),
            emits_packets=("draft", "question", "blocked"),
            visible_in=("agent-sync", "agent work-board"),
        ),
        routing=DevelopmentRoutingContract(
            route_sources=(
                "context-graph",
                "system-map",
                "graph-walk",
                "ResearchRouteGrant",
            ),
            selection_signals=(
                "fan_out",
                "dependency_edges",
                "coverage_targets",
                "external_evidence_needed",
            ),
            graph_views=("context-graph --query <term>", "graph-walk from target file"),
            dispatch_contracts=("AgentDispatchRoute", "ResearchEvidenceBundle"),
            fail_closed_when=(
                "query cannot resolve the target contract or path",
                "external research is requested without ResearchRouteGrant",
            ),
        ),
        allowed_actions=(
            "inspect",
            "draft_patch",
            "run_read_only_checks",
            "external_research_with_provenance",
        ),
        blocked_actions=(
            "write_live_tree_without_lease",
            "web_search_without_route_grant",
            "commit",
            "push",
        ),
    )


def _knowledge_synthesizer() -> DevelopmentWorkstreamSpec:
    return DevelopmentWorkstreamSpec(
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
        allowed_actions=(
            "record_synthesis",
            "route_guard_candidate",
            "route_plan_gap",
            "refresh_generated_projection",
        ),
        blocked_actions=(
            "promote_uncited_research",
            "make_graph_authority",
            "store_architecture_in_chat",
        ),
    )


def _architect() -> DevelopmentWorkstreamSpec:
    return DevelopmentWorkstreamSpec(
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
            route_sources=(
                "findings-priority",
                "context-graph",
                "PlanningIRSnapshot",
                "KnowledgeSynthesisRecord",
            ),
            selection_signals=(
                "cluster_confidence",
                "plan_finding_mismatch",
                "hot_path_count",
                "knowledge_gap",
            ),
            graph_views=(
                "context-graph --mode diff",
                "system-map connectivity registry",
                "PointerRefIndex cited traversal view",
            ),
            dispatch_contracts=("PatternObservation", "PlanRow"),
            fail_closed_when=("pattern has no named consumer",),
        ),
        allowed_actions=("record_pattern", "propose_contract", "route_plan_gap"),
        blocked_actions=("change_runtime_authority_without_plan_row",),
    )


def _quality_engineer() -> DevelopmentWorkstreamSpec:
    return DevelopmentWorkstreamSpec(
        workstream_id="quality_engineer",
        display_name="Quality Engineer",
        aliases=("quality", "guard", "probe"),
        runtime_role="reviewer",
        plain_language="proves guards and probes are precise, useful, and replayable",
        phases=("guard_audit", "probe_audit", "red_team"),
        mutation_policy="fixture_only",
        authority=DevelopmentAuthorityRequirement(
            capabilities=("guard.audit", "probe.audit"),
        ),
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


def _dogfood_tester() -> DevelopmentWorkstreamSpec:
    return DevelopmentWorkstreamSpec(
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


def _runtime_watcher() -> DevelopmentWorkstreamSpec:
    return DevelopmentWorkstreamSpec(
        workstream_id="runtime_watcher",
        display_name="Runtime Watcher",
        aliases=("watcher", "observer", "dashboard"),
        runtime_role="dashboard",
        plain_language="watches packets, sync status, stale actors, and drift",
        phases=("observe", "wake", "blocker_detection"),
        mutation_policy="read_only",
        authority=DevelopmentAuthorityRequirement(
            capabilities=("runtime.observe", "packet.observe"),
        ),
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


def _operator() -> DevelopmentWorkstreamSpec:
    return DevelopmentWorkstreamSpec(
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


def build_default_development_team() -> DevelopmentModeTopology:
    """Compatibility alias for older callers."""
    return build_default_development_topology()


__all__ = [
    "DEVELOPMENT_MODE_CONTRACT_ID",
    "DEVELOPMENT_MODE_SCHEMA_VERSION",
    "DEVELOPMENT_TEAM_CONTRACT_ID",
    "DevelopmentAuthorityRequirement",
    "DevelopmentEvidenceContract",
    "DevelopmentExternalResearchContract",
    "DevelopmentKnowledgeFlowContract",
    "DevelopmentLearningContract",
    "DevelopmentModeTopology",
    "DevelopmentRoutingContract",
    "DevelopmentWorkstreamSpec",
    "build_default_development_team",
    "build_default_development_topology",
]
