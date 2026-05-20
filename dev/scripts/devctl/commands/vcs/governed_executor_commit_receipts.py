"""Receipt emission for governed commit execution."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path

from ...runtime import ActionResult
from ...runtime.commit_receipt import (
    build_commit_receipt,
    build_feature_lifecycle_proof,
    build_feature_proof_receipt,
    write_commit_receipt_artifact,
    write_feature_lifecycle_proof_artifact,
    write_feature_proof_receipt_artifact,
)
from ...runtime.remote_commit_pipeline_models import RemoteCommitPipelineContract
from ...runtime.review_snapshot_refresh import receipt_commit_parent_sha
from .governed_executor_commit_proof import (
    CommitMutationProofRequest,
    record_commit_mutation_proof,
)

ResultBuilder = Callable[..., ActionResult]
PipelinePersister = Callable[[RemoteCommitPipelineContract], list[str]]


@dataclass(frozen=True, slots=True)
class CommitReceiptEmissionRequest:
    """Inputs needed to emit mutation, commit, lifecycle, and feature receipts."""

    action_id: str
    repo_root: Path
    completed: RemoteCommitPipelineContract
    artifact_paths: tuple[str, ...]
    persist_pipeline_contract_only: PipelinePersister
    result_builder: ResultBuilder


@dataclass(frozen=True, slots=True)
class CommitReceiptEmissionResult:
    """Result of emitting governed commit receipt artifacts."""

    artifact_paths: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    failure_result: ActionResult | None = None


def record_commit_receipt_chain(
    request: CommitReceiptEmissionRequest,
) -> CommitReceiptEmissionResult:
    """Emit receipts for the commit head and its managed content commit."""
    proof_result = record_commit_mutation_proof(
        CommitMutationProofRequest(
            action_id=request.action_id,
            repo_root=request.repo_root,
            completed=request.completed,
            artifact_paths=request.artifact_paths,
            persist_pipeline_contract_only=request.persist_pipeline_contract_only,
            result_builder=request.result_builder,
        )
    )
    if proof_result.failure_result is not None:
        return CommitReceiptEmissionResult(
            artifact_paths=proof_result.artifact_paths,
            failure_result=proof_result.failure_result,
        )

    artifact_paths = proof_result.artifact_paths
    warnings: list[str] = []
    content_commit_sha = _managed_receipt_content_sha(
        repo_root=request.repo_root,
        commit_sha=request.completed.commit_sha,
    )
    if content_commit_sha:
        content_completed = replace(request.completed, commit_sha=content_commit_sha)
        content_result = _record_content_commit_receipts(
            request=request,
            completed=content_completed,
            artifact_paths=artifact_paths,
        )
        if content_result.failure_result is not None:
            return content_result
        artifact_paths = content_result.artifact_paths
        warnings.extend(content_result.warnings)

    artifact_paths, commit_warnings = _write_commit_receipt_artifacts(
        repo_root=request.repo_root,
        completed=request.completed,
        artifact_paths=artifact_paths,
    )
    warnings.extend(commit_warnings)
    return CommitReceiptEmissionResult(
        artifact_paths=artifact_paths,
        warnings=tuple(warnings),
    )


def _record_content_commit_receipts(
    *,
    request: CommitReceiptEmissionRequest,
    completed: RemoteCommitPipelineContract,
    artifact_paths: tuple[str, ...],
) -> CommitReceiptEmissionResult:
    content_proof = record_commit_mutation_proof(
        CommitMutationProofRequest(
            action_id=request.action_id,
            repo_root=request.repo_root,
            completed=completed,
            artifact_paths=artifact_paths,
            persist_pipeline_contract_only=request.persist_pipeline_contract_only,
            result_builder=request.result_builder,
            allow_reachable_head=True,
        )
    )
    if content_proof.failure_result is not None:
        return CommitReceiptEmissionResult(
            artifact_paths=content_proof.artifact_paths,
            failure_result=content_proof.failure_result,
        )
    artifact_paths, warnings = _write_commit_receipt_artifacts(
        repo_root=request.repo_root,
        completed=completed,
        artifact_paths=content_proof.artifact_paths,
    )
    return CommitReceiptEmissionResult(
        artifact_paths=artifact_paths,
        warnings=tuple(warnings),
    )


def _managed_receipt_content_sha(*, repo_root: Path, commit_sha: str) -> str:
    content_sha = receipt_commit_parent_sha(
        repo_root=repo_root,
        current_head=commit_sha,
    )
    if content_sha and content_sha != commit_sha:
        return content_sha
    return ""


def _write_commit_receipt_artifacts(
    *,
    repo_root: Path,
    completed: RemoteCommitPipelineContract,
    artifact_paths: tuple[str, ...],
) -> tuple[tuple[str, ...], list[str]]:
    warnings: list[str] = []
    try:
        receipt = build_commit_receipt(
            completed,
            artifact_paths=artifact_paths,
        )
        artifact_paths = (
            *artifact_paths,
            write_commit_receipt_artifact(repo_root, receipt),
        )
        proof = build_feature_lifecycle_proof(completed, receipt)
        artifact_paths = (
            *artifact_paths,
            write_feature_lifecycle_proof_artifact(repo_root, proof),
        )
        feature_proof_receipt = build_feature_proof_receipt(
            completed,
            receipt,
            lifecycle_proof=proof,
            evidence_artifacts=artifact_paths,
            repo_root=repo_root,
        )
        artifact_paths = (
            *artifact_paths,
            write_feature_proof_receipt_artifact(
                repo_root,
                feature_proof_receipt,
            ),
        )
    except Exception as exc:  # broad-except: allow reason=commit already durable and receipt writers have heterogeneous IO/serialization failures fallback=warning evidence debt
        warnings.append(f"commit_receipt_write_failed:{exc}")
    return artifact_paths, warnings
