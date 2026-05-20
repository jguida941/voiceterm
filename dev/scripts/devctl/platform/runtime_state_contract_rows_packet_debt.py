"""Packet-debt runtime-state contract rows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .contracts import ContractField, ContractSpec

if TYPE_CHECKING:
    from ..runtime.packet_debt_remediation_contracts import (
        DecidedPacketDebtDetector,
        PacketBatchTriage,
        PacketBatchTriageRow,
        PacketDebtRemediationReport,
        PacketDebtRemediationRow,
        PacketDurableIngestionReceipt,
    )
    from ..runtime.packet_attention_drain_report import PacketAttentionDrainReport
    from ..runtime.packet_observation_receipt import PacketObservationReceipt

    _RUNTIME_MODEL_REFS: tuple[
        type[DecidedPacketDebtDetector],
        type[PacketAttentionDrainReport],
        type[PacketBatchTriage],
        type[PacketBatchTriageRow],
        type[PacketDebtRemediationReport],
        type[PacketDebtRemediationRow],
        type[PacketDurableIngestionReceipt],
        type[PacketObservationReceipt],
    ]

PACKET_DEBT_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="PacketAttentionDrainReport",
        owner_layer="governance_runtime",
        purpose=(
            "Typed report proving packet body observation changed or preserved "
            "the actor-scoped packet-attention queue."
        ),
        required_fields=(
            ContractField("drain_report_id", "str", "Stable drain report id."),
            ContractField("observer_actor_id", "str", "Actor that opened the packet."),
            ContractField("observer_role_id", "str", "Role used for scoped attention."),
            ContractField(
                "observer_session_id",
                "str",
                "Session used for scoped attention.",
            ),
            ContractField("generated_at_utc", "str", "UTC report timestamp."),
            ContractField(
                "before_pending_packet_count",
                "int",
                "Pending packet count before observation.",
            ),
            ContractField(
                "before_unopened_packet_ids",
                "tuple[str, ...]",
                "Body-open packet ids before observation.",
            ),
            ContractField(
                "after_pending_packet_count",
                "int",
                "Pending packet count after observation.",
            ),
            ContractField(
                "after_unopened_packet_ids",
                "tuple[str, ...]",
                "Body-open packet ids after observation.",
            ),
            ContractField(
                "drained_packet_ids",
                "tuple[str, ...]",
                "Packet ids removed from body-open attention.",
            ),
            ContractField(
                "remaining_blocker_packet_id",
                "str",
                "Next packet still blocking the actor, when present.",
            ),
            ContractField(
                "remaining_required_action",
                "str",
                "Next lifecycle action still required, when present.",
            ),
            ContractField(
                "observation_receipt_refs",
                "tuple[str, ...]",
                "PacketObservationReceipt ids used as source evidence.",
            ),
            ContractField(
                "source_receipts",
                "tuple[PacketObservationReceipt, ...]",
                "Structured receipt rows available to typed consumers.",
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.packet_attention_drain_report:"
            "PacketAttentionDrainReport"
        ),
        startup_surface_tokens=("drained_packet_ids", "remaining_required_action"),
    ),
    ContractSpec(
        contract_id="PacketDurableIngestionReceipt",
        owner_layer="governance_runtime",
        purpose=(
            "Typed receipt proving packet-carried plan, finding, guard, probe, "
            "or architecture intent was merged into durable governance state."
        ),
        required_fields=(
            ContractField("packet_id", "str", "Source review packet id."),
            ContractField("status", "str", "inserted, updated, already_present, or failed."),
            ContractField("reason", "str", "Machine-readable ingestion reason."),
            ContractField("target_kind", "str", "Durable sink kind such as plan_row."),
            ContractField("target_ref", "str", "Plan, finding, guard, or policy target ref."),
            ContractField("binding_target_kind", "str", "Concrete durable target kind."),
            ContractField("binding_target", "str", "Concrete durable row or artifact id."),
            ContractField("path", "str", "Typed store path written by ingestion."),
            ContractField("projection_path", "str", "Human projection path updated."),
            ContractField("event_id", "str", "Review-channel event id for receipt."),
            ContractField("recorded_at_utc", "str", "UTC timestamp for receipt event."),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.packet_debt_remediation_contracts:"
            "PacketDurableIngestionReceipt"
        ),
        startup_surface_tokens=("packet_id", "status", "target_kind", "binding_target"),
    ),
    ContractSpec(
        contract_id="DecidedPacketDebtDetector",
        owner_layer="governance_runtime",
        purpose=(
            "Detector summary for ACKed packets that have been decided in "
            "transport but still lack terminal or durable ownership evidence."
        ),
        required_fields=(
            ContractField("reason", "str", "Debt reason being detected."),
            ContractField("total_count", "int", "Total matching decided packets."),
            ContractField("sample_packet_ids", "tuple[str, ...]", "Bounded examples."),
            ContractField("kind_counts", "dict[str, int]", "Counts by packet kind."),
            ContractField("status_counts", "dict[str, int]", "Counts by packet status."),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.packet_debt_remediation_contracts:"
            "DecidedPacketDebtDetector"
        ),
        startup_surface_tokens=("total_count", "sample_packet_ids", "kind_counts"),
    ),
    ContractSpec(
        contract_id="PacketBatchTriageRow",
        owner_layer="governance_runtime",
        purpose=(
            "One clustered packet-debt batch sharing a reason, target, and "
            "recommended durable-ingestion route."
        ),
        required_fields=(
            ContractField("cluster_id", "str", "Stable debt-cluster id."),
            ContractField("reason", "str", "Carry-forward debt reason."),
            ContractField("recommended_action", "str", "Next remediation route."),
            ContractField("target_ref", "str", "Durable target ref for the batch."),
            ContractField("packet_count", "int", "Packets in this batch."),
            ContractField("sample_packet_ids", "tuple[str, ...]", "Bounded examples."),
            ContractField("kind_counts", "dict[str, int]", "Counts by packet kind."),
            ContractField("status_counts", "dict[str, int]", "Counts by packet status."),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.packet_debt_remediation_contracts:"
            "PacketBatchTriageRow"
        ),
        startup_surface_tokens=("cluster_id", "packet_count", "recommended_action"),
    ),
    ContractSpec(
        contract_id="PacketBatchTriage",
        owner_layer="governance_runtime",
        purpose=(
            "Clustered summary over packet debt so large ACKed packet backlogs "
            "can be drained by batch class instead of one packet at a time."
        ),
        required_fields=(
            ContractField("rows", "tuple[PacketBatchTriageRow, ...]", "Batch rows."),
            ContractField("total_cluster_count", "int", "Total cluster count."),
            ContractField("largest_batch_size", "int", "Largest cluster size."),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.packet_debt_remediation_contracts:"
            "PacketBatchTriage"
        ),
        startup_surface_tokens=("total_cluster_count", "largest_batch_size", "rows"),
    ),
    ContractSpec(
        contract_id="PacketObservationReceipt",
        owner_layer="governance_runtime",
        purpose=(
            "Typed receipt proving one actor/session opened a packet body, "
            "hashed it, and recorded the observation for attention gating."
        ),
        required_fields=(
            ContractField(
                "observation_receipt_id",
                "str",
                "Stable packet observation receipt id.",
            ),
            ContractField("observed_packet_id", "str", "Observed packet id."),
            ContractField("observed_body_sha256", "str", "Observed packet body hash."),
            ContractField("observer_actor_id", "str", "Actor that opened the body."),
            ContractField("observer_role_id", "str", "Role used for observation."),
            ContractField(
                "observer_session_id",
                "str",
                "Session used for observation.",
            ),
            ContractField("observed_at_utc", "str", "Observation timestamp."),
            ContractField("observed_body_length", "int", "Observed body length."),
            ContractField(
                "source_observation_event_id",
                "str",
                "Review-channel packet_body_observed event id.",
            ),
            ContractField(
                "source_packet_event_id",
                "str",
                "Packet event id that carried the body.",
            ),
            ContractField("source_action", "str", "Action that opened the body."),
            ContractField("attention_scope", "str", "Attention scope cleared."),
            ContractField(
                "attention_cleared",
                "bool",
                "Whether this receipt cleared body-open attention.",
            ),
            ContractField(
                "drain_report_ref",
                "str",
                "PacketAttentionDrainReport id when available.",
            ),
            ContractField("evidence_refs", "tuple[str, ...]", "Evidence refs."),
            ContractField(
                "drain_report",
                "PacketAttentionDrainReport | None",
                "Structured drain report when embedded.",
            ),
            ContractField(
                "correlation_context",
                "CorrelationContext",
                "Composed correlation, causation, and run spine ids.",
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.packet_observation_receipt:"
            "PacketObservationReceipt"
        ),
        startup_surface_tokens=("observed_packet_id", "observer_actor_id"),
    ),
    ContractSpec(
        contract_id="PacketDebtRemediationRow",
        owner_layer="governance_runtime",
        purpose=(
            "One packet carry-forward debt row with a deterministic remediation "
            "route and optional durable-ingestion receipt."
        ),
        required_fields=(
            ContractField("packet_id", "str", "Source review packet id."),
            ContractField("reason", "str", "Carry-forward debt reason."),
            ContractField("kind", "str", "Packet kind."),
            ContractField("status", "str", "Packet status."),
            ContractField("lifecycle_state", "str", "Current lifecycle state."),
            ContractField("cluster_id", "str", "Batch triage cluster id."),
            ContractField("recommended_action", "str", "Next remediation route."),
            ContractField("target_ref", "str", "Durable target ref."),
            ContractField("summary", "str", "Packet summary."),
            ContractField(
                "receipt",
                "PacketDurableIngestionReceipt | None",
                "Receipt when remediation writes durable state.",
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.packet_debt_remediation_contracts:"
            "PacketDebtRemediationRow"
        ),
        startup_surface_tokens=("packet_id", "reason", "recommended_action"),
    ),
    ContractSpec(
        contract_id="PacketDebtRemediationReport",
        owner_layer="governance_runtime",
        purpose=(
            "Bounded report clustering packet carry-forward debt and selecting "
            "deterministic durable-ingestion routes before packet transport TTL "
            "can become the only source of intent."
        ),
        required_fields=(
            ContractField("generated_at_utc", "str", "UTC report timestamp."),
            ContractField("source_review_state_path", "str", "ReviewState input path."),
            ContractField("write_enabled", "bool", "Whether durable writes ran."),
            ContractField("rows", "tuple[PacketDebtRemediationRow, ...]", "Debt rows."),
            ContractField(
                "total_debt_count",
                "int",
                "Total matching debt rows before report limit truncation.",
            ),
            ContractField(
                "decided_packet_debt",
                "DecidedPacketDebtDetector | None",
                "ACKed-but-unbuilt packet detector summary.",
            ),
            ContractField(
                "batch_triage",
                "PacketBatchTriage | None",
                "Clustered packet-debt triage summary.",
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.packet_debt_remediation_contracts:"
            "PacketDebtRemediationReport"
        ),
        startup_surface_tokens=(
            "debt_count",
            "total_debt_count",
            "omitted_debt_count",
            "action_counts",
            "receipt_counts",
        ),
    ),
)

__all__ = ["PACKET_DEBT_CONTRACTS"]
