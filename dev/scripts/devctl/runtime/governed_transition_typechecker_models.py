"""Contracts for governed transition typestate checks."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime

from .enum_compat import StrEnum


class GovernedTransitionErrorCode(StrEnum):
    """Machine-readable failure codes for governed transition checks."""

    UNKNOWN_OLD_STATUS = "unknown_old_status"
    UNKNOWN_NEW_STATUS = "unknown_new_status"
    ILLEGAL_TRANSITION = "illegal_transition"
    MISSING_RESOLUTION = "missing_resolution"
    MISSING_CLOSURE_PROOF = "missing_closure_proof"
    MISSING_COMPOSED_REF = "missing_composed_ref"
    MISMATCHED_LIFECYCLE_ID = "mismatched_lifecycle_id"
    STALE_COMMIT_ANCHOR = "stale_commit_anchor"
    BYPASS_NOT_EXPIRED = "bypass_not_expired"
    BYPASS_NOT_LINKED_TO_EXCEPTION = "bypass_not_linked_to_exception"
    ALREADY_CLOSED_NON_IDEMPOTENT = "already_closed_non_idempotent"


@dataclass(frozen=True, slots=True)
class GovernedTransitionInput:
    before: object
    after: object
    event_kind: str
    evidence_index: Mapping[str, object] | None = None
    closure_proof: object | None = None
    bypass_lifecycle: object | None = None
    bypass_expiry: object | None = None
    now_utc: datetime | None = None


@dataclass(frozen=True, slots=True)
class GovernedTransitionError:
    code: GovernedTransitionErrorCode
    message: str
    lifecycle_id: str
    composed_ref: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["code"] = self.code.value
        return payload


@dataclass(frozen=True, slots=True)
class IllegalTransition:
    old_status: str
    event_kind: str
    new_status: str
    lifecycle_id: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class StaleProofRef:
    proof_kind: str
    ref: str
    lifecycle_id: str
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GovernedTransitionCheck:
    """Result of a nontrivial governed lifecycle transition check."""

    ok: bool
    errors: tuple[GovernedTransitionError, ...]
    missing_refs: tuple[str, ...]
    illegal_transitions: tuple[IllegalTransition, ...]
    stale_proofs: tuple[StaleProofRef, ...]
    inputs_scanned: int
    assertions_evaluated: int

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {"contract_id": "GovernedTransitionCheck"}
        payload.update(asdict(self))
        payload["errors"] = [error.to_dict() for error in self.errors]
        payload["missing_refs"] = list(self.missing_refs)
        payload["illegal_transitions"] = [
            transition.to_dict() for transition in self.illegal_transitions
        ]
        payload["stale_proofs"] = [proof.to_dict() for proof in self.stale_proofs]
        return payload


__all__ = [
    "GovernedTransitionCheck",
    "GovernedTransitionError",
    "GovernedTransitionErrorCode",
    "GovernedTransitionInput",
    "IllegalTransition",
    "StaleProofRef",
]
