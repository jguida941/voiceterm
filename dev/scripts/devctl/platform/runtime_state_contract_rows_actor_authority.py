"""Actor-authority runtime-state contract rows."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec

ACTOR_AUTHORITY_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="CapabilityGrantState",
        owner_layer="governance_runtime",
        purpose=(
            "Identity-bound capability grant for one actor, keeping repo mutation, "
            "stage handoff, review, observation, and approval authority separate."
        ),
        required_fields=(
            ContractField(
                "capability",
                "str",
                "Capability token such as repo.commit or approval.commit.",
            ),
            ContractField(
                "granted", "bool", "Whether this capability is currently granted."
            ),
            ContractField(
                "source", "str", "Typed authority source that produced the grant."
            ),
            ContractField(
                "reason", "str", "Human-readable rationale for the grant or denial."
            ),
            ContractField(
                "target_kind", "str", "Optional target kind bound to the grant."
            ),
            ContractField(
                "target_ref", "str", "Optional target ref bound to the grant."
            ),
            ContractField(
                "target_revision", "str", "Optional target revision bound to the grant."
            ),
            ContractField(
                "worktree_identity", "str", "Worktree identity the grant applies to."
            ),
            ContractField(
                "packet_id", "str", "Packet id linked to the grant, when any."
            ),
            ContractField(
                "approval_ref",
                "str",
                "Approval reference linked to the grant, when any.",
            ),
            ContractField(
                "issued_at_utc", "str", "UTC timestamp when the grant was issued."
            ),
            ContractField(
                "expires_at_utc", "str", "UTC expiry for the grant, when any."
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.review_state_collaboration_models:"
            "CapabilityGrantState"
        ),
        startup_surface_tokens=("capability", "granted", "source"),
    ),
    ContractSpec(
        contract_id="ActorAuthorityState",
        owner_layer="governance_runtime",
        purpose=(
            "Principal-actor authority row that binds live actor identity to "
            "explicit capability grants instead of inferring writability from role labels."
        ),
        required_fields=(
            ContractField("actor_id", "str", "Stable actor id for the principal."),
            ContractField("provider", "str", "Concrete provider backing the actor."),
            ContractField("role", "str", "Typed runtime role for this authority row."),
            ContractField(
                "session_id",
                "str",
                "Runtime session id that scopes role authority when available.",
            ),
            ContractField(
                "live",
                "bool",
                "Whether the actor is live under typed runtime evidence.",
            ),
            ContractField("status", "str", "Actor status used by authority consumers."),
            ContractField(
                "source",
                "str",
                "Typed runtime source that produced this authority row.",
            ),
            ContractField(
                "grants",
                "tuple[CapabilityGrantState, ...]",
                "Explicit capability grants for this actor.",
            ),
            ContractField("source_contract", "str", "Contract that emitted this row."),
            ContractField(
                "source_identity",
                "dict[str, str]",
                "Producer identity tuple bound to this row.",
            ),
            ContractField(
                "snapshot_id", "str", "Surface snapshot id bound to this row."
            ),
            ContractField(
                "zref", "str", "Compact surface reference bound to this row."
            ),
            ContractField(
                "generation_id", "str", "Runtime generation id bound to this row."
            ),
            ContractField(
                "worktree_identity", "str", "Worktree identity this row applies to."
            ),
            ContractField(
                "packet_id", "str", "Packet id linked to this row, when any."
            ),
            ContractField(
                "approval_ref", "str", "Approval ref linked to this row, when any."
            ),
            ContractField(
                "issued_at_utc", "str", "UTC timestamp when this row was issued."
            ),
            ContractField(
                "expires_at_utc", "str", "UTC expiry for this row, when any."
            ),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.review_state_collaboration_models:"
            "ActorAuthorityState"
        ),
        startup_surface_tokens=("actor_id", "role", "session_id", "grants"),
    ),
)
