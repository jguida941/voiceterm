"""Packet-debt runtime-state contract rows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .contracts import ContractField, ContractSpec

if TYPE_CHECKING:
    from ..runtime.packet_debt_remediation_contracts import (
        PacketDebtRemediationReport,
        PacketDurableIngestionReceipt,
    )

    _RUNTIME_MODEL_REFS: tuple[
        type[PacketDebtRemediationReport],
        type[PacketDurableIngestionReceipt],
    ]

PACKET_DEBT_CONTRACTS: tuple[ContractSpec, ...] = (
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
