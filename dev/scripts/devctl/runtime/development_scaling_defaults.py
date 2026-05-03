"""Default scaling policy for typed development mode."""

from __future__ import annotations

from .development_team import DevelopmentScaleModeSpec, DevelopmentScalingContract

PRESSURE_INPUTS = (
    "PacketBacklogPressure",
    "PacketContinuityIndex",
    "packet_carry_forward_debt",
    "PacketDebtRemediationReport",
    "inter_agent_communication_lag",
    "FindingBacklog",
    "PlanningIRSnapshot.next_best_slices",
    "GuardSmartnessReport",
    "SystemMapSnapshot.coverage_gaps",
    "CoordinationSnapshot.current_slice",
    "AgentDispatchRouter.safe_to_fanout",
    "OrphanSnapshot",
    "WorkerTopologySnapshot",
)
ROUTE_OUTPUTS = (
    "FanoutPlan",
    "WorkerPacket",
    "AgentDispatchRoute",
    "MutationLease",
    "PacketCreationBinding",
    "PacketDurableIngestionReceipt",
    "PlanIntentIngestionReceipt",
    "PacketDebtRemediationReport",
    "AgentSessionOutcome",
    "RunRecord",
)
SCALE_OUT_WHEN = (
    "actionable_packet_count exceeds the configured intake budget",
    "near_ttl_packet_count is non-zero for plan/finding/guard intent",
    "durable_ingestion_gap_count is non-zero",
    "independent_next_slices are disjoint and have owners",
    "review_or_probe_backlog exceeds reviewer capacity",
    "watcher_stale_window_count shows packets or actors aging out",
    "external_or_architecture_research is independent of live mutation",
)
COMMUNICATION_RULES = (
    "every worker receives a WorkerPacket with owner, scope, evidence, reply target, and TTL",
    "worker progress and handoff use packets with responds_to_packet_id or causal_packet_ids",
    "plan/finding/guard claims route through PacketCreationBinding before packet expiry",
    "actors are selected by typed capability and session authority, not provider name",
    "chat prose never replaces WorkerPacket, PlanRow, FindingReview, RunRecord, or ingestion receipts",
)
SAFETY_GATES = (
    "mutable fanout requires AgentDispatchRouter.safe_to_fanout=true",
    "live-tree mutation requires exactly one active session-bound MutationLease",
    "isolated builder lanes require registered worktree identity and OrphanSnapshot clearance",
    "write scopes must be disjoint across worker lanes",
    "packet ids are provenance links, not durable work authority",
    "graph and pointer outputs are projections over canonical sinks",
    "no provider default, reviewer label, or planned topology grants repo mutation",
)
SCALE_IN_WHEN = (
    "packet pressure drops below budget and no near-TTL intent remains",
    "worker TTL expires without progress evidence",
    "selected packet is applied, dismissed, superseded, or durably ingested",
    "safe_to_fanout becomes false",
    "workstream evidence contract is missing or stale",
    "mutation lease expires, is revoked, or loses path-scope exclusivity",
)
SUCCESS_METRICS = (
    "median packet wait time decreases",
    "clock-expired packets without durable owner decrease",
    "PacketDurableIngestionReceipt coverage increases",
    "inter-agent communication lag decreases",
    "mutation scope conflicts stay at zero",
    "guard/probe recurrence rate decreases for fixed issue classes",
)

