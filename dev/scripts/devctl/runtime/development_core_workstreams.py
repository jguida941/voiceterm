"""Core workstream defaults for typed development mode."""

from __future__ import annotations

from .development_team import (
    DevelopmentAuthorityRequirement,
    DevelopmentEvidenceContract,
    DevelopmentRoutingContract,
    DevelopmentWorkstreamSpec,
)

COORDINATOR_WORKSTREAM = DevelopmentWorkstreamSpec(
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
        reads=("StartupContext", "ControlPlaneReadModel", "PlanningIRSnapshot", "AgentSyncProjection"),
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

BUILDER_WORKSTREAM = DevelopmentWorkstreamSpec(
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

REVIEWER_WORKSTREAM = DevelopmentWorkstreamSpec(
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

PLAN_INTAKE_STEWARD_WORKSTREAM = DevelopmentWorkstreamSpec(
    workstream_id="plan_intake_steward",
    display_name="Plan Intake Steward",
    aliases=("intake", "plan-ingest", "state-ingest", "packet-ingest", "provenance", "packet"),
    runtime_role="dashboard",
    plain_language=(
        "promotes packet-carried work into durable plan, finding, guard, "
        "and knowledge state with packet ids kept as provenance"
    ),
    phases=("intent_classification", "durable_ingestion", "provenance_audit"),
    mutation_policy="typed_state_only",
    authority=DevelopmentAuthorityRequirement(
        capabilities=("packet.observe", "plan.ingest", "finding.ingest", "guard.queue"),
    ),
    evidence=DevelopmentEvidenceContract(
        reads=(
            "ReviewState",
            "PacketLifecycleHistory",
            "PacketOutcomeLedger",
            "PacketContinuityIndex",
            "PacketCreationBinding",
            "PacketPlanContext",
            "AgentSyncProjection",
        ),
        writes=(
            "PlanRow",
            "FindingReview",
            "GuardPromotionCandidate",
            "KnowledgeSynthesisRecord",
            "ContextGraphSeed",
            "PacketCreationBinding",
            "PacketDurableIngestionReceipt",
            "PacketDebtRemediationReport",
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
            "PacketCreationBinding",
            "PacketDurableIngestionReceipt",
            "PacketDebtRemediationReport",
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

RESEARCHER_WORKSTREAM = DevelopmentWorkstreamSpec(
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
        reads=("ContextGraphSnapshot", "SystemCatalog", "source_files", "ResearchRouteGrant"),
        writes=("ResearchEvidenceBundle", "ExternalSourceEvidence", "draft_patch"),
        emits_packets=("draft", "question", "blocked"),
        visible_in=("agent-sync", "agent work-board"),
    ),
    routing=DevelopmentRoutingContract(
        route_sources=("context-graph", "system-map", "graph-walk", "ResearchRouteGrant"),
        selection_signals=("fan_out", "dependency_edges", "coverage_targets", "external_evidence_needed"),
        graph_views=("context-graph --query <term>", "graph-walk from target file"),
        dispatch_contracts=("AgentDispatchRoute", "ResearchEvidenceBundle"),
        fail_closed_when=(
            "query cannot resolve the target contract or path",
            "external research is requested without ResearchRouteGrant",
        ),
    ),
    allowed_actions=("inspect", "draft_patch", "run_read_only_checks", "external_research_with_provenance"),
    blocked_actions=("write_live_tree_without_lease", "web_search_without_route_grant", "commit", "push"),
)


def core_workstreams() -> tuple[DevelopmentWorkstreamSpec, ...]:
    return (
        COORDINATOR_WORKSTREAM,
        BUILDER_WORKSTREAM,
        REVIEWER_WORKSTREAM,
        PLAN_INTAKE_STEWARD_WORKSTREAM,
        RESEARCHER_WORKSTREAM,
    )


__all__ = ["core_workstreams"]
