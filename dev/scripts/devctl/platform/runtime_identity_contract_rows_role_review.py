"""Role-review lifecycle contract rows for the platform blueprint."""

from __future__ import annotations

from ..runtime.role_review_lifecycle import (
    RoleReviewAssignmentLifecycle,
    RoleReviewReceipt,
    RoleReviewTimeout,
)
from .contracts import ContractField, ContractSpec

_ROLE_REVIEW_RECEIPT_RUNTIME_MODEL = (
    f"{RoleReviewReceipt.__module__}:{RoleReviewReceipt.__name__}"
)
_ROLE_REVIEW_TIMEOUT_RUNTIME_MODEL = (
    f"{RoleReviewTimeout.__module__}:{RoleReviewTimeout.__name__}"
)
_ROLE_REVIEW_ASSIGNMENT_LIFECYCLE_RUNTIME_MODEL = (
    f"{RoleReviewAssignmentLifecycle.__module__}:"
    f"{RoleReviewAssignmentLifecycle.__name__}"
)


ROLE_REVIEW_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="RoleReviewReceipt",
        owner_layer="governance_runtime",
        purpose=(
            "Terminal receipt proving that one assigned role reviewed a "
            "role-routed packet with explicit verdict and evidence refs."
        ),
        required_fields=(
            ContractField("role", "str", "Assigned cognitive or review role."),
            ContractField("packet_id", "str", "Role-routed packet under review."),
            ContractField("reviewer_actor", "str", "Actor that performed the review."),
            ContractField("verdict", "str", "Bounded review verdict."),
            ContractField(
                "proof_evidence_refs",
                "tuple[str, ...]",
                "Evidence refs proving the role review was actually performed.",
            ),
            ContractField("reviewed_at_utc", "str", "UTC timestamp for the role review."),
        ),
        runtime_model=_ROLE_REVIEW_RECEIPT_RUNTIME_MODEL,
        startup_surface_tokens=("role", "packet_id", "verdict"),
    ),
    ContractSpec(
        contract_id="RoleReviewTimeout",
        owner_layer="governance_runtime",
        purpose=(
            "Terminal timeout receipt for an assigned role when review did not "
            "arrive before the typed fallback authority took over."
        ),
        required_fields=(
            ContractField("role", "str", "Assigned cognitive or review role."),
            ContractField("packet_id", "str", "Role-routed packet under review."),
            ContractField("timed_out_at_utc", "str", "UTC timestamp when the role timed out."),
            ContractField(
                "fallback_authority",
                "str",
                "Typed authority allowed to continue after role timeout.",
            ),
        ),
        runtime_model=_ROLE_REVIEW_TIMEOUT_RUNTIME_MODEL,
        startup_surface_tokens=("role", "packet_id", "fallback_authority"),
    ),
    ContractSpec(
        contract_id="RoleReviewAssignmentLifecycle",
        owner_layer="governance_runtime",
        purpose=(
            "Lifecycle binding a role-routed packet assignment to exactly one "
            "terminal RoleReviewReceipt or RoleReviewTimeout, with optional "
            "BypassLifecycle and GovernedExceptionLifecycle parent refs."
        ),
        required_fields=(
            ContractField("assignment_id", "str", "Stable role-review assignment id."),
            ContractField("packet_id", "str", "Role-routed packet being reviewed."),
            ContractField("assigned_role", "str", "Role required for the packet."),
            ContractField("assigned_actor", "str", "Actor assigned to that role."),
            ContractField("assigned_at_utc", "str", "UTC timestamp when assigned."),
            ContractField("due_at_utc", "str", "UTC timestamp when review is due."),
            ContractField("status", "str", "assigned, reviewed, or timed_out."),
            ContractField(
                "receipt",
                "RoleReviewReceipt | None",
                "Terminal receipt when the role reviewed the packet.",
            ),
            ContractField(
                "timeout",
                "RoleReviewTimeout | None",
                "Terminal timeout when fallback authority took over.",
            ),
            ContractField(
                "parent_bypass_lifecycle_ref",
                "str | None",
                "Optional parent BypassLifecycle ref for governed fallback authority.",
            ),
            ContractField(
                "governed_exception_refs",
                "tuple[str, ...]",
                "GovernedExceptionLifecycle refs composing with this role review.",
            ),
            ContractField(
                "evidence_refs",
                "tuple[str, ...]",
                "Evidence refs supporting assignment and terminal state.",
            ),
        ),
        runtime_model=_ROLE_REVIEW_ASSIGNMENT_LIFECYCLE_RUNTIME_MODEL,
        startup_surface_tokens=("assignment_id", "packet_id", "status"),
    ),
)


__all__ = ["ROLE_REVIEW_CONTRACTS"]
