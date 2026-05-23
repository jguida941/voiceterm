"""Git mutation proof runtime contract rows for the platform blueprint."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec

GIT_MUTATION_PROOF_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="GitMutationProofReceipt",
        owner_layer="governance_runtime",
        purpose=(
            "Typed proof that a git mutation changed the exact local object or "
            "remote ref claimed by commit/push progress and publication surfaces."
        ),
        required_fields=(
            ContractField("receipt_id", "str", "Stable proof receipt id."),
            ContractField("mutation_kind", "str", "Mutation kind, such as commit or push."),
            ContractField("action_id", "str", "Typed action that executed the mutation."),
            ContractField("pipeline_id", "str", "Remote commit pipeline linked to the mutation."),
            ContractField("plan_row_id", "str", "Plan row or feature slice advanced by the mutation."),
            ContractField("command_name", "str", "Git command family being proven."),
            ContractField("command_returncode", "int", "Observed git command return code."),
            ContractField(
                "operation_returned_success",
                "bool",
                "Whether the raw operation reported success before independent verification.",
            ),
            ContractField("expected_sha", "str", "Commit SHA the mutation claims to prove."),
            ContractField("observed_local_sha", "str", "Local HEAD SHA observed after mutation."),
            ContractField("observed_remote_sha", "str", "Remote ref SHA observed after push."),
            ContractField("object_type", "str", "Git object type for expected_sha when applicable."),
            ContractField("remote_name", "str", "Remote name for push mutations."),
            ContractField("branch_name", "str", "Branch name for push mutations."),
            ContractField("verified", "bool", "True only when observed state matches the claim."),
            ContractField("status", "str", "Proof status."),
            ContractField("failure_reason", "str", "Bounded failure reason when verification fails."),
            ContractField("recorded_at_utc", "str", "UTC timestamp when proof was recorded."),
            ContractField("produced_by", "str", "Actor/tool that produced the proof."),
            ContractField(
                "code_identity_hash",
                "str",
                "Code identity hash that pins the mutation to a typed code-identity claim.",
            ),
            ContractField("evidence_refs", "tuple[str, ...]", "Refs inspected by the proof."),
            ContractField("artifact_paths", "tuple[str, ...]", "Artifacts linked to the proof."),
            ContractField(
                "correlation_context",
                "CorrelationContext",
                "Typed lineage context shared across related receipts.",
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.git_mutation_proof_receipt:"
            "GitMutationProofReceipt"
        ),
        startup_surface_tokens=("receipt_id", "mutation_kind", "verified"),
    ),
)
