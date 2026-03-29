"""Adapter contract rows for the reusable governance platform blueprint."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec


ADAPTER_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="ProviderAdapter",
        owner_layer="governance_adapters",
        purpose=(
            "Abstracts provider-specific launch/status/fix behavior so loops "
            "do not hard-code Codex or Claude."
        ),
        required_fields=(
            ContractField("provider_id", "str", "Stable provider adapter identifier."),
            ContractField(
                "capabilities",
                "list[str]",
                "Provider features the runtime may rely on.",
            ),
            ContractField(
                "launch_mode",
                "str",
                "How the adapter executes typed actions for the provider.",
            ),
        ),
    ),
    ContractSpec(
        contract_id="WorkflowAdapter",
        owner_layer="governance_adapters",
        purpose=(
            "Abstracts CI/workflow execution so Ralph, mutation, and "
            "review loops stay reusable across repos."
        ),
        required_fields=(
            ContractField("adapter_id", "str", "Stable workflow adapter identifier."),
            ContractField(
                "transport",
                "str",
                "Workflow transport such as local, GitHub, or future CI hosts.",
            ),
            ContractField(
                "allowed_actions",
                "list[str]",
                "Allowlisted workflow actions exposed through the adapter.",
            ),
        ),
    ),
)


def adapter_contracts() -> tuple[ContractSpec, ...]:
    """Return adapter contract rows."""
    return ADAPTER_CONTRACTS
