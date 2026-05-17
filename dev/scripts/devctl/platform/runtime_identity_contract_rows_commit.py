"""Commit receipt runtime contract rows for the platform blueprint."""

from __future__ import annotations

from ..runtime.git_operation_receipts import BranchOperationReceipt, TagReceipt
from .contracts import ContractField, ContractSpec
from .runtime_identity_contract_rows_role_review import ROLE_REVIEW_CONTRACTS

_BRANCH_OPERATION_RECEIPT_RUNTIME_MODEL = (
    f"{BranchOperationReceipt.__module__}:{BranchOperationReceipt.__name__}"
)
_TAG_RECEIPT_RUNTIME_MODEL = f"{TagReceipt.__module__}:{TagReceipt.__name__}"

COMMIT_RECEIPT_CONTRACTS: tuple[ContractSpec, ...] = (
    *ROLE_REVIEW_CONTRACTS,
    ContractSpec(
        contract_id="CommitReceipt",
        owner_layer="governance_runtime",
        purpose=(
            "Typed evidence chain for one governed commit, binding commit SHA, "
            "plan row, reviewer ack packet, audit synthesis ref, validation receipt, "
            "and pipeline lineage."
        ),
        required_fields=(
            ContractField("receipt_id", "str", "Stable receipt ref for the governed commit."),
            ContractField("commit_sha", "str", "Commit SHA produced by the governed commit path."),
            ContractField(
                "tree_content_hash",
                "str",
                "Tree content identity bound to the validation snapshot.",
            ),
            ContractField("pipeline_id", "str", "Remote commit pipeline that produced the commit."),
            ContractField(
                "pipeline_generation_id",
                "str",
                "Pipeline generation bound to approval and execution.",
            ),
            ContractField("plan_row_id", "str", "Plan row or work-intake ref advanced by the commit."),
            ContractField(
                "reviewer_ack_packet_id",
                "str",
                "Reviewer ack or decision packet bound into the evidence chain.",
            ),
            ContractField("approval_packet_id", "str", "Approval request packet for the governed commit."),
            ContractField(
                "decision_packet_id",
                "str",
                "Approval/ack decision packet for the governed commit.",
            ),
            ContractField(
                "audit_synthesis_ref",
                "str",
                "Reviewer audit, validation receipt, or guard ref proving the commit.",
            ),
            ContractField("validation_receipt_id", "str", "Validation receipt id for the staged snapshot."),
            ContractField("guard_action_id", "str", "Guard action id linked to the commit."),
            ContractField("commit_action_id", "str", "Typed commit action id."),
            ContractField("status", "str", "Commit receipt status."),
            ContractField(
                "pre_state",
                "str",
                "Validation state required before commit receipt emission.",
            ),
            ContractField("post_state", "str", "Commit state produced by this receipt."),
            ContractField("recorded_at_utc", "str", "UTC timestamp when the receipt was materialized."),
            ContractField("produced_by", "str", "Actor/tool that produced the receipt."),
            ContractField("artifact_paths", "tuple[str, ...]", "Artifacts emitted by the commit boundary."),
            ContractField("evidence_refs", "tuple[str, ...]", "Refs proving the commit evidence chain."),
            ContractField(
                "role_review_roles",
                "tuple[str, ...]",
                "Review roles backed by explicit RoleReviewAssignmentLifecycle evidence.",
            ),
            ContractField(
                "role_review_receipt_refs",
                "tuple[str, ...]",
                "Terminal RoleReviewReceipt refs bound to the commit receipt.",
            ),
            ContractField(
                "role_review_timeout_refs",
                "tuple[str, ...]",
                "Terminal RoleReviewTimeout refs bound to the commit receipt.",
            ),
            ContractField("correlation_id", "str", "Parent lineage shared across related receipts."),
            ContractField("causation_id", "str", "Immediate trigger lineage for this receipt."),
            ContractField("run_id", "str", "Bounded run lineage for this receipt."),
        ),
        runtime_model="dev.scripts.devctl.runtime.commit_receipt:CommitReceipt",
        startup_surface_tokens=("receipt_id", "commit_sha", "reviewer_ack_packet_id"),
    ),
    ContractSpec(
        contract_id="BranchOperationReceipt",
        owner_layer="governance_runtime",
        purpose=(
            "Typed evidence for one git branch mutation, binding the branch name, "
            "operation, before/after refs, actor, and proof refs so branch state "
            "changes do not bypass governance receipts."
        ),
        required_fields=(
            ContractField("receipt_id", "str", "Stable receipt id for the branch operation."),
            ContractField("branch_name", "str", "Branch ref name being mutated."),
            ContractField("operation", "str", "Branch operation such as create, update, delete, or checkout."),
            ContractField("new_ref", "str", "Resulting branch ref or empty ref after deletion."),
            ContractField("previous_ref", "str", "Prior branch ref when known."),
            ContractField("remote_name", "str", "Remote namespace when the branch operation is remote-bound."),
            ContractField("executed_by_actor", "str", "Actor/tool that performed the branch operation."),
            ContractField("executed_at_utc", "str", "UTC timestamp for the operation."),
            ContractField("evidence_refs", "tuple[str, ...]", "Refs proving command output or authority."),
            ContractField("status", "str", "Recorded status for the branch operation receipt."),
        ),
        runtime_model=_BRANCH_OPERATION_RECEIPT_RUNTIME_MODEL,
        startup_surface_tokens=("branch_name", "operation", "new_ref"),
    ),
    ContractSpec(
        contract_id="TagReceipt",
        owner_layer="governance_runtime",
        purpose=(
            "Typed evidence for one git tag mutation, binding tag name, operation, "
            "target SHA, prior target when known, actor, and proof refs so release "
            "tag state is inspectable by governance."
        ),
        required_fields=(
            ContractField("receipt_id", "str", "Stable receipt id for the tag operation."),
            ContractField("tag_name", "str", "Git tag name being created, moved, or deleted."),
            ContractField("operation", "str", "Tag operation such as create, update, or delete."),
            ContractField("target_sha", "str", "Tag target SHA after the operation."),
            ContractField("previous_target_sha", "str", "Prior tag target when known."),
            ContractField("tagger_actor", "str", "Actor/tool that performed the tag operation."),
            ContractField("executed_at_utc", "str", "UTC timestamp for the operation."),
            ContractField("evidence_refs", "tuple[str, ...]", "Refs proving command output or authority."),
            ContractField("status", "str", "Recorded status for the tag receipt."),
        ),
        runtime_model=_TAG_RECEIPT_RUNTIME_MODEL,
        startup_surface_tokens=("tag_name", "operation", "target_sha"),
    ),
    ContractSpec(
        contract_id="FeatureProofReceipt",
        owner_layer="governance_runtime",
        purpose=(
            "Operator-facing per-feature proof receipt binding a feature slice, "
            "commit SHA, review fleet roles, tests, connectivity guards, dogfood "
            "evidence, and bypass audit refs."
        ),
        required_fields=(
            ContractField(
                "feature_id",
                "str",
                "Plan row or feature slice proven by the receipt.",
            ),
            ContractField("commit_sha", "str", "Commit SHA being proven."),
            ContractField("implementer_actor", "str", "Actor that shipped the commit."),
            ContractField(
                "review_fleet_roles_ran",
                "tuple[str, ...]",
                "Review fleet roles with evidence in the proof chain.",
            ),
            ContractField(
                "review_fleet_actor",
                "str",
                "Actor or channel that reviewed the work.",
            ),
            ContractField(
                "tests_run",
                "tuple[str, ...]",
                "Test or validation commands/refs executed.",
            ),
            ContractField(
                "tests_passed_count",
                "int",
                "Number of tests or validation groups that passed.",
            ),
            ContractField(
                "tests_failed_count",
                "int",
                "Number of tests or validation groups that failed.",
            ),
            ContractField(
                "connectivity_guards_ran",
                "tuple[str, ...]",
                "Connectivity guards proving the feature composes with the system.",
            ),
            ContractField(
                "connectivity_guards_passed",
                "bool",
                "Whether connectivity guards passed.",
            ),
            ContractField(
                "dogfood_invocation_evidence_ref",
                "str",
                "Artifact or receipt ref proving live invocation evidence.",
            ),
            ContractField("real_life_test_status", "str", "Real-life dogfood status."),
            ContractField(
                "not_tested_rationale",
                "str | None",
                "Required rationale when real-life testing is not available.",
            ),
            ContractField(
                "bypass_audit_trail_refs",
                "tuple[str, ...]",
                "Bypass or governed exception refs composed into the proof.",
            ),
            ContractField(
                "proven_at_utc",
                "str",
                "UTC timestamp when the proof was materialized.",
            ),
            ContractField(
                "evidence_artifacts",
                "tuple[str, ...]",
                "Artifact paths supporting the proof.",
            ),
            ContractField(
                "role_review_receipt_refs",
                "tuple[str, ...]",
                "Terminal RoleReviewReceipt refs proving declared role reviews.",
            ),
            ContractField(
                "role_review_timeout_refs",
                "tuple[str, ...]",
                "Terminal RoleReviewTimeout refs proving typed fallback when review timed out.",
            ),
        ),
        runtime_model="dev.scripts.devctl.runtime.feature_proof_receipt:FeatureProofReceipt",
        startup_surface_tokens=("feature_id", "commit_sha", "real_life_test_status"),
    ),
    ContractSpec(
        contract_id="NonTrivialOutputProof",
        owner_layer="governance_runtime",
        purpose=(
            "Substantive proof verdict for one FeatureProofReceipt, requiring "
            "resolved evidence refs, real pytest-node test evidence, and "
            "non-circular proof artifacts."
        ),
        required_fields=(
            ContractField("ref_resolves", "bool", "Whether evidence refs resolve on disk."),
            ContractField("has_real_tests", "bool", "Whether tests_run contains pytest node ids."),
            ContractField("not_circular", "bool", "Whether evidence avoids circular FPR refs."),
            ContractField(
                "role_review_terminal_refs_present",
                "bool",
                "Whether declared role-review fleet roles have terminal typed refs.",
            ),
            ContractField("failure_reasons", "tuple[str, ...]", "Bounded failed proof axes."),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.feature_proof_output_proof:"
            "NonTrivialOutputProof"
        ),
        startup_surface_tokens=("ref_resolves", "has_real_tests", "not_circular"),
    ),
    ContractSpec(
        contract_id="NonTrivialOutputProofRemediationFinding",
        owner_layer="governance_runtime",
        purpose=(
            "Remediation ledger row for legacy FeatureProofReceipt artifacts "
            "that fail NonTrivialOutputProof validation."
        ),
        required_fields=(
            ContractField("finding_id", "str", "Stable remediation finding id."),
            ContractField(
                "feature_proof_receipt_path",
                "str",
                "FeatureProofReceipt artifact that failed validation.",
            ),
            ContractField("commit_sha", "str", "Commit SHA carried by the FPR."),
            ContractField("feature_id", "str", "Feature or plan row carried by the FPR."),
            ContractField("failure_reasons", "tuple[str, ...]", "Failed proof axes."),
            ContractField("evidence_refs", "tuple[str, ...]", "Refs evaluated by the proof."),
            ContractField("emitted_at_utc", "str", "UTC timestamp for the ledger row."),
            ContractField("remediation_status", "str", "Current remediation state."),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.feature_proof_output_proof:"
            "NonTrivialOutputProofRemediationFinding"
        ),
        startup_surface_tokens=("finding_id", "feature_id", "remediation_status"),
    ),
    ContractSpec(
        contract_id="NonTrivialOutputProofRemediationFindingLedger",
        owner_layer="governance_runtime",
        purpose=(
            "JSONL state artifact contract for the NonTrivialOutputProof "
            "remediation finding ledger."
        ),
        required_fields=(
            ContractField("ledger_path", "str", "Repo-relative JSONL ledger path."),
            ContractField("finding_contract_id", "str", "Line contract stored in the ledger."),
            ContractField("storage_format", "str", "Durable state storage format."),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.feature_proof_output_proof:"
            "NonTrivialOutputProofRemediationFindingLedger"
        ),
        startup_surface_tokens=("ledger_path", "finding_contract_id", "storage_format"),
    ),
    ContractSpec(
        contract_id="TypingCompatUtility",
        owner_layer="governance_runtime",
        purpose=(
            "Compatibility contract for runtime typing helpers used by "
            "typestate exhaustiveness checks across supported Python versions."
        ),
        required_fields=(
            ContractField("exported_symbols", "tuple[str, ...]", "Typing helpers exported."),
            ContractField("compatibility_target", "str", "Stdlib typing API mirrored."),
        ),
        runtime_model="dev.scripts.devctl.runtime.typing_compat:TypingCompatUtility",
        startup_surface_tokens=("exported_symbols", "compatibility_target"),
    ),
    ContractSpec(
        contract_id="PlanRowClosureReceipt",
        owner_layer="governance_runtime",
        purpose=(
            "Typed evidence that a proven raw-git commit was reduced back into "
            "master-plan row state, including commit anchor and applied timestamp."
        ),
        required_fields=(
            ContractField("receipt_id", "str", "Stable closure receipt id."),
            ContractField("plan_row_id", "str", "Plan row reduced by the commit."),
            ContractField("commit_sha", "str", "Commit SHA that proved the row."),
            ContractField(
                "feature_proof_receipt_path",
                "str",
                "FeatureProofReceipt artifact used as reducer input.",
            ),
            ContractField(
                "previous_status",
                "str",
                "Plan row status before reduction.",
            ),
            ContractField("next_status", "str", "Plan row status after reduction."),
            ContractField("outcome", "str", "Bounded reducer outcome."),
            ContractField(
                "commit_anchor_ref",
                "str",
                "Typed commit anchor written or confirmed on the row.",
            ),
            ContractField(
                "applied_at_utc",
                "str",
                "UTC timestamp written or confirmed on the row.",
            ),
            ContractField("plan_index_path", "str", "Plan index authority path."),
            ContractField("reducer", "str", "Reducer id that emitted this receipt."),
            ContractField(
                "composes_with",
                "tuple[str, ...]",
                "Typed role-review/lifecycle proof refs composed into closure.",
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.commit_to_plan_row_reducer:"
            "PlanRowClosureReceipt"
        ),
        startup_surface_tokens=("plan_row_id", "commit_sha", "outcome"),
    ),
)
