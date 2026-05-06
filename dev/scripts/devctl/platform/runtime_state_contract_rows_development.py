"""Development-mode runtime-state contract rows."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec
from .runtime_state_contract_rows_development_packets import (
    DEVELOPMENT_PACKET_STATE_CONTRACTS,
)
from .runtime_state_contract_rows_development_roles import (
    DEVELOPMENT_ROLE_STATE_CONTRACTS,
)
from .runtime_state_contract_rows_ground_truth import GROUND_TRUTH_STATE_CONTRACTS
from .runtime_state_contract_rows_plan_intake import PLAN_INTAKE_STATE_CONTRACTS

DEVELOPMENT_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="DevelopmentModeTopology",
        owner_layer="governance_runtime",
        purpose=(
            "Provider-neutral `/develop` workstream topology that maps "
            "user-facing development jobs to typed authority, routing, "
            "evidence, external research, and knowledge-flow contracts."
        ),
        required_fields=(
            ContractField("topology_id", "str", "Named topology preset."),
            ContractField(
                "workstreams",
                "tuple[DevelopmentWorkstreamSpec, ...]",
                "User-facing workstreams mapped to runtime authority and evidence.",
            ),
            ContractField(
                "global_routing",
                "DevelopmentRoutingContract",
                "Typed sources and fail-closed rules used before assignment.",
            ),
            ContractField(
                "learning_loop",
                "DevelopmentLearningContract",
                "Typed prevention loop for findings, patterns, guards, and prompts.",
            ),
            ContractField(
                "external_research",
                "DevelopmentExternalResearchContract",
                "Route-granted source policy for web/vendor/library research.",
            ),
            ContractField(
                "knowledge_flow",
                "DevelopmentKnowledgeFlowContract",
                "Promotion path from evidence to plan/guard/graph/pointer projections.",
            ),
            ContractField(
                "scaling",
                "DevelopmentScalingContract",
                "Typed pressure-to-fanout policy with named modes and safety gates.",
            ),
            ContractField(
                "assignment_policy",
                "str",
                "Provider-neutral actor/workstream assignment policy.",
            ),
            ContractField(
                "provider_policy",
                "str",
                "Statement that provider names never grant authority.",
            ),
            ContractField(
                "mutation_policy",
                "str",
                "Single live-tree mutation owner policy.",
            ),
            ContractField(
                "default_worker_fanout",
                "int",
                "Default worker fanout for launches without explicit fanout.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.development_team:DevelopmentModeTopology",
        startup_surface_tokens=(
            "workstreams",
            "global_routing",
            "external_research",
            "knowledge_flow",
            "scaling",
        ),
    ),
    ContractSpec(
        contract_id="DevelopmentLoopReport",
        owner_layer="governance_commands",
        purpose=(
            "Read-only `/develop` controller report that explains current "
            "state, selected next slice, topology, learning signals, "
            "discovery targets, checks, blockers, and next commands."
        ),
        required_fields=(
            ContractField("action", "str", "Develop command action."),
            ContractField("status", "str", "Controller status."),
            ContractField("ok", "bool", "Whether the report is runnable."),
            ContractField("controller_state", "str", "Read-only controller state."),
            ContractField("summary", "str", "Human-readable summary."),
            ContractField(
                "topology",
                "dict[str, Any]",
                "Serialized DevelopmentModeTopology used for this report.",
            ),
            ContractField(
                "next_slice",
                "DevelopmentNextSlice",
                "Deterministic next development slice selected from typed inputs.",
            ),
            ContractField(
                "packet_attention",
                "DevelopmentPacketAttention",
                "Packet-driven wake state that can preempt ordinary slice selection.",
            ),
            ContractField(
                "runtime",
                "DevelopmentRuntimeSnapshot",
                "Typed peer runtime rows from work-board and sync projections.",
            ),
            ContractField(
                "peer_minds",
                "tuple[DevelopmentPeerMindSnapshot, ...]",
                (
                    "Provider-latest auxiliary agent-mind context with "
                    "session coverage counts; never mutation or closure authority."
                ),
            ),
            ContractField(
                "orchestration",
                "DevelopmentOrchestrationSnapshot",
                (
                    "Existing agent-loop and system-picture signals consumed "
                    "by `/develop`, including structured source_surface, "
                    "severity, recommended_action, and closure_check_command "
                    "fields; not a second scheduler."
                ),
            ),
            ContractField(
                "collaboration_mode",
                "dict[str, Any]",
                (
                    "CollaborationModeTopology read-model payload with selected "
                    "mode, role preset, and packet-pressure policy. This explains "
                    "requested topology and never grants authority."
                ),
            ),
            ContractField(
                "packet_pressure",
                "PacketBacklogPressure",
                (
                    "Packet backlog pressure counts live/actionable, near-TTL, "
                    "expired unresolved, carry-forward, durable-owner-gap, "
                    "per-kind, and per-role packet pressure."
                ),
            ),
            ContractField(
                "selected_packet_classifications",
                "tuple[PacketIntentClassification, ...]",
                "Classifications for packets selected by pressure or durable-intent rules.",
            ),
            ContractField(
                "packet_ingestion_decision",
                "PacketAttentionIngestionDecision",
                (
                    "AgentAttentionLoop packet decision: continue, pivot, "
                    "ingest durable intent, request operator decision, or fail closed."
                ),
            ),
            ContractField(
                "watcher_lease",
                "DevelopmentWatcherLease",
                "Typed watcher lease/status for pending packet observation.",
            ),
            ContractField(
                "continuation",
                "DevelopmentContinuationRequiredSignal",
                (
                    "Typed stop/continue decision; terminal responses are "
                    "allowed only when continuation_required is false."
                ),
            ),
            ContractField(
                "learning",
                "DevelopmentLearningSnapshot",
                "Guard/probe and prevention-loop inputs visible to the controller.",
            ),
            ContractField(
                "discovery",
                "DevelopmentDiscoverySnapshot",
                "System-discovery counts and coverage targets.",
            ),
            ContractField(
                "required_checks",
                "tuple[str, ...]",
                "Checks required before handoff or widening.",
            ),
            ContractField(
                "next_commands",
                "tuple[str, ...]",
                "Bounded next commands selected by the controller.",
            ),
            ContractField(
                "next_step_command",
                "str",
                "Single recommended typed command for the next agent step.",
            ),
            ContractField(
                "lifecycle",
                "DevelopmentLifecyclePlan | None",
                "Preview-only `/develop` lifecycle guidance for actor work.",
            ),
            ContractField(
                "design_preflight",
                "DevelopmentDesignPreflight | None",
                "Ground-truth-first architecture/design preflight report.",
            ),
            ContractField(
                "packet_debt_remediation",
                "dict[str, Any] | None",
                "PacketDebtRemediationReport payload for audit-packets actions.",
            ),
            ContractField("blockers", "tuple[str, ...]", "Blocking reasons."),
            ContractField("warnings", "tuple[str, ...]", "Non-blocking warnings."),
            ContractField("inputs", "dict[str, Any]", "Source input summary."),
        ),
        runtime_model="dev.scripts.devctl.commands.development.models:DevelopmentLoopReport",
        startup_surface_tokens=(
            "status",
            "controller_state",
            "next_slice",
            "packet_attention",
            "runtime",
            "orchestration",
            "collaboration_mode",
            "packet_pressure",
            "packet_ingestion_decision",
        ),
    ),
    ContractSpec(
        contract_id="CollaborationModeTopology",
        owner_layer="governance_runtime",
        purpose=(
            "Read-only `/develop` collaboration-mode and role-preset topology. "
            "It explains requested mode, role lens, packet pressure policy, and "
            "fanout gates while leaving authority to typed runtime contracts."
        ),
        required_fields=(
            ContractField("topology_id", "str", "Named collaboration topology preset."),
            ContractField(
                "modes",
                "tuple[DevelopCollaborationModeSpec, ...]",
                "Requested collaboration modes such as solo, pair_review, and fanout modes.",
            ),
            ContractField(
                "role_presets",
                "tuple[DevelopRolePresetSpec, ...]",
                "Role lenses compiled by slash adapters or `/develop` requests.",
            ),
            ContractField(
                "packet_pressure_policy",
                "PacketAttentionPressurePolicy",
                "Repo-pack configurable soft/hard packet budgets and near-TTL window.",
            ),
            ContractField(
                "authority_policy",
                "str",
                "Statement that this read model never grants authority.",
            ),
            ContractField(
                "slash_adapter_policy",
                "str",
                "Slash adapters pass typed request fields and carry no policy.",
            ),
            ContractField("default_mode_id", "str", "Default collaboration mode."),
            ContractField("default_role_preset_id", "str", "Default role preset."),
            ContractField(
                "default_worker_fanout",
                "int",
                "Default worker fanout for unqualified requests.",
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.development_collaboration_modes:"
            "CollaborationModeTopology"
        ),
        startup_surface_tokens=(
            "modes",
            "role_presets",
            "packet_pressure_policy",
            "authority_policy",
        ),
    ),
    *DEVELOPMENT_ROLE_STATE_CONTRACTS,
    *DEVELOPMENT_PACKET_STATE_CONTRACTS,
    *GROUND_TRUTH_STATE_CONTRACTS,
    *PLAN_INTAKE_STATE_CONTRACTS,
)

__all__ = ["DEVELOPMENT_STATE_CONTRACTS"]
