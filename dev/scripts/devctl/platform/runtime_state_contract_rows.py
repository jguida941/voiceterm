"""State runtime contract rows for the platform blueprint."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec
from .runtime_state_contract_rows_development import DEVELOPMENT_STATE_CONTRACTS
from .runtime_state_contract_rows_governed_exceptions import (
    GOVERNED_EXCEPTION_STATE_CONTRACTS,
)
from .runtime_state_contract_rows_governance_proposed import (
    GOVERNANCE_PROPOSED_STATE_CONTRACTS,
)
from .runtime_state_contract_rows_review_pipeline import (
    GOVERNANCE_EXTENSION_STATE_CONTRACTS,
    REVIEW_PIPELINE_STATE_CONTRACTS,
)
from .runtime_state_contract_rows_relaunch_loop import RELAUNCH_LOOP_STATE_CONTRACTS
from .runtime_state_contract_rows_transitions import TRANSITION_STATE_CONTRACTS


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
        contract_id="PlatformContractRegistryRow",
        owner_layer="governance_core",
        purpose=(
            "Repo-owned registry row that records shared-contract ownership, "
            "schema-version, planned fixture root, and parity command without "
            "replacing the blueprint as authority."
        ),
        required_fields=(
            ContractField(
                "registered_contract_id",
                "str",
                "Shared contract or artifact-schema id named by the registry row.",
            ),
            ContractField(
                "entry_kind",
                "str",
                "shared_contract, artifact_schema, or authority_composition.",
            ),
            ContractField(
                "python_owner_path",
                "str",
                "Canonical Python owner path for the registered contract family.",
            ),
            ContractField(
                "rust_owner_path",
                "str",
                "Canonical Rust owner path when present, otherwise empty.",
            ),
            ContractField(
                "fixture_path",
                "str",
                "Canonical schema-fixture root planned for the registered family.",
            ),
            ContractField(
                "registered_schema_version",
                "int",
                "Current schema version advertised by the canonical owner.",
            ),
            ContractField(
                "ownership_mode",
                "str",
                "python_only, rust_only, shared, rust_primary, or system.",
            ),
            ContractField(
                "parity_command",
                "str",
                "Guard command expected to validate this registered family.",
            ),
            ContractField(
                "registry_path",
                "str",
                "Repo-owned JSONL registry path containing this row.",
            ),
        ),
        runtime_model="dev.scripts.devctl.platform.contract_registry_models:ContractRegistryRow",
        startup_surface_tokens=(
            "registered_contract_id",
            "entry_kind",
            "ownership_mode",
        ),
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
            ContractField("correlation_id", "str", "Parent lineage shared with the action or packet that requested the check."),
            ContractField("causation_id", "str", "Immediate trigger lineage for this check result."),
            ContractField("run_id", "str", "Orchestration run lineage for this check result."),
        ),
        runtime_model="dev.scripts.devctl.runtime.check_result_models:CheckResult",
        startup_surface_tokens=("success", "failed", "correlation_id"),
    ),
    ContractSpec(
        contract_id="SecurityReport",
        owner_layer="governance_runtime",
        purpose=(
            "Typed top-level report emitted by `devctl security`, preserving "
            "scanner settings, warnings, and step evidence for JSON and markdown renderers."
        ),
        required_fields=(
            ContractField("timestamp", "str", "UTC timestamp for the security run."),
            ContractField("ok", "bool", "Whether blocking security checks passed."),
            ContractField("rustsec_output", "str", "Resolved RustSec audit output path."),
            ContractField("scanner_tier", "str", "Scanner tier selected for the run."),
            ContractField("python_scope", "str", "Python scanner scope used by core checks."),
            ContractField("since_ref", "str | None", "Optional comparison base ref."),
            ContractField("head_ref", "str", "Comparison head ref."),
            ContractField(
                "expensive_policy",
                "str",
                "Policy for expensive advisory scanner failures.",
            ),
            ContractField(
                "core_scanners",
                "tuple[str, ...]",
                "Core scanner ids advertised by the command.",
            ),
            ContractField(
                "expensive_scanners",
                "tuple[str, ...]",
                "Expensive scanner ids advertised by the command.",
            ),
            ContractField("warnings", "tuple[str, ...]", "Non-fatal warnings emitted."),
            ContractField(
                "steps",
                "tuple[dict[str, Any], ...]",
                "Step records rendered through the CheckResult path.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.audit_report_contracts:SecurityReport",
        startup_surface_tokens=("contract_id", "schema_version", "scanner_tier"),
    ),
    ContractSpec(
        contract_id="RustAuditReport",
        owner_layer="governance_runtime",
        purpose=(
            "Typed aggregate Rust audit report preserving guard reports, "
            "category rationale, hotspots, and chart evidence for renderers."
        ),
        required_fields=(
            ContractField("mode", "str", "Resolved Rust audit mode."),
            ContractField("since_ref", "str | None", "Optional comparison base ref."),
            ContractField("head_ref", "str", "Comparison head ref."),
            ContractField("ok", "bool", "Whether all Rust audit guards were clean."),
            ContractField(
                "collection_ok",
                "bool",
                "Whether guard report collection succeeded.",
            ),
            ContractField("warnings", "tuple[str, ...]", "Non-fatal collection warnings."),
            ContractField("errors", "tuple[str, ...]", "Collection or parse errors."),
            ContractField("summary", "dict[str, Any]", "Aggregate audit summary."),
            ContractField(
                "guards",
                "tuple[dict[str, Any], ...]",
                "Per-guard status rows.",
            ),
            ContractField(
                "guard_reports",
                "dict[str, dict[str, Any]]",
                "Raw parsed guard payloads by guard id.",
            ),
            ContractField(
                "categories",
                "tuple[dict[str, Any], ...]",
                "Ranked finding categories with rationale and fixes.",
            ),
            ContractField(
                "hotspots",
                "tuple[dict[str, Any], ...]",
                "Ranked file hotspots by weighted audit score.",
            ),
            ContractField("charts", "tuple[str, ...]", "Chart artifact paths."),
        ),
        runtime_model="dev.scripts.devctl.runtime.audit_report_contracts:RustAuditReport",
        startup_surface_tokens=("contract_id", "schema_version", "collection_ok"),
    ),
    ContractSpec(
        contract_id="ReviewChannelCommandFreshness",
        owner_layer="governance_commands",
        purpose=(
            "Freshness metadata attached to review-channel read-only status "
            "and packet summary surfaces so old command output is distinguishable "
            "from current runtime state."
        ),
        required_fields=(
            ContractField(
                "command_generated_at_utc",
                "str",
                "UTC timestamp when the read-only command generated this output.",
            ),
            ContractField(
                "observed_at_utc",
                "str",
                "UTC timestamp used as the freshness comparison point.",
            ),
            ContractField(
                "command_age_seconds",
                "int | None",
                "Command output age at render time.",
            ),
            ContractField(
                "command_freshness_status",
                "str",
                "fresh, stale, or unknown command freshness.",
            ),
            ContractField(
                "runtime_snapshot_at_utc",
                "str",
                "UTC timestamp for the runtime snapshot backing the output.",
            ),
            ContractField(
                "runtime_snapshot_age_seconds",
                "int | None",
                "Runtime snapshot age at render time.",
            ),
            ContractField(
                "runtime_snapshot_freshness_status",
                "str",
                "fresh, stale, or unknown runtime snapshot freshness.",
            ),
            ContractField(
                "stale_after_seconds",
                "int",
                "Age threshold used to label freshness status.",
            ),
            ContractField("snapshot_id", "str", "Review-state snapshot id."),
            ContractField("zref", "str", "Review-state zero-ref identity."),
        ),
        runtime_model=(
            "dev.scripts.devctl.commands.review_channel.status_readiness:"
            "ReviewChannelCommandFreshness"
        ),
        startup_surface_tokens=(
            "command_generated_at_utc",
            "command_freshness_status",
            "runtime_snapshot_freshness_status",
        ),
    ),
    ContractSpec(
        contract_id="PacketGuardErrorDetail",
        owner_layer="governance_runtime",
        purpose=(
            "Structured guard and execution failure details attached to packet "
            "lifecycle events, recovery dispositions, and readable history "
            "surfaces so failures cannot collapse into generic stale backlog."
        ),
        required_fields=(
            ContractField("packet_id", "str", "Packet carrying the guard failure."),
            ContractField(
                "action",
                "str",
                "Lifecycle action that exposed the failure.",
            ),
            ContractField("reason", "str", "Primary failure reason."),
            ContractField(
                "failure_source",
                "str",
                "Where the failure detail was observed or synthesized.",
            ),
            ContractField("event_id", "str", "Lifecycle event id when available."),
            ContractField("actor", "str", "Actor associated with the failure."),
            ContractField("status", "str", "Packet or event status."),
            ContractField(
                "guard_results_summary",
                "str",
                "Guard result summary preserved from packet or event fields.",
            ),
            ContractField(
                "full_guard_bundle_evidence",
                "str",
                "Guard bundle evidence or failure-envelope reference.",
            ),
            ContractField("errors", "tuple[str, ...]", "Detailed guard errors."),
            ContractField(
                "reason_chain",
                "tuple[str, ...]",
                "Machine-readable failure reason chain.",
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.packet_guard_errors:"
            "PacketGuardErrorDetail"
        ),
        startup_surface_tokens=(
            "guard_error_detail",
            "failure_source",
            "full_guard_bundle_evidence",
        ),
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
    *DEVELOPMENT_STATE_CONTRACTS,
    *GOVERNED_EXCEPTION_STATE_CONTRACTS,
    *GOVERNANCE_EXTENSION_STATE_CONTRACTS,
    *GOVERNANCE_PROPOSED_STATE_CONTRACTS,
    *REVIEW_PIPELINE_STATE_CONTRACTS,
    *RELAUNCH_LOOP_STATE_CONTRACTS,
    *TRANSITION_STATE_CONTRACTS,
)
