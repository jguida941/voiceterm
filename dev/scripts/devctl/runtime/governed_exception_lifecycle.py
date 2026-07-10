"""Governed exception lifecycle envelope contract."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass

from .governed_exception_base import (
    GOVERNED_EXCEPTION_LIFECYCLE_CONTRACT_ID,
    GOVERNED_EXCEPTION_SCHEMA_VERSION,
    json_ready_dict,
)
from .governed_exception_receipts import ClosureProof, ExceptionReceipt, ResolutionReceipt
from .value_coercion import coerce_int, coerce_mapping, coerce_string, coerce_string_items


@dataclass(frozen=True, slots=True)
class GovernedExceptionLifecycle:
    """Lifecycle envelope linking exception debt to repair and proof."""

    lifecycle_id: str
    status: str
    exception: ExceptionReceipt | None = None
    resolution: ResolutionReceipt | None = None
    closure_proof: ClosureProof | None = None
    finding_id: str = ""
    planned_finding_ingest_ref: str = ""
    validation_plan_id: str = ""
    authority_evidence_refs: tuple[str, ...] = ()
    worktree_safety_evidence_refs: tuple[str, ...] = ()
    system_map_contract_ids: tuple[str, ...] = ()
    developer_loop_refs: tuple[str, ...] = ()
    learning_refs: tuple[str, ...] = ()
    projection_refs: tuple[str, ...] = ()
    resolution_receipt_id: str = ""
    created_at_utc: str = ""
    updated_at_utc: str = ""
    schema_version: int = GOVERNED_EXCEPTION_SCHEMA_VERSION
    contract_id: str = GOVERNED_EXCEPTION_LIFECYCLE_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return json_ready_dict(asdict(self))

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, object],
    ) -> "GovernedExceptionLifecycle":
        mapping = coerce_mapping(payload)
        exception = mapping.get("exception")
        resolution = mapping.get("resolution")
        closure_proof = mapping.get("closure_proof")
        return cls(
            lifecycle_id=coerce_string(mapping.get("lifecycle_id")),
            status=coerce_string(mapping.get("status")),
            exception=(
                ExceptionReceipt.from_mapping(exception)
                if isinstance(exception, Mapping)
                else None
            ),
            resolution=(
                ResolutionReceipt.from_mapping(resolution)
                if isinstance(resolution, Mapping)
                else None
            ),
            closure_proof=(
                ClosureProof.from_mapping(closure_proof)
                if isinstance(closure_proof, Mapping)
                else None
            ),
            finding_id=coerce_string(mapping.get("finding_id")),
            planned_finding_ingest_ref=coerce_string(mapping.get("planned_finding_ingest_ref")),
            validation_plan_id=coerce_string(mapping.get("validation_plan_id")),
            authority_evidence_refs=coerce_string_items(mapping.get("authority_evidence_refs")),
            worktree_safety_evidence_refs=coerce_string_items(
                mapping.get("worktree_safety_evidence_refs")
            ),
            system_map_contract_ids=coerce_string_items(mapping.get("system_map_contract_ids")),
            developer_loop_refs=coerce_string_items(mapping.get("developer_loop_refs")),
            learning_refs=coerce_string_items(mapping.get("learning_refs")),
            projection_refs=coerce_string_items(mapping.get("projection_refs")),
            resolution_receipt_id=coerce_string(mapping.get("resolution_receipt_id")),
            created_at_utc=coerce_string(mapping.get("created_at_utc")),
            updated_at_utc=coerce_string(mapping.get("updated_at_utc")),
            schema_version=coerce_int(mapping.get("schema_version"))
            or GOVERNED_EXCEPTION_SCHEMA_VERSION,
        )


__all__ = ["GovernedExceptionLifecycle"]