CONTROLLER_ONLY_MODE = DevelopmentScaleModeSpec(
    mode_id="controller_only",
    display_name="Controller Only",
    workstreams=("coordinator", "runtime_watcher"),
    purpose="route, observe, and explain with no extra workers",
    pressure_signals=("no independent work pressure", "safe_to_fanout=false"),
    capacity_effect="keeps one controller path active until safe fanout evidence exists",
    evidence_outputs=("DevelopmentLoopReport", "CommandRunPlan"),
    blocked_when=("required visibility inputs are stale",),
)
INTAKE_FANOUT_MODE = DevelopmentScaleModeSpec(
    mode_id="intake_fanout",
    display_name="Intake Fanout",
    workstreams=("plan_intake_steward",),
    purpose="clear packet-to-plan/finding/guard ingestion pressure before TTL loss",
    pressure_signals=(
        "near_ttl_packet_count",
        "durable_ingestion_gap_count",
        "outcome_promoted_without_durable_row",
        "packet_carry_forward_debt",
    ),
    capacity_effect="adds Plan Intake Steward lanes that write durable typed owners",
    required_gates=("packet lifecycle projection is fresh",),
    evidence_outputs=(
        "PlanRow",
        "FindingReview",
        "GuardPromotionCandidate",
        "PacketDurableIngestionReceipt",
        "PlanIntentIngestionReceipt",
    ),
    blocked_when=("packet would remain the only source of truth",),
)
REVIEW_FANOUT_MODE = DevelopmentScaleModeSpec(
    mode_id="review_fanout",
    display_name="Review Fanout",
    workstreams=("reviewer", "quality_engineer"),
    purpose="parallelize patch review, guard proof, and smartness audits",
    pressure_signals=(
        "completion_packet_backlog",
        "review_or_probe_backlog",
        "GuardSmartnessReport due",
        "red_team_fixture backlog",
    ),
    capacity_effect="adds independent read-only reviewers and quality lanes",
    required_gates=("review targets are disjoint or read-only",),
    evidence_outputs=("FindingReview", "GuardSmartnessReport", "red_team_fixture_result"),
    blocked_when=("review evidence would be self-accepted by the builder",),
)
RESEARCH_FANOUT_MODE = DevelopmentScaleModeSpec(
    mode_id="research_fanout",
    display_name="Research Fanout",
    workstreams=("researcher", "knowledge_synthesizer", "architect"),
    purpose="answer independent code, graph, system-map, and approved external questions",
    pressure_signals=(
        "coverage_gaps",
        "abstract contract query misses",
        "external_evidence_needed",
        "architecture pattern cluster",
    ),
    capacity_effect="adds read-only research lanes that feed canonical sinks",
    required_gates=("ResearchRouteGrant exists for web/vendor/library work",),
    evidence_outputs=("ResearchEvidenceBundle", "ExternalSourceEvidence", "KnowledgeSynthesisRecord", "ContextGraphSeed"),
    blocked_when=("uncited external claim would become plan or guard authority",),
)
WATCHER_FANOUT_MODE = DevelopmentScaleModeSpec(
    mode_id="watcher_fanout",
    display_name="Watcher Fanout",
    workstreams=("runtime_watcher",),
    purpose="track stale packets, sync drift, process drift, and queue pressure",
    pressure_signals=("stale_packet_count", "actor_stale_seconds", "inter_agent_communication_lag", "fanout_command_latency"),
    capacity_effect="adds read-only watcher lanes with bounded packets",
    evidence_outputs=("stale_state_report", "wake_recommendation"),
    blocked_when=("watcher infers activity from partner wait state only",),
)
ISOLATED_BUILDER_FANOUT_MODE = DevelopmentScaleModeSpec(
    mode_id="isolated_builder_fanout",
    display_name="Isolated Builder Fanout",
    workstreams=("builder",),
    purpose="draft bounded patches in isolated worktrees when scopes are independent",
    pressure_signals=("independent_next_slices", "safe_to_fanout=true"),
    capacity_effect="adds isolated builders whose output stays draft until integrated",
    required_gates=(
        "AgentDispatchRouter.safe_to_fanout=true",
        "registered delegated worktree",
        "OrphanSnapshot clear",
        "disjoint path_scope",
    ),
    evidence_outputs=("draft_patch", "RunRecord", "completion_packet"),
    blocked_when=("unregistered worktree or overlapping write scope exists",),
)
LEASED_LIVE_TREE_BUILDER_MODE = DevelopmentScaleModeSpec(
    mode_id="leased_live_tree_builder",
    display_name="Leased Live-Tree Builder",
    workstreams=("builder",),
    purpose="perform the one live-tree mutation path after routing selects an owner",
    pressure_signals=("implementation slice selected", "MutationLease active"),
    capacity_effect="activates the exclusive live-tree writer and keeps other work isolated",
    required_gates=(
        "session-bound MutationLease",
        "repo.stage and repo.commit capabilities",
        "approval packet when required by policy",
    ),
    evidence_outputs=("source_diff", "RunRecord", "completion_packet", "AgentSessionOutcome"),
    blocked_when=("another live-tree mutation owner is active",),
)
SCALING_MODES = (
    CONTROLLER_ONLY_MODE,
    INTAKE_FANOUT_MODE,
    REVIEW_FANOUT_MODE,
    RESEARCH_FANOUT_MODE,
    WATCHER_FANOUT_MODE,
    ISOLATED_BUILDER_FANOUT_MODE,
    LEASED_LIVE_TREE_BUILDER_MODE,
)


def build_development_scaling_contract() -> DevelopmentScalingContract:
    """Return the default pressure-to-fanout contract."""
    return DevelopmentScalingContract(
        pressure_inputs=PRESSURE_INPUTS,
        route_outputs=ROUTE_OUTPUTS,
        scale_out_when=SCALE_OUT_WHEN,
        communication_rules=COMMUNICATION_RULES,
        safety_gates=SAFETY_GATES,
        scale_in_when=SCALE_IN_WHEN,
        success_metrics=SUCCESS_METRICS,
        modes=SCALING_MODES,
    )


__all__ = ["build_development_scaling_contract"]
