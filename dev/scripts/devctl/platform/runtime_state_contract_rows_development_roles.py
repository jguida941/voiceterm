"""Development role-adapter runtime-state contract rows."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec

DEVELOPMENT_ROLE_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="DevelopRoleAdapterSpec",
        owner_layer="governance_runtime",
        purpose=(
            "Provider-facing role shortcut over the shared `/develop` request "
            "model. Codex and Claude adapters share this role-to-mode map."
        ),
        required_fields=(
            ContractField("provider_id", "str", "Provider consuming the adapter."),
            ContractField("role_preset", "str", "Shared `/develop` role preset."),
            ContractField(
                "collaboration_mode",
                "str",
                "Shared collaboration mode paired with the role preset.",
            ),
            ContractField(
                "adapter_command",
                "str",
                "Typed devctl command emitted by a thin provider adapter.",
            ),
            ContractField(
                "authority_source",
                "str",
                "Typed source that owns role/mode authority.",
            ),
            ContractField(
                "backend_surface",
                "str",
                "Backend command surface receiving the provider adapter call.",
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.development_role_adapters:"
            "DevelopRoleAdapterSpec"
        ),
        startup_surface_tokens=("provider_id", "role_preset", "adapter_command"),
    ),
)

__all__ = ["DEVELOPMENT_ROLE_STATE_CONTRACTS"]
