"""Identity/action/evidence runtime contract rows for the platform blueprint."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec


RUNTIME_IDENTITY_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="RepoPack",
        owner_layer="repo_packs",
        purpose=(
            "Declares repo policy, docs templates, workflow defaults, and "
            "adoption checks for one repository family."
        ),
        required_fields=(
            ContractField("pack_id", "str", "Stable repo-pack identifier."),
            ContractField(
                "policy_path",
                "str",
                "Path to the repo policy file used by quality/governance commands.",
            ),
            ContractField(
                "workflow_profiles",
                "list[str]",
                "Allowlisted workflow/action profiles exposed for this repo.",
            ),
        ),
    ),
    ContractSpec(
        contract_id="TypedAction",
        owner_layer="governance_runtime",
        purpose=(
            "Canonical command payload for check, probe, bootstrap, fix, "
            "report, export, review, and remediation actions."
        ),
        required_fields=(
            ContractField("action_id", "str", "Stable typed action identifier."),
            ContractField(
                "repo_pack_id",
                "str",
                "Repo pack responsible for repo-local policy or defaults.",
            ),
            ContractField(
                "parameters",
                "dict[str, object]",
                "Machine-readable action arguments after parsing/validation.",
            ),
            ContractField("requested_by", "str", "Caller identity requesting the action."),
            ContractField(
                "dry_run",
                "bool",
                "Whether execution is report-only and must not mutate state.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.action_contracts:TypedAction",
    ),
    ContractSpec(
        contract_id="RunRecord",
        owner_layer="governance_runtime",
        purpose=(
            "Durable record for one governed execution episode, including "
            "inputs, findings, repairs, and outcomes."
        ),
        required_fields=(
            ContractField("run_id", "str", "Stable execution episode identifier."),
            ContractField("action_id", "str", "Typed action executed for the episode."),
            ContractField(
                "artifact_paths",
                "list[str]",
                "Materialized artifacts emitted during the episode.",
            ),
            ContractField("status", "str", "Execution status for the governed run."),
            ContractField("findings_count", "int", "Finding count emitted during the run."),
            ContractField("started_at", "str", "UTC start timestamp for the run."),
            ContractField("finished_at", "str", "UTC finish timestamp for the run."),
        ),
        runtime_model="dev.scripts.devctl.runtime.action_contracts:RunRecord",
    ),
    ContractSpec(
        contract_id="ActionResult",
        owner_layer="governance_runtime",
        purpose=(
            "Canonical result envelope for any command, service call, or "
            "agent action so all consumers parse one outcome shape."
        ),
        required_fields=(
            ContractField("action_id", "str", "Typed action that produced this result."),
            ContractField("ok", "bool", "Whether the action succeeded."),
            ContractField("status", "str", "Execution status label."),
            ContractField("reason", "str", "Failure or outcome reason code."),
            ContractField(
                "retryable",
                "bool",
                "Whether the caller can retry with the same inputs.",
            ),
            ContractField(
                "partial_progress",
                "bool",
                "Whether some work completed before failure.",
            ),
            ContractField(
                "operator_guidance",
                "str",
                "Human-readable next-step guidance on failure.",
            ),
            ContractField("warnings", "list[str]", "Non-fatal advisory messages."),
            ContractField("findings_count", "int", "Findings emitted during the action."),
            ContractField(
                "artifact_paths",
                "list[str]",
                "Materialized artifacts produced by the action.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.action_contracts:ActionResult",
    ),
    ContractSpec(
        contract_id="ArtifactStore",
        owner_layer="governance_runtime",
        purpose=(
            "Stable storage contract for reports, projections, review "
            "packets, snapshots, and benchmark evidence."
        ),
        required_fields=(
            ContractField("root", "str", "Root path for managed artifacts."),
            ContractField(
                "retention_policy",
                "dict[str, object]",
                "Retention/deletion rules enforced for this artifact family.",
            ),
            ContractField("managed_kinds", "list[str]", "Artifact kinds stored under the root."),
        ),
        runtime_model="dev.scripts.devctl.runtime.action_contracts:ArtifactStore",
    ),
    ContractSpec(
        contract_id="Finding",
        owner_layer="governance_runtime",
        purpose=(
            "Canonical machine-readable evidence row for one governance "
            "finding across probes, reports, and later review/fix flows."
        ),
        required_fields=(
            ContractField("finding_id", "str", "Stable finding identifier."),
            ContractField(
                "signal_type",
                "str",
                "Signal family that produced the finding, such as probe.",
            ),
            ContractField("check_id", "str", "Check or probe identifier."),
            ContractField("rule_id", "str", "Stable rule identifier."),
            ContractField("rule_version", "int", "Version of the emitting rule."),
            ContractField("repo_name", "str", "Repo identity label."),
            ContractField("repo_path", "str", "Repo provenance path."),
            ContractField("file_path", "str", "Repo-relative file path."),
            ContractField("symbol", "str", "Symbol or file-level target."),
            ContractField("line", "int | None", "Start line for the finding."),
            ContractField("end_line", "int | None", "End line for the finding."),
            ContractField("severity", "str", "Finding severity."),
            ContractField("risk_type", "str", "Normalized risk family."),
            ContractField("review_lens", "str", "Review lens or discipline."),
            ContractField(
                "ai_instruction",
                "str",
                "Machine-readable remediation guidance for AI.",
            ),
            ContractField("signals", "list[str]", "Raw evidence signals."),
            ContractField(
                "source_command",
                "str",
                "Command that emitted or aggregated the finding.",
            ),
            ContractField(
                "source_artifact",
                "str",
                "Artifact family that carried the finding.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.finding_contracts:FindingRecord",
    ),
    ContractSpec(
        contract_id="DecisionPacket",
        owner_layer="governance_runtime",
        purpose=(
            "Typed decision packet projected from one canonical finding for "
            "AI/human architectural review and approval."
        ),
        required_fields=(
            ContractField("finding_id", "str", "Stable source finding identifier."),
            ContractField("check_id", "str", "Check or probe identifier."),
            ContractField("rule_id", "str", "Stable rule identifier."),
            ContractField("rule_version", "int", "Version of the emitting rule."),
            ContractField("file_path", "str", "Repo-relative file path."),
            ContractField("symbol", "str", "Symbol or file-level target."),
            ContractField("severity", "str", "Finding severity."),
            ContractField("review_lens", "str", "Review lens or discipline."),
            ContractField("risk_type", "str", "Normalized decision risk family."),
            ContractField(
                "decision_mode",
                "str",
                "Whether the AI may auto-apply, recommend, or request approval.",
            ),
            ContractField("rationale", "str", "Human/AI rationale for the decision."),
            ContractField(
                "ai_instruction",
                "str",
                "Machine-readable guidance carried forward from the finding.",
            ),
            ContractField(
                "research_instruction",
                "str",
                "Follow-up investigation prompt for the decision-maker.",
            ),
            ContractField(
                "source_artifact",
                "str",
                "Artifact family that carried the packet.",
            ),
            ContractField("precedent", "str", "Prior art or precedent reference."),
            ContractField("invariants", "list[str]", "Constraints the decision must preserve."),
            ContractField(
                "validation_plan",
                "list[str]",
                "Checks to rerun after the selected decision path.",
            ),
            ContractField("signals", "list[str]", "Evidence signals carried into the packet."),
            ContractField(
                "rule_summary",
                "str",
                "Plain-language summary of why this decision rule was selected.",
            ),
            ContractField(
                "match_evidence",
                "list[RuleMatchEvidence]",
                "Structured reasons and concrete facts showing why the selected rule matched.",
            ),
            ContractField(
                "rejected_rule_traces",
                "list[RejectedRuleTrace]",
                "Competing rules that were considered and explicitly rejected.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.finding_contracts:DecisionPacketRecord",
    ),
    ContractSpec(
        contract_id="FailurePacket",
        owner_layer="governance_runtime",
        purpose=(
            "Canonical failure-evidence packet for test and workflow failures "
            "so triage, reports, and automation consume one structured root-cause surface."
        ),
        required_fields=(
            ContractField("source", "str", "Origin of the failure evidence bundle."),
            ContractField("runner", "str", "Failing test runner or workflow executor."),
            ContractField("generated_at", "str", "UTC timestamp for packet materialization."),
            ContractField("status", "str", "Overall packet status such as failed or passed."),
            ContractField("total_tests", "int", "Total tests observed in the packet."),
            ContractField("failed_tests", "int", "Total failed test cases."),
            ContractField("error_tests", "int", "Total errored test cases."),
            ContractField("skipped_tests", "int", "Total skipped test cases."),
            ContractField("passed_tests", "int", "Total passed test cases."),
            ContractField(
                "primary_test_id",
                "str",
                "Best-effort first or highest-priority failing test identifier.",
            ),
            ContractField(
                "primary_message",
                "str",
                "Best-effort primary assertion/error message for the packet.",
            ),
            ContractField(
                "cases",
                "tuple[FailureCase, ...]",
                "Structured failing test cases with message and traceback excerpts.",
            ),
            ContractField(
                "artifact_paths",
                "list[str]",
                "Artifact paths used to build the packet.",
            ),
            ContractField("warnings", "list[str]", "Non-blocking packet ingestion warnings."),
        ),
        runtime_model="dev.scripts.devctl.runtime.failure_packet:FailurePacket",
    ),
)
