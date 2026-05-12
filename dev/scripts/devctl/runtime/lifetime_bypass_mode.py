"""Typed bypass mode receipts for operator-authorized governance exceptions.

Composes with governed_exception_lifecycle.GovernedExceptionLifecycle: bypass
receipts are first-class typed evidence, not bash-permission grants.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from .correlation_spine import correlation_context_for_ref
from .governed_exception_base import json_ready_dict
from .governed_exception_receipts import ExceptionReceipt
from .value_coercion import coerce_string

if TYPE_CHECKING:
    from .governed_exception_lifecycle import (
        GovernedExceptionLifecycle as GovernedExceptionRecord,
    )


BYPASS_EXCEPTION_CLASS = "operator_lifetime_bypass"
BYPASS_GUARD_ID = "lifetime_bypass_mode"


class BypassAuthorityScope(StrEnum):
    EDIT_ONLY = "edit_only"
    EDIT_AND_COMMIT = "edit_and_commit"
    EDIT_COMMIT_AND_PUSH = "edit_commit_and_push"
    AGENT_SPAWN_ONLY = "agent_spawn_only"


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
        return json_ready_dict(asdict(self))


_REGISTERED_BYPASS_RECEIPTS: tuple[BypassReceipt, ...] = ()

_GRANTED_SCOPES: Mapping[BypassAuthorityScope, frozenset[BypassAuthorityScope]] = {
    BypassAuthorityScope.AGENT_SPAWN_ONLY: frozenset(
        {BypassAuthorityScope.AGENT_SPAWN_ONLY}
    ),
    BypassAuthorityScope.EDIT_ONLY: frozenset(
        {
            BypassAuthorityScope.AGENT_SPAWN_ONLY,
            BypassAuthorityScope.EDIT_ONLY,
        }
    ),
    BypassAuthorityScope.EDIT_AND_COMMIT: frozenset(
        {
            BypassAuthorityScope.AGENT_SPAWN_ONLY,
            BypassAuthorityScope.EDIT_ONLY,
            BypassAuthorityScope.EDIT_AND_COMMIT,
        }
    ),
    BypassAuthorityScope.EDIT_COMMIT_AND_PUSH: frozenset(
        {
            BypassAuthorityScope.AGENT_SPAWN_ONLY,
            BypassAuthorityScope.EDIT_ONLY,
            BypassAuthorityScope.EDIT_AND_COMMIT,
            BypassAuthorityScope.EDIT_COMMIT_AND_PUSH,
        }
    ),
}

_ACTION_KIND_BY_SCOPE: Mapping[BypassAuthorityScope, str] = {
    BypassAuthorityScope.AGENT_SPAWN_ONLY: "runtime.spawn",
    BypassAuthorityScope.EDIT_ONLY: "runtime.mutate",
    BypassAuthorityScope.EDIT_AND_COMMIT: "vcs.commit",
    BypassAuthorityScope.EDIT_COMMIT_AND_PUSH: "vcs.push",
}


def grant_lifetime_bypass(receipt: BypassReceipt) -> "GovernedExceptionRecord":
    """Grant bypass authority through the governed exception lifecycle."""
    from .governed_exception_lifecycle import GovernedExceptionLifecycle

    authority_refs = (
        f"bypass_receipt:{receipt.receipt_id}",
        f"operator:{receipt.granted_by_operator_actor_id}",
        receipt.ai_approval_evidence,
    )
    worktree_refs = (f"requested_authority_scope:{receipt.requested_authority_scope}",)
    exception_receipt_id = f"exception:{receipt.receipt_id}"
    exception_context = correlation_context_for_ref(
        "exception_receipt",
        exception_receipt_id,
        causation_kind="bypass_receipt",
        causation_ref_value=receipt.receipt_id,
        run_kind="validation_plan",
        run_ref_value="MP377-LIFETIME-BYPASS-MODE-S1",
    )
    exception = ExceptionReceipt(
        receipt_id=exception_receipt_id,
        action_kind=_ACTION_KIND_BY_SCOPE[receipt.requested_authority_scope],
        phase="operator_bypass_authorization",
        guard_id=BYPASS_GUARD_ID,
        exception_class=BYPASS_EXCEPTION_CLASS,
        operator_reason=receipt.reason,
        head=f"bypass:{receipt.receipt_id}",
        scope=receipt.requested_authority_scope,
        planned_finding_ingest_ref=f"bypass_receipt:{receipt.receipt_id}",
        authority_evidence_refs=authority_refs,
        worktree_safety_evidence_refs=worktree_refs,
        validation_plan_id="MP377-LIFETIME-BYPASS-MODE-S1",
        execution_status="operator_approved",
        expires_at_utc=receipt.expires_at_utc,
        created_at_utc=receipt.granted_at_utc,
        correlation_id=exception_context.correlation_id,
        causation_id=exception_context.causation_id,
        run_id=exception_context.run_id,
    )
    lifecycle = GovernedExceptionLifecycle(
        lifecycle_id=f"gel:bypass:{receipt.receipt_id}",
        status="operator_approved",
        exception=exception,
        planned_finding_ingest_ref=f"bypass_receipt:{receipt.receipt_id}",
        validation_plan_id="MP377-LIFETIME-BYPASS-MODE-S1",
        authority_evidence_refs=authority_refs,
        worktree_safety_evidence_refs=worktree_refs,
        system_map_contract_ids=("GovernedExceptionLifecycle", "BypassReceipt"),
        developer_loop_refs=(receipt.ai_approval_evidence,),
        created_at_utc=receipt.granted_at_utc,
        updated_at_utc=receipt.granted_at_utc,
    )
    _register_bypass_receipt(receipt)
    return lifecycle


def is_bypass_active(receipt_id: str, action_class: BypassAuthorityScope) -> bool:
    """Return True iff a registered receipt grants the action and is current."""
    receipt = _find_registered_receipt(receipt_id)
    if receipt is None:
        return False
    return bypass_receipt_active(receipt) and bypass_receipt_grants_scope(
        receipt, action_class
    )


def bypass_receipt_from_mapping(mapping: Mapping[str, object]) -> BypassReceipt:
    """Parse a JSONL row into typed BypassReceipt."""
    raw_scope = coerce_string(mapping.get("requested_authority_scope"))
    try:
        scope = BypassAuthorityScope(raw_scope)
    except ValueError as exc:
        raise ValueError(f"unknown_bypass_authority_scope: {raw_scope}") from exc
    return BypassReceipt(
        receipt_id=coerce_string(mapping.get("receipt_id")),
        reason=coerce_string(mapping.get("reason")),
        operator_signature=coerce_string(mapping.get("operator_signature")),
        ai_approval_evidence=coerce_string(mapping.get("ai_approval_evidence")),
        requested_authority_scope=scope,
        granted_at_utc=coerce_string(mapping.get("granted_at_utc")),
        granted_by_operator_actor_id=coerce_string(
            mapping.get("granted_by_operator_actor_id")
        ),
        expires_at_utc=coerce_string(mapping.get("expires_at_utc")),
        revoked_at_utc=coerce_string(mapping.get("revoked_at_utc")),
        revoked_reason=coerce_string(mapping.get("revoked_reason")),
    )


def bypass_receipt_active(
    receipt: BypassReceipt, *, now_utc: datetime | None = None
) -> bool:
    """Return whether the receipt is currently usable."""
    if receipt.revoked_at_utc:
        return False
    if not receipt.expires_at_utc:
        return True
    expires_at = _parse_utc(receipt.expires_at_utc)
    if expires_at is None:
        return False
    effective_now = now_utc or datetime.now(UTC)
    if effective_now.tzinfo is None:
        effective_now = effective_now.replace(tzinfo=UTC)
    return expires_at > effective_now.astimezone(UTC)


def bypass_receipt_grants_scope(
    receipt: BypassReceipt, action_class: BypassAuthorityScope
) -> bool:
    """Return whether receipt scope includes the requested action class."""
    return action_class in _GRANTED_SCOPES[receipt.requested_authority_scope]


def _register_bypass_receipt(receipt: BypassReceipt) -> None:
    global _REGISTERED_BYPASS_RECEIPTS
    retained = tuple(
        existing
        for existing in _REGISTERED_BYPASS_RECEIPTS
        if existing.receipt_id != receipt.receipt_id
    )
    _REGISTERED_BYPASS_RECEIPTS = retained + (receipt,)


def _find_registered_receipt(receipt_id: str) -> BypassReceipt | None:
    for receipt in reversed(_REGISTERED_BYPASS_RECEIPTS):
        if receipt.receipt_id == receipt_id:
            return receipt
    return None


def _parse_utc(value: str) -> datetime | None:
    normalized = value.strip()
    if not normalized:
        return None
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


__all__ = [
    "BYPASS_EXCEPTION_CLASS",
    "BYPASS_GUARD_ID",
    "BypassAuthorityScope",
    "BypassReceipt",
    "bypass_receipt_active",
    "bypass_receipt_from_mapping",
    "bypass_receipt_grants_scope",
    "grant_lifetime_bypass",
    "is_bypass_active",
]
