"""Packet-pressure contract rows for development-mode runtime state."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec

DEVELOPMENT_PACKET_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="PacketBacklogPressure",
        owner_layer="governance_runtime",
        purpose=(
            "Read-side `/develop` packet pressure summary that makes packet "
            "volume and durable-owner gaps visible without draining packets."
        ),
        required_fields=(
            ContractField("live_total", "int", "Live pending packet count."),
            ContractField("actionable_total", "int", "Selected actionable count."),
            ContractField("near_ttl_total", "int", "Live packets near TTL expiry."),
            ContractField("expired_unresolved_total", "int", "Expired unresolved packets."),
            ContractField("carry_forward_total", "int", "Carry-forward packet debt count."),
            ContractField("durable_owner_gap_total", "int", "Durable intent without owner/receipt."),
            ContractField("per_kind", "dict[str, int]", "Live pressure by kind."),
            ContractField("per_role", "dict[str, int]", "Live pressure by target role/agent."),
            ContractField("selected_packet_ids", "tuple[str, ...]", "Packets selected for classification."),
            ContractField("pressure_state", "str", "below, soft, hard, durable gap, or expired."),
            ContractField("soft_attention_budget", "int", "Repo-pack soft packet budget."),
            ContractField("hard_attention_budget", "int", "Repo-pack hard packet budget."),
            ContractField("near_ttl_minutes", "int", "Repo-pack near-TTL window."),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.development_packet_pressure_models:"
            "PacketBacklogPressure"
        ),
        startup_surface_tokens=(
            "pressure_state",
            "durable_owner_gap_total",
            "selected_packet_ids",
        ),
    ),
    ContractSpec(
        contract_id="PacketIntentClassification",
        owner_layer="governance_runtime",
        purpose=(
            "Selected packet classification used before `/develop` promotes "
            "durable intent into typed state or terminal receipts."
        ),
        required_fields=(
            ContractField("packet_id", "str", "Review-channel packet id."),
            ContractField("kind", "str", "Packet kind."),
            ContractField("status", "str", "Packet transport status."),
            ContractField("to_role", "str", "Target role or agent."),
            ContractField("classification", "str", "Durable/communication/lifecycle class."),
            ContractField("durable_owner", "str", "Existing durable owner when present."),
            ContractField("terminal_receipt", "str", "Terminal receipt/disposition."),
            ContractField("action_required", "bool", "Whether typed owner/receipt is required."),
            ContractField("reason", "str", "Bounded classification reason."),
            ContractField("target_ref", "str", "Typed target reference when present."),
            ContractField("expires_at_utc", "str", "Packet expiry timestamp when present."),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.development_packet_pressure_models:"
            "PacketIntentClassification"
        ),
        startup_surface_tokens=("packet_id", "classification", "action_required"),
    ),
    ContractSpec(
        contract_id="PacketAttentionIngestionDecision",
        owner_layer="governance_runtime",
        purpose=(
            "AgentAttentionLoop packet-ingestion decision derived from selected "
            "classifications and packet-pressure policy."
        ),
        required_fields=(
            ContractField("decision", "str", "continue, pivot, ingest, operator, or fail-closed."),
            ContractField("reason_code", "str", "Machine-readable decision reason."),
            ContractField("required_action", "str", "Required next action."),
            ContractField("fail_closed", "bool", "Whether current work must stop."),
            ContractField("selected_packet_ids", "tuple[str, ...]", "Selected packet ids."),
            ContractField("next_command", "str", "Bounded next command when applicable."),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.development_packet_pressure_models:"
            "PacketAttentionIngestionDecision"
        ),
        startup_surface_tokens=("decision", "reason_code", "next_command"),
    ),
    ContractSpec(
        contract_id="PacketIngestDecision",
        owner_layer="governance_runtime",
        purpose=(
            "Per-packet typed reducer decision that maps one "
            "PacketIntentClassification to the existing ingest-intent, "
            "terminal-receipt, review-channel ACK, defer, or operator-triage path."
        ),
        required_fields=(
            ContractField("packet_id", "str", "Review-channel packet id."),
            ContractField("classification", "str", "PacketIntentClassification value."),
            ContractField("decision", "str", "ingest, ack, terminal receipt, defer, or operator."),
            ContractField("reason_code", "str", "Machine-readable decision reason."),
            ContractField("required_action", "str", "Required next action."),
            ContractField("next_command", "str", "Existing command path for the decision."),
            ContractField("target_kind", "str", "Typed target kind when known."),
            ContractField("target_ref", "str", "Typed target reference when present."),
            ContractField("terminal_status", "str", "Terminal status receipt value when applicable."),
            ContractField("fail_closed", "bool", "Whether packet triage must stop ordinary work."),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.development_packet_pressure_models:"
            "PacketIngestDecision"
        ),
        startup_surface_tokens=("packet_id", "decision", "next_command"),
    ),
)

__all__ = ["DEVELOPMENT_PACKET_STATE_CONTRACTS"]
