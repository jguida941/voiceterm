"""State runtime contract rows for the platform blueprint."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec
from .runtime_state_contract_rows_review_pipeline import (
    REVIEW_PIPELINE_STATE_CONTRACTS,
)


RUNTIME_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="FindingReview",
        owner_layer="governance_core",
        purpose=(
            "Canonical adjudication input for one governance-review row before "
            "it is persisted into the durable finding backlog."
        ),
        required_fields=(
            ContractField("signal_type", "str", "Signal family under review."),
            ContractField(
                "check_id",
                "str",
                "Guard, probe, or workflow check identifier.",
            ),
            ContractField("verdict", "str", "Reviewer verdict for the finding row."),
            ContractField("file_path", "str", "Repo-relative finding target path."),
            ContractField(
                "symbol",
                "str | None",
                "Optional symbol or file-level target.",
            ),
            ContractField("line", "int | None", "Optional source line for the finding."),
            ContractField("severity", "str | None", "Optional normalized severity."),
            ContractField("risk_type", "str | None", "Optional normalized risk family."),
            ContractField("source_command", "str | None", "Command that produced the row."),
            ContractField("scan_mode", "str | None", "Optional scan mode provenance."),
            ContractField("repo_name", "str | None", "Optional repo identity label."),
            ContractField("repo_path", "str | None", "Optional repo provenance path."),
            ContractField("notes", "str | None", "Reviewer notes or AI guidance."),
            ContractField("finding_type", "str | None", "Optional source finding type."),
            ContractField("finding_id", "str | None", "Optional stable finding identity."),
            ContractField(
                "finding_class",
                "str | None",
                "Optional governance finding classification.",
            ),
            ContractField(
                "recurrence_risk",
                "str | None",
                "Optional recurrence-risk classification.",
            ),
            ContractField(
                "prevention_surface",
                "str | None",
                "Optional surface expected to prevent recurrence.",
            ),
            ContractField("waiver_reason", "str | None", "Optional waiver rationale."),
            ContractField("guidance_id", "str | None", "Optional guidance identifier."),
            ContractField(
                "guidance_followed",
                "bool | None",
                "Whether attached guidance was followed.",
            ),
        ),
        runtime_model="dev.scripts.devctl.governance_review.models:GovernanceReviewInput",
        startup_surface_tokens=("signal_type", "check_id", "verdict"),
    ),
    ContractSpec(
        contract_id="FindingBacklog",
        owner_layer="governance_runtime",
        purpose=(
            "Canonical latest/open finding backlog projected from the durable "
            "governance-review log for ranking, planning, and startup quality signals."
        ),
        required_fields=(
            ContractField("log_path", "str", "Durable governance-review log path."),
            ContractField("repo_name", "str", "Repo identity label."),
            ContractField("repo_path", "str", "Repo provenance path."),
            ContractField("total_rows", "int", "Total governance-review rows read."),
            ContractField("total_findings", "int", "Total latest finding identities."),
            ContractField(
                "latest_rows",
                "tuple[dict[str, Any], ...]",
                "Latest governance-review row for each finding identity.",
            ),
            ContractField(
                "open_rows",
                "tuple[dict[str, Any], ...]",
                "Latest rows still classified as open confirmed issues.",
            ),
            ContractField(
                "open_findings",
                "tuple[FindingRecord, ...]",
                "Typed open Finding records reprojected from open rows.",
            ),
            ContractField(
                "open_severity_counts",
                "tuple[FindingSeverityCount, ...]",
                "Open finding counts bucketed by severity.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.finding_backlog:FindingBacklog",
        startup_surface_tokens=("latest_rows", "open_rows", "open_findings"),
    ),
    ContractSpec(
        contract_id="PlatformFindingIngest",
        owner_layer="governance_runtime",
        purpose=(
            "Fail-open platform finding ingest result that records dogfood and "
            "governance-review evidence through the canonical FindingBacklog seam."
        ),
        required_fields=(
            ContractField("status", "str", "Ingest outcome status."),
            ContractField("reason", "str", "Bounded reason for the ingest outcome."),
            ContractField("log_path", "str", "Governance-review log path written."),
            ContractField(
                "row",
                "dict[str, Any] | None",
                "Persisted governance-review row.",
            ),
            ContractField(
                "finding",
                "dict[str, Any] | None",
                "Typed Finding projection for the persisted row.",
            ),
            ContractField(
                "dogfood_log_path",
                "str",
                "Dogfood ledger path when command-failure evidence was persisted.",
            ),
            ContractField(
                "dogfood_record",
                "dict[str, Any] | None",
                "Persisted dogfood row linked to the governance finding.",
            ),
            ContractField(
                "dogfood_summary_paths",
                "dict[str, str] | None",
                "Refreshed dogfood summary artifact paths.",
            ),
            ContractField(
                "summary_paths",
                "dict[str, str] | None",
                "Refreshed governance-review summary artifact paths.",
            ),
            ContractField(
                "promotion_candidate",
                "dict[str, Any] | None",
                "Optional guard-promotion candidate derived from the row.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.platform_finding_ingest:PlatformFindingIngestResult",
        startup_surface_tokens=("status", "reason", "finding"),
    ),
    ContractSpec(
        contract_id="CheckResult",
        owner_layer="governance_runtime",
        purpose="Typed check-output envelope carrying step results, enriched status, and ViolationRecords for renderers and downstream consumers.",
        required_fields=(
            ContractField("timestamp", "str", "UTC timestamp for the run."),
            ContractField("success", "bool", "Whether all steps passed."),
            ContractField("total", "int", "Total step count."),
            ContractField("passed", "int", "Passed step count."),
            ContractField("failed", "int", "Failed step count."),
            ContractField("skipped", "int", "Skipped step count."),
            ContractField("steps", "tuple[dict, ...]", "Enriched step dicts with status and violation_summary."),
            ContractField("violations", "tuple[ViolationRecord, ...]", "Typed violation records from failed steps."),
        ),
        runtime_model="dev.scripts.devctl.runtime.check_result_models:CheckResult",
        startup_surface_tokens=("success", "total", "failed"),
    ),
    ContractSpec(
        contract_id="ControlState",
        owner_layer="governance_runtime",
        purpose=(
            "Machine-readable status snapshot for runs, queue state, "
            "approvals, warnings, and errors across clients."
        ),
        required_fields=(
            ContractField("timestamp", "str", "UTC timestamp for the snapshot."),
            ContractField(
                "approvals",
                "ApprovalPolicyState",
                "Approval/waiver state projected into every frontend.",
            ),
            ContractField(
                "active_runs",
                "tuple[ActiveRunState, ...]",
                "Current governed runs visible to CLI/UI clients.",
            ),
            ContractField(
                "review_bridge",
                "ReviewBridgeState",
                "Shared review-channel liveness and heartbeat state.",
            ),
            ContractField(
                "agents",
                "tuple[ReviewAgentState, ...]",
                "Visible review/loop agents participating in the control plane.",
            ),
            ContractField(
                "sources",
                "ControlStateSources",
                "Bounded source paths used to derive the control snapshot.",
            ),
            ContractField(
                "operator_context",
                "OperatorContext",
                "Typed operator-presence metadata for mode-aware governance decisions.",
            ),
            ContractField(
                "warnings",
                "tuple[str, ...]",
                "Non-blocking warnings carried with the control snapshot.",
            ),
            ContractField(
                "errors",
                "tuple[str, ...]",
                "Blocking errors carried with the control snapshot.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.control_state:ControlState",
        startup_surface_tokens=("approvals", "active_runs", "review_bridge"),
    ),
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
            ContractField("blockers", "tuple[str, ...]", "Blocking reasons."),
            ContractField("warnings", "tuple[str, ...]", "Non-blocking warnings."),
            ContractField("inputs", "dict[str, Any]", "Source input summary."),
        ),
        runtime_model="dev.scripts.devctl.commands.development.models:DevelopmentLoopReport",
        startup_surface_tokens=("status", "controller_state", "next_slice"),
    ),
    *REVIEW_PIPELINE_STATE_CONTRACTS,
)
