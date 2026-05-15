"""Coercion helpers for typed master-plan contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .master_plan_contract import (
    EXPLAIN_BACK_RECEIPT_CONTRACT_ID,
    INGESTED_DOC_CONTRACT_ID,
    INGESTION_DRIFT_CONTRACT_ID,
    INGESTION_PROVENANCE_CONTRACT_ID,
    INGESTION_POLICY_CONTRACT_ID,
    LINKED_DOC_CONTRACT_ID,
    MASTER_PLAN_CONTRACT_ID,
    MASTER_PLAN_SCHEMA_VERSION,
    PLAN_PROPOSAL_CONTRACT_ID,
    PLAN_ROW_CONTRACT_ID,
    ExplainBackReceipt,
    commit_anchor_ref_from_anchor_refs,
    IngestedDoc,
    IngestionDrift,
    IngestionPolicy,
    IngestionProvenance,
    LinkedDoc,
    MasterPlan,
    PlanProposal,
    PlanRow,
    SDLCStage,
)
from .value_coercion import (
    coerce_int,
    coerce_mapping,
    coerce_mapping_items,
    coerce_string,
    coerce_string_items,
)


def linked_doc_from_mapping(payload: Mapping[str, object]) -> LinkedDoc:
    schema_version = coerce_int(payload.get("schema_version"))
    contract_id = coerce_string(payload.get("contract_id"))
    return LinkedDoc(
        schema_version=schema_version or MASTER_PLAN_SCHEMA_VERSION,
        contract_id=contract_id or LINKED_DOC_CONTRACT_ID,
        path=coerce_string(payload.get("path")),
        role=coerce_string(payload.get("role")),
        sdlc_stage=SDLCStage.normalize(payload.get("sdlc_stage")),
        links_to_plan_row=coerce_string(payload.get("links_to_plan_row")),
    )


def ingestion_provenance_from_mapping(
    payload: Mapping[str, object],
) -> IngestionProvenance:
    """Parse provenance, accepting legacy PlanRow source fields as fallback."""
    provenance_payload = coerce_mapping(payload.get("provenance"))
    source = provenance_payload or payload
    schema_version = coerce_int(source.get("schema_version"))
    contract_id = coerce_string(source.get("contract_id"))
    source_file = coerce_string(source.get("source_file")) or coerce_string(
        source.get("source_doc_path")
    )
    source_line = coerce_int(source.get("source_line"))
    source_hash = coerce_string(source.get("source_hash")) or coerce_string(
        source.get("content_hash")
    )
    return IngestionProvenance(
        schema_version=schema_version or MASTER_PLAN_SCHEMA_VERSION,
        contract_id=contract_id or INGESTION_PROVENANCE_CONTRACT_ID,
        source_file=source_file,
        source_line=source_line,
        source_kind=coerce_string(source.get("source_kind")),
        source_hash=source_hash,
        observed_at_utc=coerce_string(source.get("observed_at_utc")),
        section_authority=coerce_string(source.get("section_authority")),
    )


def plan_row_from_mapping(payload: Mapping[str, object]) -> PlanRow:
    schema_version = coerce_int(payload.get("schema_version"))
    contract_id = coerce_string(payload.get("contract_id"))
    anchor_refs = coerce_string_items(payload.get("anchor_refs"))
    status = coerce_string(payload.get("status")) or "open"
    commit_anchor_ref = coerce_string(payload.get("commit_anchor_ref"))
    if status in {"applied", "completed"} and not commit_anchor_ref:
        commit_anchor_ref = commit_anchor_ref_from_anchor_refs(anchor_refs)
    return PlanRow(
        schema_version=schema_version or MASTER_PLAN_SCHEMA_VERSION,
        contract_id=contract_id or PLAN_ROW_CONTRACT_ID,
        row_id=coerce_string(payload.get("row_id")),
        title=coerce_string(payload.get("title")),
        status=status,
        sdlc_stage=SDLCStage.normalize(payload.get("sdlc_stage")),
        row_kind=coerce_string(payload.get("row_kind")) or "task",
        sourced_from_packets=coerce_string_items(payload.get("sourced_from_packets")),
        contradicts_packets=coerce_string_items(payload.get("contradicts_packets")),
        work_evidence_ids=coerce_string_items(payload.get("work_evidence_ids")),
        superseded_by_row=coerce_string(payload.get("superseded_by_row")),
        plan_revision_at_write=coerce_string(payload.get("plan_revision_at_write")),
        source_doc_path=coerce_string(payload.get("source_doc_path")),
        source_line=coerce_int(payload.get("source_line")),
        content_hash=coerce_string(payload.get("content_hash")),
        provenance=ingestion_provenance_from_mapping(payload),
        anchor_refs=anchor_refs,
        target_ref=coerce_string(payload.get("target_ref")),
        mutation_op=coerce_string(payload.get("mutation_op")),
        commit_anchor_ref=commit_anchor_ref,
        applied_at_utc=coerce_string(payload.get("applied_at_utc")),
    )


def master_plan_from_mapping(payload: Mapping[str, object]) -> MasterPlan:
    schema_version = coerce_int(payload.get("schema_version"))
    contract_id = coerce_string(payload.get("contract_id"))
    source_path = coerce_string(payload.get("source_path"))
    typed_store_path = coerce_string(payload.get("typed_store_path"))
    projection_path = coerce_string(payload.get("projection_path"))
    return MasterPlan(
        schema_version=schema_version or MASTER_PLAN_SCHEMA_VERSION,
        contract_id=contract_id or MASTER_PLAN_CONTRACT_ID,
        repo_id=coerce_string(payload.get("repo_id")),
        rows=tuple(
            plan_row_from_mapping(row)
            for row in coerce_mapping_items(payload.get("rows"))
        ),
        linked_docs=tuple(
            linked_doc_from_mapping(row)
            for row in coerce_mapping_items(payload.get("linked_docs"))
        ),
        status=coerce_string(payload.get("status")) or "pending_explainback",
        last_ingested_at_utc=coerce_string(payload.get("last_ingested_at_utc")),
        plan_revision=coerce_string(payload.get("plan_revision")),
        source_path=source_path,
        typed_store_path=typed_store_path,
        projection_path=projection_path or source_path,
    )


def plan_proposal_from_mapping(payload: Mapping[str, object]) -> PlanProposal:
    proposed_row_payload = coerce_mapping(payload.get("proposed_row"))
    proposed_row = (
        plan_row_from_mapping(proposed_row_payload)
        if proposed_row_payload
        else None
    )
    proposed_links = tuple(
        linked_doc_from_mapping(row)
        for row in coerce_mapping_items(payload.get("proposed_links"))
    )
    return PlanProposal(
        schema_version=(
            coerce_int(payload.get("schema_version")) or MASTER_PLAN_SCHEMA_VERSION
        ),
        contract_id=(
            coerce_string(payload.get("contract_id")) or PLAN_PROPOSAL_CONTRACT_ID
        ),
        target_ref=coerce_string(payload.get("target_ref")),
        anchor_refs=coerce_string_items(payload.get("anchor_refs")),
        mutation_op=coerce_string(payload.get("mutation_op")),
        proposed_row=proposed_row,
        proposed_links=proposed_links,
        plan_revision_at_propose=coerce_string(
            payload.get("plan_revision_at_propose")
        ),
    )


def ingestion_policy_from_mapping(payload: Mapping[str, object]) -> IngestionPolicy:
    scan_roots = coerce_string_items(payload.get("scan_roots"))
    adapters = coerce_string_items(payload.get("adapters"))
    return IngestionPolicy(
        schema_version=(
            coerce_int(payload.get("schema_version")) or MASTER_PLAN_SCHEMA_VERSION
        ),
        contract_id=(
            coerce_string(payload.get("contract_id")) or INGESTION_POLICY_CONTRACT_ID
        ),
        scan_roots=scan_roots,
        exclude_globs=coerce_string_items(payload.get("exclude_globs")),
        adapters=adapters,
        max_file_bytes=coerce_int(payload.get("max_file_bytes")) or 1_000_000,
        drift_mode=coerce_string(payload.get("drift_mode")) or "surface_finding",
    )


def ingestion_drift_from_mapping(payload: Mapping[str, object]) -> IngestionDrift:
    schema_version = coerce_int(payload.get("schema_version"))
    contract_id = coerce_string(payload.get("contract_id"))
    return IngestionDrift(
        schema_version=schema_version or MASTER_PLAN_SCHEMA_VERSION,
        contract_id=contract_id or INGESTION_DRIFT_CONTRACT_ID,
        row_id=coerce_string(payload.get("row_id")),
        source_doc_path=coerce_string(payload.get("source_doc_path")),
        expected_hash=coerce_string(payload.get("expected_hash")),
        observed_hash=coerce_string(payload.get("observed_hash")),
        reason=coerce_string(payload.get("reason")),
    )


def ingested_doc_from_mapping(payload: Mapping[str, object]) -> IngestedDoc:
    schema_version = coerce_int(payload.get("schema_version"))
    contract_id = coerce_string(payload.get("contract_id"))
    return IngestedDoc(
        schema_version=schema_version or MASTER_PLAN_SCHEMA_VERSION,
        contract_id=contract_id or INGESTED_DOC_CONTRACT_ID,
        source_file=coerce_string(payload.get("source_file")),
        source_kind=coerce_string(payload.get("source_kind")),
        status=coerce_string(payload.get("status")) or "unknown",
        reason=coerce_string(payload.get("reason")),
        rows=tuple(
            plan_row_from_mapping(row)
            for row in coerce_mapping_items(payload.get("rows"))
        ),
        observed_at_utc=coerce_string(payload.get("observed_at_utc")),
    )


def explain_back_receipt_from_mapping(
    payload: Mapping[str, object],
) -> ExplainBackReceipt:
    schema_version = coerce_int(payload.get("schema_version"))
    contract_id = coerce_string(payload.get("contract_id"))
    return ExplainBackReceipt(
        schema_version=schema_version or MASTER_PLAN_SCHEMA_VERSION,
        contract_id=contract_id or EXPLAIN_BACK_RECEIPT_CONTRACT_ID,
        receipt_id=coerce_string(payload.get("receipt_id")),
        repo_pack_id=coerce_string(payload.get("repo_pack_id")),
        ingested_files=coerce_string_items(payload.get("ingested_files")),
        derived_plan_rows=coerce_string_items(payload.get("derived_plan_rows")),
        nl_summary=coerce_string(payload.get("nl_summary")),
        confidence=_coerce_float(payload.get("confidence")),
        pending_questions=coerce_string_items(payload.get("pending_questions")),
        status=coerce_string(payload.get("status")) or "pending",
        operator_signature=coerce_string(payload.get("operator_signature")),
    )


def normalize_plan_proposal(value: object) -> PlanProposal:
    if isinstance(value, PlanProposal):
        return value
    if isinstance(value, Mapping):
        return plan_proposal_from_mapping(value)
    return PlanProposal()


def plan_proposal_from_packet_fields(
    *,
    target_ref: str,
    anchor_refs: Sequence[str] = (),
    mutation_op: str = "",
    plan_revision_at_propose: str = "",
) -> PlanProposal:
    normalized_anchor_refs = tuple(
        anchor_ref for anchor_ref in anchor_refs if anchor_ref
    )
    return PlanProposal(
        target_ref=target_ref,
        anchor_refs=normalized_anchor_refs,
        mutation_op=mutation_op,
        plan_revision_at_propose=plan_revision_at_propose,
    )


def _coerce_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


__all__ = [
    "explain_back_receipt_from_mapping",
    "ingested_doc_from_mapping",
    "ingestion_drift_from_mapping",
    "ingestion_policy_from_mapping",
    "ingestion_provenance_from_mapping",
    "linked_doc_from_mapping",
    "master_plan_from_mapping",
    "normalize_plan_proposal",
    "plan_proposal_from_mapping",
    "plan_proposal_from_packet_fields",
    "plan_row_from_mapping",
]
