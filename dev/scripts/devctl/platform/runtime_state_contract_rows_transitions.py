"""Governed transition platform contract rows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .contracts import ContractField, ContractSpec

if TYPE_CHECKING:
    from ..runtime.governed_transition_typechecker_models import (
        GovernedTransitionCheck,
        GovernedTransitionError,
        GovernedTransitionInput,
        IllegalTransition,
        StaleProofRef,
    )
    from ..runtime.governed_transitions import (
        GovernedTransitionModule,
        TransitionContract,
    )

    _RUNTIME_MODEL_REFS: tuple[
        type[GovernedTransitionCheck],
        type[GovernedTransitionError],
        type[GovernedTransitionInput],
        type[GovernedTransitionModule],
        type[IllegalTransition],
        type[StaleProofRef],
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
    ContractSpec(
        contract_id="GovernedTransitionInput",
        owner_layer="governance_runtime",
        purpose=(
            "Input envelope for checking a governed exception lifecycle "
            "transition against typed evidence and optional bypass lifecycle proof."
        ),
        required_fields=(
            ContractField("before", "object", "Pre-transition lifecycle object."),
            ContractField("after", "object", "Post-transition lifecycle object."),
            ContractField("event_kind", "str", "Typed transition event kind."),
            ContractField(
                "evidence_index",
                "Mapping[str, object] | None",
                "Evidence refs available to the transition checker.",
            ),
            ContractField(
                "closure_proof",
                "object | None",
                "Optional closure proof override for post-state validation.",
            ),
            ContractField(
                "bypass_lifecycle",
                "object | None",
                "Optional bypass lifecycle proof for bypass expiry closure.",
            ),
            ContractField(
                "bypass_expiry",
                "object | None",
                "Optional bypass expiry proof for time-bound closure.",
            ),
            ContractField(
                "now_utc",
                "datetime | None",
                "Clock used for deterministic expiry checks.",
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.governed_transition_typechecker_models:"
            "GovernedTransitionInput"
        ),
        startup_surface_tokens=("before", "after", "event_kind"),
    ),
    ContractSpec(
        contract_id="GovernedTransitionError",
        owner_layer="governance_runtime",
        purpose="One typed failure emitted by the governed transition checker.",
        required_fields=(
            ContractField("code", "GovernedTransitionErrorCode", "Typed error code."),
            ContractField("message", "str", "Human-readable failure detail."),
            ContractField("lifecycle_id", "str", "Lifecycle id under validation."),
            ContractField(
                "composed_ref",
                "str",
                "Optional missing or stale composed evidence ref.",
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.governed_transition_typechecker_models:"
            "GovernedTransitionError"
        ),
        startup_surface_tokens=("code", "lifecycle_id"),
    ),
    ContractSpec(
        contract_id="IllegalTransition",
        owner_layer="governance_runtime",
        purpose=(
            "Structured old-status/event/new-status triple rejected by the "
            "governed transition checker."
        ),
        required_fields=(
            ContractField("old_status", "str", "Pre-transition status."),
            ContractField("event_kind", "str", "Transition event kind."),
            ContractField("new_status", "str", "Rejected post-transition status."),
            ContractField("lifecycle_id", "str", "Lifecycle id under validation."),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.governed_transition_typechecker_models:"
            "IllegalTransition"
        ),
        startup_surface_tokens=("old_status", "event_kind", "new_status"),
    ),
    ContractSpec(
        contract_id="StaleProofRef",
        owner_layer="governance_runtime",
        purpose=(
            "Structured proof reference that resolved syntactically but is stale "
            "against the transition evidence index."
        ),
        required_fields=(
            ContractField("proof_kind", "str", "Proof family."),
            ContractField("ref", "str", "Stale proof reference."),
            ContractField("lifecycle_id", "str", "Lifecycle id under validation."),
            ContractField("reason", "str", "Reason the proof is stale."),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.governed_transition_typechecker_models:"
            "StaleProofRef"
        ),
        startup_surface_tokens=("proof_kind", "ref"),
    ),
    ContractSpec(
        contract_id="GovernedTransitionCheck",
        owner_layer="governance_runtime",
        purpose=(
            "Nontrivial result envelope from the governed transition checker, "
            "including typed errors and green-on-empty defense counters."
        ),
        required_fields=(
            ContractField("ok", "bool", "Whether the transition is accepted."),
            ContractField(
                "errors",
                "tuple[GovernedTransitionError, ...]",
                "Typed transition errors.",
            ),
            ContractField("missing_refs", "tuple[str, ...]", "Missing evidence refs."),
            ContractField(
                "illegal_transitions",
                "tuple[IllegalTransition, ...]",
                "Illegal transition triples.",
            ),
            ContractField(
                "stale_proofs",
                "tuple[StaleProofRef, ...]",
                "Stale proof refs.",
            ),
            ContractField("inputs_scanned", "int", "Number of non-empty inputs scanned."),
            ContractField(
                "assertions_evaluated",
                "int",
                "Number of checker assertions evaluated.",
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.governed_transition_typechecker_models:"
            "GovernedTransitionCheck"
        ),
        startup_surface_tokens=("ok", "errors", "assertions_evaluated"),
    ),
)


__all__ = ["TRANSITION_STATE_CONTRACTS"]
