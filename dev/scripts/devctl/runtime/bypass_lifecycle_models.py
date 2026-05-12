"""Typed lifecycle models for governed bypass authorization."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from .governed_exception_base import json_ready_dict
from .value_coercion import coerce_mapping, coerce_string, coerce_string_items

if TYPE_CHECKING:
    from .governed_exception_lifecycle import (
        GovernedExceptionLifecycle as GovernedExceptionRecord,
    )

BYPASS_EXCEPTION_CLASS = "operator_lifetime_bypass"
BYPASS_GUARD_ID = "lifetime_bypass_mode"
DEFAULT_BYPASS_LIFECYCLE_STORE_REL = Path("dev/state/bypass_lifecycles.jsonl")


class BypassAuthorityScope(StrEnum):
    EDIT_ONLY = "edit_only"
    EDIT_AND_COMMIT = "edit_and_commit"
    EDIT_COMMIT_AND_PUSH = "edit_commit_and_push"
    AGENT_SPAWN_ONLY = "agent_spawn_only"


class BypassLifecycleState(StrEnum):
    REQUESTED = "bypass_requested"
    EVALUATING = "bypass_evaluating"
    RECEIPT_ISSUED = "bypass_receipt_issued"
    ACTIVE = "bypass_active"
    DENIED = "bypass_denied"
    REVOKED = "bypass_revoked"
    EXPIRED = "bypass_expired"


class BypassEvaluationDecision(StrEnum):
    APPROVED = "approved"
    DENIED = "denied"


class BypassExpirySource(StrEnum):
    TIME_BOUND = "time_bound"
    STOP_ANCHOR = "stop_anchor"
    OPERATOR_REVOKE = "operator_revoke"


@dataclass(frozen=True, slots=True)
class BypassRequest:
    request_id: str
    scope: BypassAuthorityScope
    reason: str
    actor: str
    requested_at_utc: str
    target_role: str = ""
    target_session_id: str = ""
    target_surface: str = ""
    evidence_refs: tuple[str, ...] = ()
    schema_version: int = 1
    contract_id: str = "BypassRequest"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        return json_ready_dict(payload)

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, object]) -> "BypassRequest":
        payload = coerce_mapping(mapping)
        return cls(
            request_id=coerce_string(payload.get("request_id")),
            scope=scope_from_value(payload.get("scope")),
            reason=coerce_string(payload.get("reason")),
            actor=coerce_string(payload.get("actor")),
            requested_at_utc=coerce_string(payload.get("requested_at_utc")),
            target_role=coerce_string(payload.get("target_role")),
            target_session_id=coerce_string(payload.get("target_session_id")),
            target_surface=coerce_string(payload.get("target_surface")),
            evidence_refs=coerce_string_items(payload.get("evidence_refs")),
        )


@dataclass(frozen=True, slots=True)
class BypassEvaluation:
    evaluation_id: str
    request_id: str
    decision: BypassEvaluationDecision
    evaluated_at_utc: str
    evaluator_actor_id: str
    reason: str
    approved_scope: BypassAuthorityScope | None = None
    governed_exception_lifecycle_id: str = ""
    authority_evidence_refs: tuple[str, ...] = ()
    policy_evidence_refs: tuple[str, ...] = ()
    schema_version: int = 1
    contract_id: str = "BypassEvaluation"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        return json_ready_dict(payload)

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, object]) -> "BypassEvaluation":
        payload = coerce_mapping(mapping)
        raw_decision = coerce_string(payload.get("decision"))
        try:
            decision = BypassEvaluationDecision(raw_decision)
        except ValueError as exc:
            raise ValueError(f"unknown_bypass_evaluation_decision: {raw_decision}") from exc
        raw_scope = coerce_string(payload.get("approved_scope"))
        return cls(
            evaluation_id=coerce_string(payload.get("evaluation_id")),
            request_id=coerce_string(payload.get("request_id")),
            decision=decision,
            evaluated_at_utc=coerce_string(payload.get("evaluated_at_utc")),
            evaluator_actor_id=coerce_string(payload.get("evaluator_actor_id")),
            reason=coerce_string(payload.get("reason")),
            approved_scope=scope_from_value(raw_scope) if raw_scope else None,
            governed_exception_lifecycle_id=coerce_string(
                payload.get("governed_exception_lifecycle_id")
            ),
            authority_evidence_refs=coerce_string_items(
                payload.get("authority_evidence_refs")
            ),
            policy_evidence_refs=coerce_string_items(payload.get("policy_evidence_refs")),
        )


@dataclass(frozen=True, slots=True)
class BypassReceipt:
    receipt_id: str
    reason: str
    operator_signature: str
    ai_approval_evidence: str
    requested_authority_scope: BypassAuthorityScope
    granted_at_utc: str
    granted_by_operator_actor_id: str
    expires_at_utc: str = ""
    revoked_at_utc: str = ""
    revoked_reason: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        return json_ready_dict(payload)

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, object]) -> "BypassReceipt":
        payload = coerce_mapping(mapping)
        return cls(
            receipt_id=coerce_string(payload.get("receipt_id")),
            reason=coerce_string(payload.get("reason")),
            operator_signature=coerce_string(payload.get("operator_signature")),
            ai_approval_evidence=coerce_string(payload.get("ai_approval_evidence")),
            requested_authority_scope=scope_from_value(
                payload.get("requested_authority_scope")
            ),
            granted_at_utc=coerce_string(payload.get("granted_at_utc")),
            granted_by_operator_actor_id=coerce_string(
                payload.get("granted_by_operator_actor_id")
            ),
            expires_at_utc=coerce_string(payload.get("expires_at_utc")),
            revoked_at_utc=coerce_string(payload.get("revoked_at_utc")),
            revoked_reason=coerce_string(payload.get("revoked_reason")),
        )


@dataclass(frozen=True, slots=True)
class BypassExpiry:
    expiry_id: str
    receipt_id: str
    expired_at_utc: str
    source: BypassExpirySource
    reason: str
    evidence_refs: tuple[str, ...] = ()
    schema_version: int = 1
    contract_id: str = "BypassExpiry"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        return json_ready_dict(payload)

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, object]) -> "BypassExpiry":
        payload = coerce_mapping(mapping)
        raw_source = coerce_string(payload.get("source"))
        try:
            source = BypassExpirySource(raw_source)
        except ValueError as exc:
            raise ValueError(f"unknown_bypass_expiry_source: {raw_source}") from exc
        return cls(
            expiry_id=coerce_string(payload.get("expiry_id")),
            receipt_id=coerce_string(payload.get("receipt_id")),
            expired_at_utc=coerce_string(payload.get("expired_at_utc")),
            source=source,
            reason=coerce_string(payload.get("reason")),
            evidence_refs=coerce_string_items(payload.get("evidence_refs")),
        )


@dataclass(frozen=True, slots=True)
class BypassLifecycle:
    lifecycle_id: str
    state: BypassLifecycleState
    request: BypassRequest
    evaluation: BypassEvaluation
    receipt: BypassReceipt | None = None
    governed_exception: "GovernedExceptionRecord | None" = None
    expiry: BypassExpiry | None = None
    activation_evidence_refs: tuple[str, ...] = ()
    schema_version: int = 1
    contract_id: str = "BypassLifecycle"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        return json_ready_dict(payload)

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, object]) -> "BypassLifecycle":
        from .governed_exception_lifecycle import GovernedExceptionLifecycle

        payload = coerce_mapping(mapping)
        raw_state = coerce_string(payload.get("state"))
        try:
            state = BypassLifecycleState(raw_state)
        except ValueError as exc:
            raise ValueError(f"unknown_bypass_lifecycle_state: {raw_state}") from exc
        request = payload.get("request")
        evaluation = payload.get("evaluation")
        receipt = payload.get("receipt")
        governed_exception = payload.get("governed_exception")
        expiry = payload.get("expiry")
        return cls(
            lifecycle_id=coerce_string(payload.get("lifecycle_id")),
            state=state,
            request=BypassRequest.from_mapping(
                request if isinstance(request, Mapping) else {}
            ),
            evaluation=BypassEvaluation.from_mapping(
                evaluation if isinstance(evaluation, Mapping) else {}
            ),
            receipt=(
                BypassReceipt.from_mapping(receipt)
                if isinstance(receipt, Mapping)
                else None
            ),
            governed_exception=(
                GovernedExceptionLifecycle.from_mapping(governed_exception)
                if isinstance(governed_exception, Mapping)
                else None
            ),
            expiry=(
                BypassExpiry.from_mapping(expiry)
                if isinstance(expiry, Mapping)
                else None
            ),
            activation_evidence_refs=coerce_string_items(
                payload.get("activation_evidence_refs")
            ),
        )


@dataclass(frozen=True, slots=True)
class BypassLifecycleStoreLoadResult:
    lifecycles: tuple[BypassLifecycle, ...]
    errors: tuple[str, ...] = ()


def scope_from_value(value: object) -> BypassAuthorityScope:
    raw_scope = coerce_string(value)
    try:
        return BypassAuthorityScope(raw_scope)
    except ValueError as exc:
        raise ValueError(f"unknown_bypass_authority_scope: {raw_scope}") from exc


def bypass_receipt_from_mapping(mapping: Mapping[str, object]) -> BypassReceipt:
    parsed = BypassReceipt.from_mapping(mapping)
    return parsed


__all__ = [
    "BYPASS_EXCEPTION_CLASS",
    "BYPASS_GUARD_ID",
    "DEFAULT_BYPASS_LIFECYCLE_STORE_REL",
    "BypassAuthorityScope",
    "BypassEvaluation",
    "BypassEvaluationDecision",
    "BypassExpiry",
    "BypassExpirySource",
    "BypassLifecycle",
    "BypassLifecycleState",
    "BypassLifecycleStoreLoadResult",
    "BypassReceipt",
    "BypassRequest",
    "bypass_receipt_from_mapping",
    "scope_from_value",
]
