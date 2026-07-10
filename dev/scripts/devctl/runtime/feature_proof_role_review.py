"""Role-review terminal coverage helpers for FeatureProofReceipt."""

from __future__ import annotations

from typing import Protocol

from .value_coercion import coerce_string

ROLE_REVIEW_TERMINAL_REQUIRED_ROLES = frozenset(
    (
        "Orchestrator",
        "Watcher",
        "CodexResearch",
        "Implementation",
        "ArchitectureReview",
        "DuplicateScopeGuard",
        "DupGuard",
        "DogfoodTest",
        "GovernanceReceipt",
    )
)


class RoleReviewCoverageReceipt(Protocol):
    role_review_receipt_refs: tuple[str, ...]
    role_review_timeout_refs: tuple[str, ...]
    review_fleet_roles_ran: tuple[str, ...]


def role_review_terminal_coverage_failure_reasons(
    receipt: RoleReviewCoverageReceipt,
) -> tuple[str, ...]:
    """Return missing terminal-review refs for declared role-review fleet roles."""
    role_refs = tuple(receipt.role_review_receipt_refs or ())
    timeout_refs = tuple(receipt.role_review_timeout_refs or ())
    terminal_refs = (*role_refs, *timeout_refs)
    roles = tuple(receipt.review_fleet_roles_ran or ())
    if not terminal_refs:
        return tuple(
            f"missing_role_review_terminal_ref:{role}"
            for role in roles
            if role in ROLE_REVIEW_TERMINAL_REQUIRED_ROLES
        )
    failures: list[str] = []
    for role in roles:
        if role not in ROLE_REVIEW_TERMINAL_REQUIRED_ROLES:
            continue
        if not any(_role_review_ref_matches_role(ref, role) for ref in terminal_refs):
            failures.append(f"missing_role_review_terminal_ref:{role}")
    return tuple(failures)


def _role_review_ref_matches_role(ref: str, role: str) -> bool:
    parts = tuple(part for part in coerce_string(ref).split(":") if part)
    return role in parts[1:]


__all__ = [
    "ROLE_REVIEW_TERMINAL_REQUIRED_ROLES",
    "role_review_terminal_coverage_failure_reasons",
]
