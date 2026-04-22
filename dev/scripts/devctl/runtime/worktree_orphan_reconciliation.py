"""Orphan reconciliation packet/action typed contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field

from .value_coercion import (
    coerce_int,
    coerce_mapping,
    coerce_mapping_items,
    coerce_string,
)
from .worktree_orphan_types import (
    ACCEPT_ALL_ORPHAN_SCOPES,
    ORPHAN_RECONCILIATION_ACTIONS,
    enum_value,
)


@dataclass(frozen=True, slots=True)
class OrphanSourceDecision:
    """One per-source operator reconciliation decision."""

    source_ref: str
    chosen_action: str
    action_args: dict[str, object] = field(default_factory=dict)
    rationale: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["action_args"] = dict(self.action_args)
        return payload


@dataclass(frozen=True, slots=True)
class OrphanReconciliationDecision:
    """Packet payload carrying operator intent for orphan reconciliation."""

    decision_id: str
    responds_to_snapshot_hash: str
    per_source_decisions: tuple[OrphanSourceDecision, ...]
    operator_identity: str
    authorization_receipt_ref: str
    governed_execution_plan_id: str
    decided_at_utc: str = ""
    plan_scope_hint: str = ""
    confirmed_issue_id: str = ""
    schema_version: int = 1
    contract_id: str = "OrphanReconciliationDecision"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["per_source_decisions"] = [
            decision.to_dict() for decision in self.per_source_decisions
        ]
        return payload


@dataclass(frozen=True, slots=True)
class AcceptAllOrphansAction:
    """Typed bulk override for classifying orphan debt."""

    action_id: str
    reason: str
    scope: str
    operator_identity: str
    authorization_receipt_ref: str
    requested_at_utc: str = ""
    schema_version: int = 1
    contract_id: str = "AcceptAllOrphansAction"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AcceptAllOrphansReceipt:
    """Typed receipt emitted after accept-all override execution."""

    receipt_id: str
    action_id: str
    scope: str
    affected_orphan_count: int
    emitted_at_utc: str
    schema_version: int = 1
    contract_id: str = "AcceptAllOrphansReceipt"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def orphan_source_decision_from_mapping(value: object) -> OrphanSourceDecision | None:
    payload = coerce_mapping(value)
    if not payload:
        return None
    source_ref = coerce_string(payload.get("source_ref"))
    if not source_ref:
        return None
    return OrphanSourceDecision(
        source_ref=source_ref,
        chosen_action=enum_value(
            coerce_string(payload.get("chosen_action")),
            allowed=ORPHAN_RECONCILIATION_ACTIONS,
            default="ignore_with_receipt",
        ),
        action_args=dict(coerce_mapping(payload.get("action_args"))),
        rationale=coerce_string(payload.get("rationale")),
    )


def orphan_source_decisions_from_mapping(
    value: object,
) -> tuple[OrphanSourceDecision, ...]:
    decisions: list[OrphanSourceDecision] = []
    for item in coerce_mapping_items(value):
        decision = orphan_source_decision_from_mapping(item)
        if decision is not None:
            decisions.append(decision)
    return tuple(decisions)


def orphan_reconciliation_decision_from_mapping(
    value: object,
) -> OrphanReconciliationDecision | None:
    payload = coerce_mapping(value)
    if not payload:
        return None

    contract_id = (
        coerce_string(payload.get("contract_id")) or "OrphanReconciliationDecision"
    )

    return OrphanReconciliationDecision(
        schema_version=coerce_int(payload.get("schema_version")) or 1,
        contract_id=contract_id,
        decision_id=coerce_string(payload.get("decision_id")),
        responds_to_snapshot_hash=coerce_string(
            payload.get("responds_to_snapshot_hash")
        ),
        per_source_decisions=orphan_source_decisions_from_mapping(
            payload.get("per_source_decisions")
        ),
        operator_identity=coerce_string(payload.get("operator_identity")),
        authorization_receipt_ref=coerce_string(
            payload.get("authorization_receipt_ref")
        ),
        governed_execution_plan_id=coerce_string(
            payload.get("governed_execution_plan_id")
        ),
        decided_at_utc=coerce_string(payload.get("decided_at_utc")),
        plan_scope_hint=coerce_string(payload.get("plan_scope_hint")),
        confirmed_issue_id=coerce_string(payload.get("confirmed_issue_id")),
    )


def accept_all_orphans_action_from_mapping(
    value: object,
) -> AcceptAllOrphansAction | None:
    payload = coerce_mapping(value)
    if not payload:
        return None

    action_id = coerce_string(payload.get("action_id"))
    if not action_id:
        return None

    return AcceptAllOrphansAction(
        schema_version=coerce_int(payload.get("schema_version")) or 1,
        contract_id=_accept_all_contract_id(payload, "AcceptAllOrphansAction"),
        action_id=action_id,
        reason=coerce_string(payload.get("reason")),
        scope=_accept_all_scope(payload),
        operator_identity=coerce_string(payload.get("operator_identity")),
        authorization_receipt_ref=coerce_string(
            payload.get("authorization_receipt_ref")
        ),
        requested_at_utc=coerce_string(payload.get("requested_at_utc")),
    )


def accept_all_orphans_receipt_from_mapping(
    value: object,
) -> AcceptAllOrphansReceipt | None:
    payload = coerce_mapping(value)
    if not payload:
        return None

    receipt_id = coerce_string(payload.get("receipt_id"))
    action_id = coerce_string(payload.get("action_id"))
    if not receipt_id or not action_id:
        return None

    return AcceptAllOrphansReceipt(
        schema_version=coerce_int(payload.get("schema_version")) or 1,
        contract_id=_accept_all_contract_id(payload, "AcceptAllOrphansReceipt"),
        receipt_id=receipt_id,
        action_id=action_id,
        scope=_accept_all_scope(payload),
        affected_orphan_count=coerce_int(payload.get("affected_orphan_count")),
        emitted_at_utc=coerce_string(payload.get("emitted_at_utc")),
    )


def _accept_all_scope(payload: Mapping[str, object]) -> str:
    return enum_value(
        coerce_string(payload.get("scope")),
        allowed=ACCEPT_ALL_ORPHAN_SCOPES,
        default="worktree",
    )


def _accept_all_contract_id(payload: Mapping[str, object], default: str) -> str:
    return coerce_string(payload.get("contract_id")) or default


__all__ = [
    "AcceptAllOrphansAction",
    "AcceptAllOrphansReceipt",
    "OrphanReconciliationDecision",
    "OrphanSourceDecision",
    "accept_all_orphans_action_from_mapping",
    "accept_all_orphans_receipt_from_mapping",
    "orphan_reconciliation_decision_from_mapping",
    "orphan_source_decisions_from_mapping",
]
