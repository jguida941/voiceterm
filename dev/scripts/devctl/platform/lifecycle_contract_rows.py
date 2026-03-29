"""Lifecycle contract rows for the reusable governance platform blueprint."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec


RUNTIME_LIFECYCLE_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="LocalServiceEndpoint",
        owner_layer="governance_runtime",
        purpose=(
            "Lifecycle and attach contract for the optional shared local "
            "service/daemon used by VoiceTerm, CLI, desktop, and phone clients."
        ),
        required_fields=(
            ContractField("service_id", "str", "Stable identifier for the shared local service."),
            ContractField(
                "launch_entrypoints",
                "list[str]",
                "Canonical commands or host paths allowed to launch the service.",
            ),
            ContractField(
                "discovery_fields",
                "list[str]",
                "Machine-readable fields clients use to discover and attach to the service.",
            ),
            ContractField(
                "health_signals",
                "list[str]",
                "Required readiness/health fields emitted after attach.",
            ),
            ContractField(
                "shutdown_entrypoints",
                "list[str]",
                "Canonical commands or host paths allowed to stop the service cleanly.",
            ),
        ),
    ),
    ContractSpec(
        contract_id="CallerAuthorityPolicy",
        owner_layer="governance_runtime",
        purpose=(
            "Allowed, staged, approval-required, and forbidden action buckets "
            "for each caller class over the shared backend."
        ),
        required_fields=(
            ContractField(
                "caller_id",
                "str",
                "Stable caller class identifier such as operator or agent.",
            ),
            ContractField(
                "allowed_actions",
                "list[str]",
                "Actions the caller may execute directly through the backend.",
            ),
            ContractField(
                "stage_only_actions",
                "list[str]",
                "Actions the caller may only stage or draft, not auto-apply.",
            ),
            ContractField(
                "approval_required_actions",
                "list[str]",
                "Actions that always require approval or confirmation.",
            ),
            ContractField(
                "forbidden_actions",
                "list[str]",
                "Actions the caller may not execute through the backend.",
            ),
        ),
    ),
)


def runtime_lifecycle_contracts() -> tuple[ContractSpec, ...]:
    """Return lifecycle and caller-authority contract rows."""
    return RUNTIME_LIFECYCLE_CONTRACTS
