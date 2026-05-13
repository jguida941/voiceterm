"""Commit receipt runtime contract rows for the platform blueprint."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec


COMMIT_RECEIPT_CONTRACTS: tuple[ContractSpec, ...] = (
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
            ContractField("correlation_id", "str", "Parent lineage shared across related receipts."),
            ContractField("causation_id", "str", "Immediate trigger lineage for this receipt."),
            ContractField("run_id", "str", "Bounded run lineage for this receipt."),
        ),
        runtime_model="dev.scripts.devctl.runtime.commit_receipt:CommitReceipt",
        startup_surface_tokens=("receipt_id", "commit_sha", "reviewer_ack_packet_id"),
    ),
)

