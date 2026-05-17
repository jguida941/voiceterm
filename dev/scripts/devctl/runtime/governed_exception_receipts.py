"""Receipt and proof contracts for governed exceptions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass

from .correlation_spine import correlation_context_for_ref, merge_correlation_context
from .governed_exception_base import (
    AUTO_REPAIR_RECEIPT_CONTRACT_ID,
    CLOSURE_PROOF_CONTRACT_ID,
    EXCEPTION_RECEIPT_CONTRACT_ID,
    GOVERNED_EXCEPTION_SCHEMA_VERSION,
    MANUAL_BYPASS_IMPORT_RECEIPT_CONTRACT_ID,
    RESOLUTION_RECEIPT_CONTRACT_ID,
    json_ready_dict,
)
from .value_coercion import (
    coerce_bool,
    coerce_int,
    coerce_mapping,
    coerce_string,
    coerce_string_items,
)


class GovernedExceptionReceiptMixin:
    """Shared JSON serialization for governed-exception receipt dataclasses."""

    def to_dict(self) -> dict[str, object]:
        return json_ready_dict(asdict(self))


@dataclass(frozen=True, slots=True)
class ExceptionReceipt(GovernedExceptionReceiptMixin):
    """Pending or historical exception evidence, not execution authority."""

    receipt_id: str
    action_kind: str
    phase: str
    guard_id: str
    exception_class: str
    operator_reason: str
    head: str
    scope: str = ""
    finding_id: str = ""
    planned_finding_ingest_ref: str = ""
    worktree_fingerprint: str = ""
    remote: str = ""
    policy_result: str = ""
    authority_evidence_refs: tuple[str, ...] = ()
    worktree_safety_evidence_refs: tuple[str, ...] = ()
    validation_plan_id: str = ""
    execution_status: str = "not_executed"
    remote_ref_verified: bool = False
    post_push_proof_ref: str = ""
    expires_at_utc: str = ""
    created_at_utc: str = ""
    correlation_id: str = ""
    causation_id: str = ""
    run_id: str = ""
    schema_version: int = GOVERNED_EXCEPTION_SCHEMA_VERSION
    contract_id: str = EXCEPTION_RECEIPT_CONTRACT_ID

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "ExceptionReceipt":
        mapping = coerce_mapping(payload)
        receipt_id = coerce_string(mapping.get("receipt_id"))
        guard_id = coerce_string(mapping.get("guard_id"))
        validation_plan_id = coerce_string(mapping.get("validation_plan_id"))
        context = merge_correlation_context(
            mapping,
            correlation_context_for_ref(
                "exception_receipt",
                receipt_id,
                causation_kind="guard",
                causation_ref_value=guard_id,
                run_kind="validation_plan",
                run_ref_value=validation_plan_id
                or coerce_string(mapping.get("phase"))
                or receipt_id,
            ).to_dict(),
        )
        return cls(
            receipt_id=receipt_id,
            action_kind=coerce_string(mapping.get("action_kind")),
            phase=coerce_string(mapping.get("phase")),
            guard_id=guard_id,
            exception_class=coerce_string(mapping.get("exception_class")),
            operator_reason=coerce_string(mapping.get("operator_reason")),
            head=coerce_string(mapping.get("head")),
            scope=coerce_string(mapping.get("scope")),
            finding_id=coerce_string(mapping.get("finding_id")),
            planned_finding_ingest_ref=coerce_string(mapping.get("planned_finding_ingest_ref")),
            worktree_fingerprint=coerce_string(mapping.get("worktree_fingerprint")),
            remote=coerce_string(mapping.get("remote")),
            policy_result=coerce_string(mapping.get("policy_result")),
            authority_evidence_refs=coerce_string_items(mapping.get("authority_evidence_refs")),
            worktree_safety_evidence_refs=coerce_string_items(
                mapping.get("worktree_safety_evidence_refs")
            ),
            validation_plan_id=coerce_string(mapping.get("validation_plan_id")),
            execution_status=coerce_string(mapping.get("execution_status")) or "not_executed",
            remote_ref_verified=coerce_bool(mapping.get("remote_ref_verified")),
            post_push_proof_ref=coerce_string(mapping.get("post_push_proof_ref")),
            expires_at_utc=coerce_string(mapping.get("expires_at_utc")),
            created_at_utc=coerce_string(mapping.get("created_at_utc")),
            correlation_id=context.correlation_id,
            causation_id=context.causation_id,
            run_id=context.run_id,
            schema_version=coerce_int(mapping.get("schema_version"))
            or GOVERNED_EXCEPTION_SCHEMA_VERSION,
        )


@dataclass(frozen=True, slots=True)
class ClosureProof(GovernedExceptionReceiptMixin):
    """Proof that the original guarded path passed without exception."""

    closure_proof_id: str
    exception_lifecycle_id: str
    normal_command: str
    validation_receipt_id: str
    action_result_id: str = ""
    run_record_id: str = ""
    exception_used: bool = False
    remote_ref_verified: bool = False
    post_push_green: bool = False
    proof_artifacts: tuple[str, ...] = ()
    schema_version: int = GOVERNED_EXCEPTION_SCHEMA_VERSION
    contract_id: str = CLOSURE_PROOF_CONTRACT_ID

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "ClosureProof":
        mapping = coerce_mapping(payload)
        return cls(
            closure_proof_id=coerce_string(mapping.get("closure_proof_id")),
            exception_lifecycle_id=coerce_string(mapping.get("exception_lifecycle_id")),
            normal_command=coerce_string(mapping.get("normal_command")),
            validation_receipt_id=coerce_string(mapping.get("validation_receipt_id")),
            action_result_id=coerce_string(mapping.get("action_result_id")),
            run_record_id=coerce_string(mapping.get("run_record_id")),
            exception_used=coerce_bool(mapping.get("exception_used")),
            remote_ref_verified=coerce_bool(mapping.get("remote_ref_verified")),
            post_push_green=coerce_bool(mapping.get("post_push_green")),
            proof_artifacts=coerce_string_items(mapping.get("proof_artifacts")),
            schema_version=coerce_int(mapping.get("schema_version"))
            or GOVERNED_EXCEPTION_SCHEMA_VERSION,
        )


@dataclass(frozen=True, slots=True)
class ResolutionReceipt(GovernedExceptionReceiptMixin):
    """Closure receipt for one governed exception lifecycle."""

    resolution_id: str
    exception_lifecycle_id: str
    finding_id: str
    status: str
    root_cause_class: str
    root_cause_summary: str
    fixed_by_commit: str = ""
    changed_files: tuple[str, ...] = ()
    validation_receipt_id: str = ""
    action_result_id: str = ""
    dogfood_evidence_id: str = ""
    closure_proof_id: str = ""
    exception_used: bool = False
    remote_ref_verified: bool = False
    post_push_green: bool = False
    closed_at_utc: str = ""
    closure_reason: str = ""
    schema_version: int = GOVERNED_EXCEPTION_SCHEMA_VERSION
    contract_id: str = RESOLUTION_RECEIPT_CONTRACT_ID

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "ResolutionReceipt":
        mapping = coerce_mapping(payload)
        return cls(
            resolution_id=coerce_string(mapping.get("resolution_id")),
            exception_lifecycle_id=coerce_string(mapping.get("exception_lifecycle_id")),
            finding_id=coerce_string(mapping.get("finding_id")),
            status=coerce_string(mapping.get("status")),
            root_cause_class=coerce_string(mapping.get("root_cause_class")),
            root_cause_summary=coerce_string(mapping.get("root_cause_summary")),
            fixed_by_commit=coerce_string(mapping.get("fixed_by_commit")),
            changed_files=coerce_string_items(mapping.get("changed_files")),
            validation_receipt_id=coerce_string(mapping.get("validation_receipt_id")),
            action_result_id=coerce_string(mapping.get("action_result_id")),
            dogfood_evidence_id=coerce_string(mapping.get("dogfood_evidence_id")),
            closure_proof_id=coerce_string(mapping.get("closure_proof_id")),
            exception_used=coerce_bool(mapping.get("exception_used")),
            remote_ref_verified=coerce_bool(mapping.get("remote_ref_verified")),
            post_push_green=coerce_bool(mapping.get("post_push_green")),
            closed_at_utc=coerce_string(mapping.get("closed_at_utc")),
            closure_reason=coerce_string(mapping.get("closure_reason")),
            schema_version=coerce_int(mapping.get("schema_version"))
            or GOVERNED_EXCEPTION_SCHEMA_VERSION,
        )


@dataclass(frozen=True, slots=True)
class AutoRepairReceipt(GovernedExceptionReceiptMixin):
    """Receipt for bounded auto-repair attempted before exception request."""

    receipt_id: str
    action_kind: str
    guard_id: str
    exception_class: str
    repair_command: str
    status: str
    rerun_guard_status: str = ""
    head: str = ""
    created_at_utc: str = ""
    evidence_refs: tuple[str, ...] = ()
    schema_version: int = GOVERNED_EXCEPTION_SCHEMA_VERSION
    contract_id: str = AUTO_REPAIR_RECEIPT_CONTRACT_ID

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "AutoRepairReceipt":
        mapping = coerce_mapping(payload)
        return cls(
            receipt_id=coerce_string(mapping.get("receipt_id")),
            action_kind=coerce_string(mapping.get("action_kind")),
            guard_id=coerce_string(mapping.get("guard_id")),
            exception_class=coerce_string(mapping.get("exception_class")),
            repair_command=coerce_string(mapping.get("repair_command")),
            status=coerce_string(mapping.get("status")),
            rerun_guard_status=coerce_string(mapping.get("rerun_guard_status")),
            head=coerce_string(mapping.get("head")),
            created_at_utc=coerce_string(mapping.get("created_at_utc")),
            evidence_refs=coerce_string_items(mapping.get("evidence_refs")),
            schema_version=coerce_int(mapping.get("schema_version"))
            or GOVERNED_EXCEPTION_SCHEMA_VERSION,
        )


@dataclass(frozen=True, slots=True)
class ManualBypassImportReceipt(GovernedExceptionReceiptMixin):
    """Historical import of a manual bypass as evidence, not permission."""

    receipt_id: str
    action_kind: str
    imported_command_summary: str
    operator_reason: str
    head: str
    finding_id: str = ""
    planned_finding_ingest_ref: str = ""
    remote_ref_verified: bool = False
    post_push_proof_ref: str = ""
    imported_at_utc: str = ""
    evidence_refs: tuple[str, ...] = ()
    schema_version: int = GOVERNED_EXCEPTION_SCHEMA_VERSION
    contract_id: str = MANUAL_BYPASS_IMPORT_RECEIPT_CONTRACT_ID

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "ManualBypassImportReceipt":
        mapping = coerce_mapping(payload)
        return cls(
            receipt_id=coerce_string(mapping.get("receipt_id")),
            action_kind=coerce_string(mapping.get("action_kind")),
            imported_command_summary=coerce_string(mapping.get("imported_command_summary")),
            operator_reason=coerce_string(mapping.get("operator_reason")),
            head=coerce_string(mapping.get("head")),
            finding_id=coerce_string(mapping.get("finding_id")),
            planned_finding_ingest_ref=coerce_string(mapping.get("planned_finding_ingest_ref")),
            remote_ref_verified=coerce_bool(mapping.get("remote_ref_verified")),
            post_push_proof_ref=coerce_string(mapping.get("post_push_proof_ref")),
            imported_at_utc=coerce_string(mapping.get("imported_at_utc")),
            evidence_refs=coerce_string_items(mapping.get("evidence_refs")),
            schema_version=coerce_int(mapping.get("schema_version"))
            or GOVERNED_EXCEPTION_SCHEMA_VERSION,
        )


__all__ = [
    "AutoRepairReceipt",
    "ClosureProof",
    "ExceptionReceipt",
    "ManualBypassImportReceipt",
    "ResolutionReceipt",
]
