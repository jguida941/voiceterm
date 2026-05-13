"""Core governed-exception contract rows."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec, CrossLinkSpec
from .runtime_state_contract_rows_bypass_lifecycle import BYPASS_LIFECYCLE_CONTRACTS

GOVERNED_EXCEPTION_CORE_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="TypedGateFailure",
        owner_layer="governance_runtime",
        purpose=(
            "Typed discoverability payload emitted by gate failures so agents "
            "see the gate id, violation reason, existing audited bypass "
            "invocation, owning contract path, and governed exception lifecycle "
            "path at point of need."
        ),
        required_fields=(
            ContractField("gate_id", "str", "Canonical gate identifier."),
            ContractField("violation_reason", "str", "Reason the gate failed."),
            ContractField(
                "bypass_invocation",
                "str",
                "Existing typed CLI invocation for audited edit-only override.",
            ),
            ContractField(
                "bypass_receipt_kind",
                "str",
                "Receipt kind issued by the existing BypassLifecycle path.",
            ),
            ContractField(
                "contract_definition_path",
                "str",
                "File and line for the gate's typed contract or reducer.",
            ),
            ContractField(
                "exception_lifecycle_class",
                "str",
                "Governed lifecycle to file for architectural gate changes.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.typed_gate_failure:TypedGateFailure",
        startup_surface_tokens=(
            "gate_id",
            "bypass_invocation",
            "bypass_receipt_kind",
            "exception_lifecycle_class",
        ),
    ),
    ContractSpec(
        contract_id="GovernedExceptionLifecycle",
        owner_layer="governance_runtime",
        purpose=(
            "Typed lifecycle envelope that keeps exception debt bound to "
            "repair, proof, finding, validation, and projection state without "
            "granting exception execution authority."
        ),
        required_fields=(
            ContractField("lifecycle_id", "str", "Stable lifecycle id."),
            ContractField("status", "str", "Lifecycle status."),
            ContractField("exception", "ExceptionReceipt | None", "Pending receipt."),
            ContractField("resolution", "ResolutionReceipt | None", "Closure receipt."),
            ContractField("closure_proof", "ClosureProof | None", "Normal-path proof."),
            ContractField("finding_id", "str", "Linked FindingBacklog id."),
            ContractField("planned_finding_ingest_ref", "str", "Planned finding-ingest hook."),
            ContractField("validation_plan_id", "str", "Linked ValidationPlan id."),
            ContractField("authority_evidence_refs", "tuple[str, ...]", "Authority evidence refs."),
            ContractField("worktree_safety_evidence_refs", "tuple[str, ...]", "Orphan/worktree evidence refs."),
            ContractField("system_map_contract_ids", "tuple[str, ...]", "Registered SYSTEM_MAP contracts."),
            ContractField("developer_loop_refs", "tuple[str, ...]", "devctl develop / packet refs."),
            ContractField("learning_refs", "tuple[str, ...]", "Dogfood or learning refs."),
            ContractField("projection_refs", "tuple[str, ...]", "Projection readers."),
            ContractField("resolution_receipt_id", "str", "External closure receipt id."),
            ContractField("created_at_utc", "str", "Creation timestamp."),
            ContractField("updated_at_utc", "str", "Last update timestamp."),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.governed_exception_contracts:"
            "GovernedExceptionLifecycle"
        ),
        startup_surface_tokens=("lifecycle_id", "status", "finding_id"),
        cross_links=(
            CrossLinkSpec(
                "exception",
                "ExceptionReceipt",
                "contains",
                target_node_kind="receipt",
                target_resolver="embedded_exception_receipt",
                required=True,
            ),
            CrossLinkSpec(
                "resolution",
                "ResolutionReceipt",
                "contains",
                target_node_kind="receipt",
                target_resolver="embedded_resolution_receipt",
                required_when="status in {closed,resolved}",
            ),
            CrossLinkSpec(
                "closure_proof",
                "ClosureProof",
                "contains",
                target_node_kind="receipt",
                target_resolver="embedded_closure_proof",
                required_when="status in {closed,resolved}",
            ),
            CrossLinkSpec(
                "finding_id",
                "FindingBacklog",
                "finding_blocks",
                target_node_kind="finding",
                target_resolver="finding_backlog_id",
                direction="reverse",
                required=True,
                required_when="no planned_finding_ingest_ref",
                validation_policy="must_resolve_or_planned_ingest",
            ),
            CrossLinkSpec(
                "planned_finding_ingest_ref",
                "PlatformFindingIngest",
                "related_to",
                target_node_kind="typed_contract",
                target_resolver="platform_finding_ingest_ref",
                required=True,
                required_when="no finding_id",
                validation_policy="must_resolve_or_finding",
            ),
            CrossLinkSpec(
                "resolution_receipt_id",
                "ResolutionReceipt",
                "receipt_proves",
                target_node_kind="receipt",
                target_resolver="resolution_receipt_id",
                required_when="status in {closed,resolved}",
            ),
        ),
    ),
    ContractSpec(
        contract_id="ExceptionReceipt",
        owner_layer="governance_runtime",
        purpose="Typed exception receipt; evidence only, not mutation authority.",
        required_fields=(
            ContractField("receipt_id", "str", "Stable exception receipt id."),
            ContractField("action_kind", "str", "Guarded action kind."),
            ContractField("phase", "str", "Guarded action phase."),
            ContractField("guard_id", "str", "Guard or preflight id."),
            ContractField("exception_class", "str", "Policy exception class."),
            ContractField("operator_reason", "str", "Specific typed reason."),
            ContractField("head", "str", "HEAD bound to the receipt."),
            ContractField("scope", "str", "Bounded operator-approved request scope."),
            ContractField("finding_id", "str", "Linked FindingBacklog id."),
            ContractField("planned_finding_ingest_ref", "str", "Planned finding-ingest hook."),
            ContractField("worktree_fingerprint", "str", "Bound worktree fingerprint."),
            ContractField("remote", "str", "Remote name for publish-class actions."),
            ContractField("policy_result", "str", "Policy decision result."),
            ContractField("authority_evidence_refs", "tuple[str, ...]", "Authority evidence refs."),
            ContractField("worktree_safety_evidence_refs", "tuple[str, ...]", "Worktree/orphan evidence refs."),
            ContractField("validation_plan_id", "str", "Linked ValidationPlan id."),
            ContractField("execution_status", "str", "Evidence-only execution status."),
            ContractField("remote_ref_verified", "bool", "Push remote-ref proof."),
            ContractField("post_push_proof_ref", "str", "Post-push proof ref."),
            ContractField("expires_at_utc", "str", "Receipt expiry timestamp."),
            ContractField("created_at_utc", "str", "Receipt creation timestamp."),
            ContractField(
                "correlation_id",
                "str",
                "Parent lineage shared with the guarded action and receipts.",
            ),
            ContractField(
                "causation_id",
                "str",
                "Immediate trigger lineage for the exception receipt.",
            ),
            ContractField(
                "run_id",
                "str",
                "Run lineage for the validation or bypass sequence.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.governed_exception_contracts:ExceptionReceipt",
        startup_surface_tokens=("receipt_id", "action_kind", "correlation_id"),
        cross_links=(
            CrossLinkSpec(
                "finding_id",
                "FindingBacklog",
                "finding_blocks",
                target_node_kind="finding",
                target_resolver="finding_backlog_id",
                direction="reverse",
                required=True,
                required_when="no planned_finding_ingest_ref",
                validation_policy="must_resolve_or_planned_ingest",
            ),
            CrossLinkSpec(
                "planned_finding_ingest_ref",
                "PlatformFindingIngest",
                "related_to",
                target_node_kind="typed_contract",
                target_resolver="platform_finding_ingest_ref",
                required=True,
                required_when="no finding_id",
                validation_policy="must_resolve_or_finding",
            ),
        ),
    ),
    *BYPASS_LIFECYCLE_CONTRACTS,
    ContractSpec(
        contract_id="ResolutionReceipt",
        owner_layer="governance_runtime",
        purpose="Closure receipt proving the original guarded path passed normally.",
        required_fields=(
            ContractField("resolution_id", "str", "Stable resolution id."),
            ContractField("exception_lifecycle_id", "str", "Lifecycle closed by this receipt."),
            ContractField("finding_id", "str", "Linked finding id."),
            ContractField("status", "str", "Resolution status."),
            ContractField("root_cause_class", "str", "Classified root cause."),
            ContractField("root_cause_summary", "str", "Root cause summary."),
            ContractField("fixed_by_commit", "str", "Fix commit or empty for non-code fix."),
            ContractField("changed_files", "tuple[str, ...]", "Files changed by fix."),
            ContractField("validation_receipt_id", "str", "ValidationReceipt proof id."),
            ContractField("action_result_id", "str", "ActionResult proof id."),
            ContractField("dogfood_evidence_id", "str", "Dogfood/governance evidence id."),
            ContractField("closure_proof_id", "str", "ClosureProof id."),
            ContractField("exception_used", "bool", "Must be false for final proof."),
            ContractField("remote_ref_verified", "bool", "Push remote-ref proof."),
            ContractField("post_push_green", "bool", "Post-push proof status."),
            ContractField("closed_at_utc", "str", "Closure timestamp."),
            ContractField("closure_reason", "str", "Closure reason."),
        ),
        runtime_model="dev.scripts.devctl.runtime.governed_exception_contracts:ResolutionReceipt",
        startup_surface_tokens=("resolution_id", "status", "finding_id"),
        cross_links=(
            CrossLinkSpec(
                "exception_lifecycle_id",
                "GovernedExceptionLifecycle",
                "receipt_proves",
                target_resolver="governed_exception_lifecycle_id",
                required=True,
                validation_policy="must_resolve",
            ),
            CrossLinkSpec(
                "finding_id",
                "FindingBacklog",
                "related_to",
                target_node_kind="finding",
                target_resolver="finding_backlog_id",
                required=True,
                validation_policy="must_resolve",
            ),
            CrossLinkSpec(
                "action_result_id",
                "ActionResult",
                "receipt_proves",
                target_resolver="action_result_id",
                required_when="status == verified",
                validation_policy="must_resolve_for_verified_status",
            ),
            CrossLinkSpec(
                "closure_proof_id",
                "ClosureProof",
                "receipt_proves",
                target_node_kind="receipt",
                target_resolver="closure_proof_id",
                required_when="status == verified",
                validation_policy="must_resolve_for_verified_status",
            ),
        ),
    ),
)

__all__ = ["GOVERNED_EXCEPTION_CORE_CONTRACTS"]
