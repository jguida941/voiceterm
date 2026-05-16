"""Typed commit receipt evidence for governed commit boundaries."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

UTC = timezone.utc

from .feature_proof_receipt import (
    FEATURE_PROOF_RECEIPT_ARTIFACT_ROOT,
    FeatureProofReceipt,
    feature_proof_receipt_artifact_relpath,
    require_non_circular_resolved_output_refs,
    write_feature_proof_receipt_artifact,
)
from .governance_proposed_contracts import FeatureLifecycleProof, LifecycleReceipt
from .remote_commit_pipeline_models import RemoteCommitPipelineContract
from .receipt_state_gate import require_receipt_state
from .typed_ids import ReceiptId, as_receipt_id, id_text
from .value_coercion import coerce_int, coerce_mapping, coerce_string, coerce_string_items


COMMIT_RECEIPT_CONTRACT_ID = "CommitReceipt"
COMMIT_RECEIPT_SCHEMA_VERSION = 1
COMMIT_RECEIPT_ARTIFACT_ROOT = "dev/reports/commit_receipts"
FEATURE_LIFECYCLE_PROOF_ARTIFACT_ROOT = "dev/reports/feature_lifecycle_proofs"
FEATURE_LIFECYCLE_REQUIRED_RECEIPT_KINDS = (
    "validation",
    "commit",
    "review",
    "audit",
    "tree",
)
VALIDATION_PASSED_STATE = "validation_passed"
VALIDATION_FAILED_STATE = "validation_failed"
VALIDATION_UNKNOWN_STATE = "validation_unknown"
COMMIT_RECORDED_STATE = "commit_recorded"
COMMIT_MISSING_SHA_STATE = "missing_commit_sha"


class CommitReceiptStateRequired(ValueError):
    """Raised when commit receipt evidence violates expected state ordering."""


@dataclass(frozen=True, slots=True)
class CommitReceipt:
    """Evidence chain for one governed commit."""

    schema_version: int = COMMIT_RECEIPT_SCHEMA_VERSION
    contract_id: str = COMMIT_RECEIPT_CONTRACT_ID
    receipt_id: str = ""
    commit_sha: str = ""
    tree_content_hash: str = ""
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
    pre_state: str = ""
    post_state: str = ""
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
    tree_content_hash = _tree_content_hash(pipeline)
    pre_state = _validation_receipt_state(validation)
    if validation is not None and commit_sha:
        require_receipt_state(
            validation,
            state_getter=_validation_receipt_state,
            required_state=VALIDATION_PASSED_STATE,
            error_factory=lambda: CommitReceiptStateRequired(
                "commit receipt requires a validation_passed receipt"
            ),
        )
    resolved_audit_ref = (
        coerce_string(audit_synthesis_ref)
        or _validation_receipt_ref(validation_receipt_id)
        or _guard_action_ref(pipeline.guard_action_id)
    )
    plan_row_id = _plan_row_id(pipeline)
    post_state = COMMIT_RECORDED_STATE if commit_sha else COMMIT_MISSING_SHA_STATE
    evidence_refs = _unique_refs(
        (
            _ref("commit", commit_sha),
            _ref("remote_commit_pipeline", pipeline.pipeline_id),
            _ref("packet", reviewer_ack_packet_id),
            _ref("packet", approval_packet_id),
            resolved_audit_ref,
            _ref("tree_content_hash", tree_content_hash),
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
        tree_content_hash=tree_content_hash,
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
        status=post_state,
        pre_state=pre_state,
        post_state=post_state,
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
        tree_content_hash=coerce_string(mapping.get("tree_content_hash")),
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
        pre_state=coerce_string(mapping.get("pre_state")),
        post_state=coerce_string(mapping.get("post_state")),
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


def build_feature_lifecycle_proof(
    pipeline: RemoteCommitPipelineContract,
    commit_receipt: CommitReceipt,
) -> FeatureLifecycleProof:
    """Build per-commit proof coverage from the governed commit evidence chain."""
    receipts = _feature_lifecycle_receipts(pipeline, commit_receipt)
    observed_kinds = {receipt.receipt_kind for receipt in receipts}
    missing = tuple(
        kind
        for kind in FEATURE_LIFECYCLE_REQUIRED_RECEIPT_KINDS
        if kind not in observed_kinds
    )
    total = len(FEATURE_LIFECYCLE_REQUIRED_RECEIPT_KINDS)
    completeness = (total - len(missing)) / total if total else 1.0
    return FeatureLifecycleProof(
        feature_id=(
            commit_receipt.plan_row_id
            or commit_receipt.pipeline_id
            or commit_receipt.commit_sha
        ),
        commit_sha=commit_receipt.commit_sha,
        receipts=receipts,
        completeness_score=round(completeness, 3),
        missing_receipt_kinds=missing,
    )


def feature_lifecycle_proof_artifact_relpath(commit_sha: str) -> str:
    """Return the repo-relative artifact path for one feature proof."""
    token = _path_token(commit_sha) or "unknown"
    return f"{FEATURE_LIFECYCLE_PROOF_ARTIFACT_ROOT}/{token}.json"


def write_feature_lifecycle_proof_artifact(
    repo_root: Path,
    proof: FeatureLifecycleProof,
) -> str:
    """Materialize a FeatureLifecycleProof artifact and return its relpath."""
    relpath = feature_lifecycle_proof_artifact_relpath(proof.commit_sha)
    path = repo_root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(proof.to_dict(), indent=2, sort_keys=True) + "\n")
    return relpath


def build_feature_proof_receipt(
    pipeline: RemoteCommitPipelineContract,
    commit_receipt: CommitReceipt,
    *,
    lifecycle_proof: FeatureLifecycleProof | None = None,
    evidence_artifacts: Iterable[str] = (),
    repo_root: Path | None = None,
) -> FeatureProofReceipt:
    """Build the operator-facing proof receipt for a shipped commit."""
    validation = pipeline.validation_receipt
    validation_passed = (
        commit_receipt.pre_state == VALIDATION_PASSED_STATE
        and commit_receipt.post_state == COMMIT_RECORDED_STATE
    )
    validation_plan_id = (
        coerce_string(validation.plan_id) if validation is not None else ""
    )
    validation_bundle_id = (
        coerce_string(validation.bundle_id) if validation is not None else ""
    )
    guard_ref = _guard_action_ref(pipeline.guard_action_id)
    tests_run = _unique_refs(
        (
            _ref("validation_plan", validation_plan_id),
            _ref("validation_bundle", validation_bundle_id),
            guard_ref,
        )
    )
    connectivity_guards = _unique_refs(
        (
            guard_ref,
            _validation_receipt_ref(
                as_receipt_id(
                    coerce_string(validation.receipt_id)
                    if validation is not None
                    else ""
                )
            ),
            commit_receipt.audit_synthesis_ref,
        )
    )
    artifacts = _unique_refs(
        (
            *tuple(coerce_string(path) for path in evidence_artifacts),
            commit_receipt_artifact_relpath(commit_receipt.commit_sha),
            (
                feature_lifecycle_proof_artifact_relpath(commit_receipt.commit_sha)
                if lifecycle_proof is not None
                else ""
            ),
        )
    )
    dogfood_ref = (
        artifacts[-1]
        if artifacts
        else commit_receipt.audit_synthesis_ref
        or _validation_receipt_ref(as_receipt_id(commit_receipt.validation_receipt_id))
        or commit_receipt.receipt_id
    )
    receipt = FeatureProofReceipt(
        feature_id=(
            commit_receipt.plan_row_id
            or commit_receipt.pipeline_id
            or commit_receipt.commit_sha
        ),
        commit_sha=commit_receipt.commit_sha,
        implementer_actor=commit_receipt.produced_by,
        review_fleet_roles_ran=_feature_proof_review_roles(commit_receipt),
        review_fleet_actor=(
            "review-channel" if commit_receipt.reviewer_ack_packet_id else "devctl"
        ),
        tests_run=tests_run or ("governed_commit_validation",),
        tests_passed_count=1 if validation_passed else 0,
        tests_failed_count=0 if validation_passed else 1,
        connectivity_guards_ran=connectivity_guards or tests_run,
        connectivity_guards_passed=validation_passed,
        dogfood_invocation_evidence_ref=dogfood_ref,
        real_life_test_status="proven_passed" if validation_passed else "proven_failed",
        not_tested_rationale=None,
        bypass_audit_trail_refs=_bypass_audit_trail_refs(commit_receipt),
        proven_at_utc=commit_receipt.recorded_at_utc,
        evidence_artifacts=artifacts,
    )
    if repo_root is not None:
        require_non_circular_resolved_output_refs(receipt, repo_root=repo_root)
    return receipt


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


def _tree_content_hash(pipeline: RemoteCommitPipelineContract) -> str:
    validation = pipeline.validation_receipt
    if validation is not None:
        value = coerce_string(getattr(validation, "staged_tree_hash", ""))
        if value:
            return value
    intent_value = coerce_string(getattr(pipeline.intent, "staged_tree_hash", ""))
    if intent_value:
        return intent_value
    plan = getattr(pipeline.intent, "validation_plan", None)
    return coerce_string(getattr(plan, "staged_tree_hash", ""))


def _feature_lifecycle_receipts(
    pipeline: RemoteCommitPipelineContract,
    commit_receipt: CommitReceipt,
) -> tuple[LifecycleReceipt, ...]:
    receipts: list[LifecycleReceipt] = []
    validation = pipeline.validation_receipt
    if validation is not None and coerce_string(validation.receipt_id):
        receipts.append(
            _lifecycle_receipt(
                "validation",
                commit_receipt,
                _validation_receipt_ref(as_receipt_id(validation.receipt_id)),
                (
                    f"validation {validation.post_state or validation.status} "
                    f"for bundle {validation.bundle_id}"
                ),
                executed_at_utc=coerce_string(validation.emitted_at_utc),
            )
        )
    if commit_receipt.receipt_id:
        receipts.append(
            _lifecycle_receipt(
                "commit",
                commit_receipt,
                commit_receipt.receipt_id,
                f"commit {commit_receipt.commit_sha} recorded",
            )
        )
    if commit_receipt.reviewer_ack_packet_id:
        receipts.append(
            _lifecycle_receipt(
                "review",
                commit_receipt,
                _ref("packet", commit_receipt.reviewer_ack_packet_id),
                "review or approval packet bound to commit receipt",
            )
        )
    if commit_receipt.audit_synthesis_ref:
        receipts.append(
            _lifecycle_receipt(
                "audit",
                commit_receipt,
                commit_receipt.audit_synthesis_ref,
                "audit or validation synthesis bound to commit receipt",
            )
        )
    if commit_receipt.tree_content_hash:
        receipts.append(
            _lifecycle_receipt(
                "tree",
                commit_receipt,
                _ref("tree_content_hash", commit_receipt.tree_content_hash),
                "tree content hash bound to validation and commit evidence",
            )
        )
    return tuple(receipts)


def _lifecycle_receipt(
    receipt_kind: str,
    commit_receipt: CommitReceipt,
    evidence_ref: str,
    proof_summary: str,
    *,
    executed_at_utc: str = "",
) -> LifecycleReceipt:
    return LifecycleReceipt(
        receipt_kind=receipt_kind,
        actor=commit_receipt.produced_by,
        executed_at_utc=executed_at_utc or commit_receipt.recorded_at_utc,
        evidence_ref=evidence_ref,
        proof_summary=proof_summary,
    )


def _feature_proof_review_roles(
    commit_receipt: CommitReceipt,
) -> tuple[str, ...]:
    roles: list[str] = []
    if commit_receipt.reviewer_ack_packet_id:
        roles.append("GovernanceReceipt")
    if commit_receipt.audit_synthesis_ref or commit_receipt.validation_receipt_id:
        roles.append("GuardsPerRound")
    if commit_receipt.evidence_refs:
        roles.append("ArchitectureReview")
    return tuple(roles or ("review_channel_not_recorded",))


def _bypass_audit_trail_refs(commit_receipt: CommitReceipt) -> tuple[str, ...]:
    return _unique_refs(
        ref
        for ref in commit_receipt.evidence_refs
        if ref.startswith(("raw_git", "bypass", "governed_exception"))
    )


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


def _validation_receipt_state(validation: object | None) -> str:
    if validation is None:
        return VALIDATION_UNKNOWN_STATE
    raw_post_state: object = getattr(validation, "post_state", "")
    post_state = str(raw_post_state).strip() if raw_post_state is not None else ""
    if post_state:
        return post_state
    raw_status: object = getattr(validation, "status", "")
    status = str(raw_status).strip() if raw_status is not None else ""
    if status == "pass":
        return VALIDATION_PASSED_STATE
    if status == "fail":
        return VALIDATION_FAILED_STATE
    return VALIDATION_UNKNOWN_STATE


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
    "COMMIT_RECORDED_STATE",
    "FEATURE_PROOF_RECEIPT_ARTIFACT_ROOT",
    "FEATURE_LIFECYCLE_PROOF_ARTIFACT_ROOT",
    "CommitReceipt",
    "CommitReceiptStateRequired",
    "FeatureProofReceipt",
    "VALIDATION_PASSED_STATE",
    "build_commit_receipt",
    "build_feature_lifecycle_proof",
    "build_feature_proof_receipt",
    "commit_receipt_artifact_relpath",
    "commit_receipt_from_mapping",
    "feature_lifecycle_proof_artifact_relpath",
    "feature_proof_receipt_artifact_relpath",
    "write_commit_receipt_artifact",
    "write_feature_lifecycle_proof_artifact",
    "write_feature_proof_receipt_artifact",
]
