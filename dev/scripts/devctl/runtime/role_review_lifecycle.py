"""Typed role-review assignment lifecycle contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import ClassVar, Literal, cast

from .value_coercion import coerce_mapping, coerce_string, coerce_string_items

ROLE_REVIEW_ASSIGNMENT_LIFECYCLE_CONTRACT_ID = "RoleReviewAssignmentLifecycle"
ROLE_REVIEW_RECEIPT_CONTRACT_ID = "RoleReviewReceipt"
ROLE_REVIEW_TIMEOUT_CONTRACT_ID = "RoleReviewTimeout"
ROLE_REVIEW_SCHEMA_VERSION = 1

RoleReviewAssignmentStatus = Literal["assigned", "reviewed", "timed_out"]
RoleReviewVerdict = Literal[
    "approved",
    "changes_requested",
    "blocked",
    "informational",
]

_VALID_ROLE_REVIEW_ASSIGNMENT_STATUSES = {"assigned", "reviewed", "timed_out"}
_VALID_ROLE_REVIEW_VERDICTS = {
    "approved",
    "changes_requested",
    "blocked",
    "informational",
}


@dataclass(frozen=True, slots=True)
class RoleReviewReceipt:
    """Terminal proof that an assigned review role actually reviewed a packet."""

    contract_id: ClassVar[str] = ROLE_REVIEW_RECEIPT_CONTRACT_ID
    schema_version: ClassVar[int] = ROLE_REVIEW_SCHEMA_VERSION

    role: str
    packet_id: str
    reviewer_actor: str
    verdict: RoleReviewVerdict
    proof_evidence_refs: tuple[str, ...]
    reviewed_at_utc: str

    def __post_init__(self) -> None:
        _require_text("role", self.role)
        _require_text("packet_id", self.packet_id)
        _require_text("reviewer_actor", self.reviewer_actor)
        _require_text("reviewed_at_utc", self.reviewed_at_utc)
        if self.verdict not in _VALID_ROLE_REVIEW_VERDICTS:
            raise ValueError(f"invalid role review verdict: {self.verdict!r}")
        if not self.proof_evidence_refs:
            raise ValueError("proof_evidence_refs must not be empty")

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["contract_id"] = self.contract_id
        payload["schema_version"] = self.schema_version
        payload["proof_evidence_refs"] = list(self.proof_evidence_refs)
        return payload


@dataclass(frozen=True, slots=True)
class RoleReviewTimeout:
    """Terminal proof that an assigned review role expired under fallback authority."""

    contract_id: ClassVar[str] = ROLE_REVIEW_TIMEOUT_CONTRACT_ID
    schema_version: ClassVar[int] = ROLE_REVIEW_SCHEMA_VERSION

    role: str
    packet_id: str
    timed_out_at_utc: str
    fallback_authority: str

    def __post_init__(self) -> None:
        _require_text("role", self.role)
        _require_text("packet_id", self.packet_id)
        _require_text("timed_out_at_utc", self.timed_out_at_utc)
        _require_text("fallback_authority", self.fallback_authority)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["contract_id"] = self.contract_id
        payload["schema_version"] = self.schema_version
        return payload


@dataclass(frozen=True, slots=True)
class RoleReviewAssignmentLifecycle:
    """Lifecycle tying one role-routed packet claim to terminal review evidence."""

    contract_id: ClassVar[str] = ROLE_REVIEW_ASSIGNMENT_LIFECYCLE_CONTRACT_ID
    schema_version: ClassVar[int] = ROLE_REVIEW_SCHEMA_VERSION

    assignment_id: str
    packet_id: str
    assigned_role: str
    assigned_actor: str
    assigned_at_utc: str
    due_at_utc: str
    status: RoleReviewAssignmentStatus
    receipt: RoleReviewReceipt | None
    timeout: RoleReviewTimeout | None
    parent_bypass_lifecycle_ref: str | None
    governed_exception_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text("assignment_id", self.assignment_id)
        _require_text("packet_id", self.packet_id)
        _require_text("assigned_role", self.assigned_role)
        _require_text("assigned_actor", self.assigned_actor)
        _require_text("assigned_at_utc", self.assigned_at_utc)
        _require_text("due_at_utc", self.due_at_utc)
        if self.status not in _VALID_ROLE_REVIEW_ASSIGNMENT_STATUSES:
            raise ValueError(f"invalid role review assignment status: {self.status!r}")
        if self.receipt is not None and self.timeout is not None:
            raise ValueError("receipt and timeout are mutually exclusive")
        if self.status == "reviewed":
            if self.receipt is None:
                raise ValueError("reviewed assignments require RoleReviewReceipt")
            _require_matching_role_review_terminal(
                assigned_role=self.assigned_role,
                packet_id=self.packet_id,
                role=self.receipt.role,
                terminal_packet_id=self.receipt.packet_id,
                terminal_kind="receipt",
            )
        elif self.status == "timed_out":
            if self.timeout is None:
                raise ValueError("timed_out assignments require RoleReviewTimeout")
            _require_matching_role_review_terminal(
                assigned_role=self.assigned_role,
                packet_id=self.packet_id,
                role=self.timeout.role,
                terminal_packet_id=self.timeout.packet_id,
                terminal_kind="timeout",
            )
        elif self.receipt is not None or self.timeout is not None:
            raise ValueError("assigned lifecycle state must not carry terminal evidence")

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["contract_id"] = self.contract_id
        payload["schema_version"] = self.schema_version
        payload["receipt"] = self.receipt.to_dict() if self.receipt is not None else None
        payload["timeout"] = self.timeout.to_dict() if self.timeout is not None else None
        payload["governed_exception_refs"] = list(self.governed_exception_refs)
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload


def role_review_receipt_from_mapping(payload: Mapping[str, object]) -> RoleReviewReceipt:
    """Normalize a mapping into a RoleReviewReceipt."""
    mapping = coerce_mapping(payload)
    return RoleReviewReceipt(
        role=coerce_string(mapping.get("role")),
        packet_id=coerce_string(mapping.get("packet_id")),
        reviewer_actor=coerce_string(mapping.get("reviewer_actor")),
        verdict=_coerce_role_review_verdict(mapping.get("verdict")),
        proof_evidence_refs=coerce_string_items(mapping.get("proof_evidence_refs")),
        reviewed_at_utc=coerce_string(mapping.get("reviewed_at_utc")),
    )


def role_review_timeout_from_mapping(payload: Mapping[str, object]) -> RoleReviewTimeout:
    """Normalize a mapping into a RoleReviewTimeout."""
    mapping = coerce_mapping(payload)
    return RoleReviewTimeout(
        role=coerce_string(mapping.get("role")),
        packet_id=coerce_string(mapping.get("packet_id")),
        timed_out_at_utc=coerce_string(mapping.get("timed_out_at_utc")),
        fallback_authority=coerce_string(mapping.get("fallback_authority")),
    )


def role_review_assignment_lifecycle_from_mapping(
    payload: Mapping[str, object],
) -> RoleReviewAssignmentLifecycle:
    """Normalize a mapping into a RoleReviewAssignmentLifecycle."""
    mapping = coerce_mapping(payload)
    return RoleReviewAssignmentLifecycle(
        assignment_id=coerce_string(mapping.get("assignment_id")),
        packet_id=coerce_string(mapping.get("packet_id")),
        assigned_role=coerce_string(mapping.get("assigned_role")),
        assigned_actor=coerce_string(mapping.get("assigned_actor")),
        assigned_at_utc=coerce_string(mapping.get("assigned_at_utc")),
        due_at_utc=coerce_string(mapping.get("due_at_utc")),
        status=_coerce_role_review_assignment_status(mapping.get("status")),
        receipt=_coerce_role_review_receipt(mapping.get("receipt")),
        timeout=_coerce_role_review_timeout(mapping.get("timeout")),
        parent_bypass_lifecycle_ref=_coerce_optional_string(
            mapping.get("parent_bypass_lifecycle_ref")
        ),
        governed_exception_refs=coerce_string_items(
            mapping.get("governed_exception_refs")
        ),
        evidence_refs=coerce_string_items(mapping.get("evidence_refs")),
    )


def _coerce_role_review_assignment_status(
    value: object,
) -> RoleReviewAssignmentStatus:
    status = coerce_string(value)
    if status not in _VALID_ROLE_REVIEW_ASSIGNMENT_STATUSES:
        raise ValueError(f"invalid role review assignment status: {status!r}")
    return cast(RoleReviewAssignmentStatus, status)


def _coerce_role_review_verdict(value: object) -> RoleReviewVerdict:
    verdict = coerce_string(value)
    if verdict not in _VALID_ROLE_REVIEW_VERDICTS:
        raise ValueError(f"invalid role review verdict: {verdict!r}")
    return cast(RoleReviewVerdict, verdict)


def _coerce_role_review_receipt(value: object) -> RoleReviewReceipt | None:
    mapping = coerce_mapping(value)
    if not mapping:
        return None
    return role_review_receipt_from_mapping(mapping)


def _coerce_role_review_timeout(value: object) -> RoleReviewTimeout | None:
    mapping = coerce_mapping(value)
    if not mapping:
        return None
    return role_review_timeout_from_mapping(mapping)


def _coerce_optional_string(value: object) -> str | None:
    text = coerce_string(value)
    return text if text else None


def _require_text(field_name: str, value: str) -> None:
    if not coerce_string(value):
        raise ValueError(f"{field_name} is required")


def _require_matching_role_review_terminal(
    *,
    assigned_role: str,
    packet_id: str,
    role: str,
    terminal_packet_id: str,
    terminal_kind: str,
) -> None:
    if role != assigned_role:
        raise ValueError(
            f"{terminal_kind} role {role!r} does not match assigned role "
            f"{assigned_role!r}"
        )
    if terminal_packet_id != packet_id:
        raise ValueError(
            f"{terminal_kind} packet {terminal_packet_id!r} does not match "
            f"assignment packet {packet_id!r}"
        )


__all__ = [
    "ROLE_REVIEW_ASSIGNMENT_LIFECYCLE_CONTRACT_ID",
    "ROLE_REVIEW_RECEIPT_CONTRACT_ID",
    "ROLE_REVIEW_SCHEMA_VERSION",
    "ROLE_REVIEW_TIMEOUT_CONTRACT_ID",
    "RoleReviewAssignmentLifecycle",
    "RoleReviewAssignmentStatus",
    "RoleReviewReceipt",
    "RoleReviewTimeout",
    "RoleReviewVerdict",
    "role_review_assignment_lifecycle_from_mapping",
    "role_review_receipt_from_mapping",
    "role_review_timeout_from_mapping",
]
