"""Typed commit receipt evidence for governed commit boundaries."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from .remote_commit_pipeline_models import RemoteCommitPipelineContract
from .typed_ids import ReceiptId, as_receipt_id, id_text
from .value_coercion import (
    coerce_bool,
    coerce_int,
    coerce_mapping,
    coerce_string,
    coerce_string_items,
)


COMMIT_RECEIPT_CONTRACT_ID = "CommitReceipt"
COMMIT_RECEIPT_SCHEMA_VERSION = 1
COMMIT_RECEIPT_ARTIFACT_ROOT = "dev/reports/commit_receipts"


@dataclass(frozen=True, slots=True)
class CommitReceipt:
    """Evidence chain for one governed commit."""

    schema_version: int = COMMIT_RECEIPT_SCHEMA_VERSION
    contract_id: str = COMMIT_RECEIPT_CONTRACT_ID
    receipt_id: str = ""
    commit_sha: str = ""
    pipeline_id: str = ""
    pipeline_generation_id: str = ""
    plan_row_id: str = ""
    reviewer_ack_packet_id: str = ""
    approval_packet_id: str = ""
    decision_packet_id: str = ""
    audit_synthesis_ref: str = ""
    validation_receipt_id: str = ""
    guard_action_id: str = ""
    commit_action_id: str = ""
    status: str = "unknown"
    recorded_at_utc: str = ""
    produced_by: str = "devctl"
    artifact_paths: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    correlation_id: str = ""
    causation_id: str = ""
    run_id: str = ""

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["artifact_paths"] = list(self.artifact_paths)
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload


def build_commit_receipt(
    pipeline: RemoteCommitPipelineContract,
    *,
    audit_synthesis_ref: str = "",
    recorded_at_utc: str = "",
    produced_by: str = "devctl",
    artifact_paths: Iterable[str] = (),
) -> CommitReceipt:
    """Build the commit receipt evidence chain for a recorded pipeline."""
    commit_sha = coerce_string(pipeline.commit_sha)
    push_auth = pipeline.push_authorization
    validation = pipeline.validation_receipt
    commit_result = pipeline.commit_result
    approval_packet_id = (
        coerce_string(push_auth.request_packet_id) if push_auth is not None else ""
    ) or coerce_string(pipeline.approval_packet_id)
    decision_packet_id = (
        coerce_string(push_auth.decision_packet_id) if push_auth is not None else ""
    ) or coerce_string(pipeline.decision_packet_id)
    reviewer_ack_packet_id = decision_packet_id or approval_packet_id
    validation_receipt_id = as_receipt_id(
        coerce_string(validation.receipt_id) if validation is not None else ""
    )
    resolved_audit_ref = (
        coerce_string(audit_synthesis_ref)
        or _validation_receipt_ref(validation_receipt_id)
        or _guard_action_ref(pipeline.guard_action_id)
    )
    plan_row_id = _plan_row_id(pipeline)
    evidence_refs = _unique_refs(
        (
            _ref("commit", commit_sha),
            _ref("remote_commit_pipeline", pipeline.pipeline_id),
            _ref("packet", reviewer_ack_packet_id),
            _ref("packet", approval_packet_id),
            resolved_audit_ref,
            _validation_receipt_ref(validation_receipt_id),
            _guard_action_ref(pipeline.guard_action_id),
            _ref(
                "action_result",
                coerce_string(getattr(commit_result, "action_id", "")),
            ),
        )
    )
    return CommitReceipt(
        receipt_id=_ref("commit_receipt", commit_sha),
        commit_sha=commit_sha,
        pipeline_id=coerce_string(pipeline.pipeline_id),
        pipeline_generation_id=coerce_string(pipeline.generation_id),
        plan_row_id=plan_row_id,
        reviewer_ack_packet_id=reviewer_ack_packet_id,
        approval_packet_id=approval_packet_id,
        decision_packet_id=decision_packet_id,
        audit_synthesis_ref=resolved_audit_ref,
        validation_receipt_id=id_text(validation_receipt_id),
        guard_action_id=coerce_string(pipeline.guard_action_id),
        commit_action_id=coerce_string(pipeline.commit_action_id),
        status="commit_recorded" if commit_sha else "missing_commit_sha",
        recorded_at_utc=coerce_string(recorded_at_utc) or _utc_now(),
        produced_by=coerce_string(produced_by) or "devctl",
        artifact_paths=tuple(coerce_string(path) for path in artifact_paths if coerce_string(path)),
        evidence_refs=evidence_refs,
        correlation_id=coerce_string(getattr(commit_result, "correlation_id", "")),
        causation_id=coerce_string(getattr(commit_result, "causation_id", "")),
        run_id=coerce_string(getattr(commit_result, "run_id", "")),
    )


def commit_receipt_from_mapping(payload: Mapping[str, object]) -> CommitReceipt:
    """Normalize a mapping into a CommitReceipt."""
    mapping = coerce_mapping(payload)
    return CommitReceipt(
        schema_version=coerce_int(mapping.get("schema_version"))
        or COMMIT_RECEIPT_SCHEMA_VERSION,
        contract_id=coerce_string(mapping.get("contract_id"))
        or COMMIT_RECEIPT_CONTRACT_ID,
        receipt_id=coerce_string(mapping.get("receipt_id")),
        commit_sha=coerce_string(mapping.get("commit_sha")),
        pipeline_id=coerce_string(mapping.get("pipeline_id")),
        pipeline_generation_id=coerce_string(mapping.get("pipeline_generation_id")),
        plan_row_id=coerce_string(mapping.get("plan_row_id")),
        reviewer_ack_packet_id=coerce_string(mapping.get("reviewer_ack_packet_id")),
        approval_packet_id=coerce_string(mapping.get("approval_packet_id")),
        decision_packet_id=coerce_string(mapping.get("decision_packet_id")),
        audit_synthesis_ref=coerce_string(mapping.get("audit_synthesis_ref")),
        validation_receipt_id=coerce_string(mapping.get("validation_receipt_id")),
        guard_action_id=coerce_string(mapping.get("guard_action_id")),
        commit_action_id=coerce_string(mapping.get("commit_action_id")),
        status=coerce_string(mapping.get("status")) or "unknown",
        recorded_at_utc=coerce_string(mapping.get("recorded_at_utc")),
        produced_by=coerce_string(mapping.get("produced_by")) or "devctl",
        artifact_paths=coerce_string_items(mapping.get("artifact_paths")),
        evidence_refs=coerce_string_items(mapping.get("evidence_refs")),
        correlation_id=coerce_string(mapping.get("correlation_id")),
        causation_id=coerce_string(mapping.get("causation_id")),
        run_id=coerce_string(mapping.get("run_id")),
    )


def commit_receipt_artifact_relpath(commit_sha: str) -> str:
    """Return the repo-relative artifact path for one commit receipt."""
    token = _path_token(commit_sha) or "unknown"
    return f"{COMMIT_RECEIPT_ARTIFACT_ROOT}/{token}.json"


def write_commit_receipt_artifact(
    repo_root: Path,
    receipt: CommitReceipt,
) -> str:
    """Materialize a commit receipt artifact and return its repo-relative path."""
    relpath = commit_receipt_artifact_relpath(receipt.commit_sha)
    path = repo_root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt.to_dict(), indent=2, sort_keys=True) + "\n")
    return relpath


def _plan_row_id(pipeline: RemoteCommitPipelineContract) -> str:
    validation = pipeline.validation_receipt
    plan = pipeline.intent.validation_plan
    for value in (
        coerce_string(validation.plan_id) if validation is not None else "",
        coerce_string(plan.plan_id) if plan is not None else "",
        coerce_string(pipeline.intent.work_intake_ref),
    ):
        if value:
            return value
    return ""


def _unique_refs(values: Iterable[str]) -> tuple[str, ...]:
    refs: list[str] = []
    seen: set[str] = set()
    for value in values:
        ref = coerce_string(value)
        if not ref or ref in seen:
            continue
        seen.add(ref)
        refs.append(ref)
    return tuple(refs)


def _ref(prefix: str, value: str) -> str:
    token = coerce_string(value)
    if not token:
        return ""
    return f"{prefix}:{token}"


def _validation_receipt_ref(receipt_id: ReceiptId) -> str:
    return _ref("validation_receipt", id_text(receipt_id))


def _guard_action_ref(action_id: str) -> str:
    return _ref("guard_action", action_id)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _path_token(value: str) -> str:
    text = coerce_string(value)
    return "".join(char for char in text if char.isalnum() or char in "._-")[:80]


__all__ = [
    "COMMIT_RECEIPT_ARTIFACT_ROOT",
    "COMMIT_RECEIPT_CONTRACT_ID",
    "COMMIT_RECEIPT_SCHEMA_VERSION",
    "CommitReceipt",
    "build_commit_receipt",
    "commit_receipt_artifact_relpath",
    "commit_receipt_from_mapping",
    "write_commit_receipt_artifact",
]
