"""Governed transition platform contract rows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .contracts import ContractField, ContractSpec

if TYPE_CHECKING:
    from ..runtime.governed_transitions import (
        GovernedTransitionModule,
        TransitionContract,
    )

    _RUNTIME_MODEL_REFS: tuple[
        type[GovernedTransitionModule],
        type[TransitionContract],
    ]


TRANSITION_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="GovernedTransitionModule",
        owner_layer="governance_runtime",
        purpose=(
            "Manifest row naming a module that declares governed lifecycle "
            "transition metadata through the shared decorator."
        ),
        required_fields=(
            ContractField("module", "str", "Importable module path."),
            ContractField("required", "bool", "Whether missing imports fail closed."),
        ),
        runtime_model="dev.scripts.devctl.runtime.governed_transitions:GovernedTransitionModule",
        startup_surface_tokens=("module", "required"),
    ),
    ContractSpec(
        contract_id="TransitionContract",
        owner_layer="governance_runtime",
        purpose=(
            "Frozen decorator metadata for one governed lifecycle transition, "
            "including state requirements, produced states, emitted evidence, "
            "and graph path hints."
        ),
        required_fields=(
            ContractField("transition_id", "str", "Stable transition id."),
            ContractField("requires", "tuple[str, ...]", "Required state or contract refs."),
            ContractField("produces", "tuple[str, ...]", "Produced state refs."),
            ContractField("emits", "tuple[str, ...]", "Evidence or contracts emitted."),
            ContractField("graph_path", "tuple[str, ...]", "Expected graph path hints."),
            ContractField(
                "runtime_enforced",
                "bool",
                "Whether the decorator enforces runtime pre/post state refs.",
            ),
            ContractField("owner_module", "str", "Module that owns the decorated function."),
            ContractField("function_name", "str", "Decorated function qualname."),
        ),
        runtime_model="dev.scripts.devctl.runtime.governed_transitions:TransitionContract",
        startup_surface_tokens=("transition_id", "requires", "produces"),
    ),
)


__all__ = ["TRANSITION_STATE_CONTRACTS"]
