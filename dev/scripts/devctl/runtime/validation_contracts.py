"""Typed validation plan/receipt contracts for governed mutation lanes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass

from .correlation_spine import correlation_context_for_ref, merge_correlation_context
from .value_coercion import (
    coerce_bool,
    coerce_int,
    coerce_mapping,
    coerce_string,
    coerce_string_items,
)


VALIDATION_PLAN_CONTRACT_ID = "ValidationPlan"
VALIDATION_PLAN_SCHEMA_VERSION = 1
VALIDATION_RECEIPT_CONTRACT_ID = "ValidationReceipt"
VALIDATION_RECEIPT_SCHEMA_VERSION = 1

DEFAULT_VALIDATION_INVALIDATION_RULES = (
    "staged_tree_hash_changed",
    "selected_paths_changed",
    "validation_bundle_changed",
    "risk_addons_changed",
)


@dataclass(frozen=True, slots=True)
class ValidationPlan:
    """Tree-bound validation policy selected for one governed pipeline."""

    schema_version: int = VALIDATION_PLAN_SCHEMA_VERSION
    contract_id: str = VALIDATION_PLAN_CONTRACT_ID
    plan_id: str = ""
    bundle_id: str = ""
    staged_tree_hash: str = ""
    selected_paths: tuple[str, ...] = ()
    risk_addons: tuple[str, ...] = ()
    proof_level: str = ""
    checkpoint_required: bool = False
    push_requested: bool = False
    work_intake_ref: str = ""
    invalidation_rules: tuple[str, ...] = DEFAULT_VALIDATION_INVALIDATION_RULES

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["selected_paths"] = list(self.selected_paths)
        payload["risk_addons"] = list(self.risk_addons)
        payload["invalidation_rules"] = list(self.invalidation_rules)
        return payload


@dataclass(frozen=True, slots=True)
class ValidationReceipt:
    """Executed proof evidence for one validation plan."""

    schema_version: int = VALIDATION_RECEIPT_SCHEMA_VERSION
    contract_id: str = VALIDATION_RECEIPT_CONTRACT_ID
    receipt_id: str = ""
    plan_id: str = ""
    bundle_id: str = ""
    staged_tree_hash: str = ""
    action_id: str = ""
    status: str = "unknown"
    reason: str = ""
    findings_count: int = 0
    warnings: tuple[str, ...] = ()
    checkpoint_sufficient: bool = False
    push_sufficient: bool = False
    emitted_at_utc: str = ""
    correlation_id: str = ""
    causation_id: str = ""
    run_id: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["warnings"] = list(self.warnings)
        return payload


def validation_plan_from_mapping(payload: Mapping[str, object]) -> ValidationPlan | None:
    """Normalize a mapping into a typed validation plan."""
    mapping = coerce_mapping(payload)
    if not mapping:
        return None
    plan_id = coerce_string(mapping.get("plan_id"))
    bundle_id = coerce_string(mapping.get("bundle_id"))
    staged_tree_hash = coerce_string(mapping.get("staged_tree_hash"))
    if not plan_id and not bundle_id and not staged_tree_hash:
        return None
    invalidation_rules = coerce_string_items(mapping.get("invalidation_rules"))
    return ValidationPlan(
        schema_version=coerce_int(mapping.get("schema_version"))
        or VALIDATION_PLAN_SCHEMA_VERSION,
        contract_id=coerce_string(mapping.get("contract_id"))
        or VALIDATION_PLAN_CONTRACT_ID,
        plan_id=plan_id,
        bundle_id=bundle_id,
        staged_tree_hash=staged_tree_hash,
        selected_paths=coerce_string_items(mapping.get("selected_paths")),
        risk_addons=coerce_string_items(mapping.get("risk_addons")),
        proof_level=coerce_string(mapping.get("proof_level")),
        checkpoint_required=coerce_bool(mapping.get("checkpoint_required")),
        push_requested=coerce_bool(mapping.get("push_requested")),
        work_intake_ref=coerce_string(mapping.get("work_intake_ref")),
        invalidation_rules=(
            invalidation_rules or DEFAULT_VALIDATION_INVALIDATION_RULES
        ),
    )


def validation_receipt_from_mapping(
    payload: Mapping[str, object],
) -> ValidationReceipt | None:
    """Normalize a mapping into a typed validation receipt."""
    mapping = coerce_mapping(payload)
    if not mapping:
        return None
    receipt_id = coerce_string(mapping.get("receipt_id"))
    plan_id = coerce_string(mapping.get("plan_id"))
    bundle_id = coerce_string(mapping.get("bundle_id"))
    staged_tree_hash = coerce_string(mapping.get("staged_tree_hash"))
    if not receipt_id and not plan_id and not bundle_id and not staged_tree_hash:
        return None
    context = merge_correlation_context(
        mapping,
        correlation_context_for_ref(
            "validation_receipt",
            receipt_id or staged_tree_hash,
            causation_kind="typed_action",
            causation_ref_value=coerce_string(mapping.get("action_id")),
            run_kind="validation_plan",
            run_ref_value=plan_id or bundle_id or staged_tree_hash,
        ).to_dict(),
    )
    return ValidationReceipt(
        schema_version=coerce_int(mapping.get("schema_version"))
        or VALIDATION_RECEIPT_SCHEMA_VERSION,
        contract_id=coerce_string(mapping.get("contract_id"))
        or VALIDATION_RECEIPT_CONTRACT_ID,
        receipt_id=receipt_id,
        plan_id=plan_id,
        bundle_id=bundle_id,
        staged_tree_hash=staged_tree_hash,
        action_id=coerce_string(mapping.get("action_id")),
        status=coerce_string(mapping.get("status")) or "unknown",
        reason=coerce_string(mapping.get("reason")),
        findings_count=coerce_int(mapping.get("findings_count")),
        warnings=coerce_string_items(mapping.get("warnings")),
        checkpoint_sufficient=coerce_bool(mapping.get("checkpoint_sufficient")),
        push_sufficient=coerce_bool(mapping.get("push_sufficient")),
        emitted_at_utc=coerce_string(mapping.get("emitted_at_utc")),
        correlation_id=context.correlation_id,
        causation_id=context.causation_id,
        run_id=context.run_id,
    )


__all__ = [
    "DEFAULT_VALIDATION_INVALIDATION_RULES",
    "VALIDATION_PLAN_CONTRACT_ID",
    "VALIDATION_PLAN_SCHEMA_VERSION",
    "VALIDATION_RECEIPT_CONTRACT_ID",
    "VALIDATION_RECEIPT_SCHEMA_VERSION",
    "ValidationPlan",
    "ValidationReceipt",
    "validation_plan_from_mapping",
    "validation_receipt_from_mapping",
]
