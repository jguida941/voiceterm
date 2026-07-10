"""Role-review evidence collection for governed commit receipts."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from .ref_collections import unique_refs as _unique_refs
from .role_review_lifecycle import RoleReviewAssignmentLifecycle
from .value_coercion import coerce_string


@dataclass(frozen=True, slots=True)
class RoleReviewCommitEvidence:
    roles: tuple[str, ...] = ()
    lifecycle_refs: tuple[str, ...] = ()
    receipt_refs: tuple[str, ...] = ()
    timeout_refs: tuple[str, ...] = ()
    parent_refs: tuple[str, ...] = ()
    governed_exception_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()

    @property
    def all_refs(self) -> tuple[str, ...]:
        return (
            *self.lifecycle_refs,
            *self.receipt_refs,
            *self.timeout_refs,
            *self.parent_refs,
            *self.governed_exception_refs,
            *self.evidence_refs,
        )


class FeatureProofReviewRoleEvidence(Protocol):
    role_review_roles: tuple[str, ...]
    reviewer_ack_packet_id: str
    audit_synthesis_ref: str
    validation_receipt_id: str
    evidence_refs: tuple[str, ...]


def collect_role_review_commit_evidence(
    role_review_lifecycles: Iterable[RoleReviewAssignmentLifecycle],
) -> RoleReviewCommitEvidence:
    lifecycles = tuple(role_review_lifecycles)
    roles: list[str] = []
    lifecycle_refs: list[str] = []
    receipt_refs: list[str] = []
    timeout_refs: list[str] = []
    parent_refs: list[str] = []
    governed_exception_refs: list[str] = []
    evidence_refs: list[str] = []
    for lifecycle in lifecycles:
        roles.append(lifecycle.assigned_role)
        lifecycle_refs.append(_ref("role_review_assignment", lifecycle.assignment_id))
        if lifecycle.receipt is not None:
            receipt_refs.append(_receipt_ref(lifecycle))
        if lifecycle.timeout is not None:
            timeout_refs.append(
                _ref(
                    "role_review_timeout",
                    ":".join((lifecycle.timeout.packet_id, lifecycle.timeout.role)),
                )
            )
        if lifecycle.parent_bypass_lifecycle_ref:
            parent_refs.append(lifecycle.parent_bypass_lifecycle_ref)
        governed_exception_refs.extend(lifecycle.governed_exception_refs)
        evidence_refs.extend(lifecycle.evidence_refs)
    return RoleReviewCommitEvidence(
        roles=_unique_refs(roles),
        lifecycle_refs=_unique_refs(lifecycle_refs),
        receipt_refs=_unique_refs(receipt_refs),
        timeout_refs=_unique_refs(timeout_refs),
        parent_refs=_unique_refs(parent_refs),
        governed_exception_refs=_unique_refs(governed_exception_refs),
        evidence_refs=_unique_refs(evidence_refs),
    )


def feature_proof_review_roles(
    commit_receipt: FeatureProofReviewRoleEvidence,
) -> tuple[str, ...]:
    roles = list(commit_receipt.role_review_roles)
    if commit_receipt.reviewer_ack_packet_id:
        roles.append("review_packet_acknowledged")
    if commit_receipt.audit_synthesis_ref or commit_receipt.validation_receipt_id:
        roles.append("GuardsPerRound")
    if commit_receipt.evidence_refs:
        roles.append("evidence_chain_recorded")
    return _unique_refs(roles or ("review_channel_not_recorded",))


def _receipt_ref(lifecycle: RoleReviewAssignmentLifecycle) -> str:
    receipt = lifecycle.receipt
    if receipt is None:
        return ""
    return _ref(
        "role_review_receipt",
        ":".join((receipt.packet_id, receipt.role, receipt.reviewer_actor)),
    )


def _ref(prefix: str, value: str) -> str:
    token = coerce_string(value)
    return f"{prefix}:{token}" if token else ""


__all__ = [
    "FeatureProofReviewRoleEvidence",
    "RoleReviewCommitEvidence",
    "collect_role_review_commit_evidence",
    "feature_proof_review_roles",
]
