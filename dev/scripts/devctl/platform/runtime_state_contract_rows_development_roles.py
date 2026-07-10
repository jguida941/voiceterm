"""Development role-adapter runtime-state contract rows."""

from __future__ import annotations

from ..runtime.role_profile import OperatorDirectivePacket
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
    ContractSpec(
        contract_id="OperatorDirectivePacket",
        owner_layer="governance_runtime",
        purpose=(
            "Typed operator directive envelope carrying source role, target "
            "role/session, scope, capability, evidence, and expiry metadata "
            "across packet and runtime attention boundaries."
        ),
        required_fields=(
            ContractField("directive_id", "str", "Stable directive id."),
            ContractField("operator_role", "str", "Typed operator source role."),
            ContractField("issued_by", "str", "Actor or source issuing the directive."),
            ContractField("target_role", "str", "Target runtime role."),
            ContractField("target_session_id", "str", "Optional exact target session."),
            ContractField("scope", "str", "Directive authority scope."),
            ContractField("summary", "str", "Short operator-facing summary."),
            ContractField("body", "str", "Directive body or packet text."),
            ContractField("capabilities", "tuple[str, ...]", "Granted capability labels."),
            ContractField("evidence_refs", "tuple[str, ...]", "Typed evidence refs."),
            ContractField("issued_at_utc", "str", "Directive issuance timestamp."),
            ContractField("expires_at_utc", "str", "Optional expiry timestamp."),
        ),
        runtime_model=(
            f"{OperatorDirectivePacket.__module__}:"
            f"{OperatorDirectivePacket.__qualname__}"
        ),
        startup_surface_tokens=("directive_id", "operator_role", "scope"),
        registry_entry_kind="authority_composition",
    ),
)

__all__ = ["DEVELOPMENT_ROLE_STATE_CONTRACTS"]
