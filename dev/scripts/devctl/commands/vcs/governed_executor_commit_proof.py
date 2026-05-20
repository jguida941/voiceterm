"""Git mutation proof support for governed commit execution."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path

from ...runtime import ActionResult
from ...runtime.action_contracts import ActionOutcome
from ...runtime.correlation_spine import CorrelationContext
from ...runtime.git_mutation_proof_receipt import (
    GitMutationProofReceipt,
    append_git_mutation_proof_receipt,
    build_commit_git_mutation_proof_receipt,
)
from ...runtime.remote_commit_pipeline_models import RemoteCommitPipelineContract
from .governed_executor_field_access import string_value

ResultBuilder = Callable[..., ActionResult]
PipelinePersister = Callable[[RemoteCommitPipelineContract], list[str]]


@dataclass(frozen=True, slots=True)
class CommitMutationProofResult:
    """Outcome of writing and verifying the commit mutation proof."""

    artifact_paths: tuple[str, ...]
    failure_result: ActionResult | None = None


@dataclass(frozen=True, slots=True)
class CommitMutationProofRequest:
    """Inputs needed to write one commit mutation proof row."""

    action_id: str
    repo_root: Path
    completed: RemoteCommitPipelineContract
    artifact_paths: tuple[str, ...]
    persist_pipeline_contract_only: PipelinePersister
    result_builder: ResultBuilder
    allow_reachable_head: bool = False


def record_commit_mutation_proof(
    request: CommitMutationProofRequest,
) -> CommitMutationProofResult:
    """Write the required GitMutationProofReceipt for a committed pipeline."""

    completed = request.completed
    commit_result = completed.commit_result
    mutation_proof = build_commit_git_mutation_proof_receipt(
        repo_root=request.repo_root,
        claim=GitMutationProofReceipt(
            mutation_kind="commit",
            action_id=request.action_id,
            pipeline_id=completed.pipeline_id,
            plan_row_id=_plan_row_id(completed),
            expected_sha=completed.commit_sha,
            command_returncode=0,
            operation_returned_success=True,
            artifact_paths=request.artifact_paths,
            correlation_context=CorrelationContext(
                correlation_id=string_value(
                    getattr(commit_result, "correlation_id", "")
                ),
                causation_id=string_value(getattr(commit_result, "causation_id", "")),
                run_id=string_value(getattr(commit_result, "run_id", "")),
            ),
        ),
        allow_reachable_head=request.allow_reachable_head,
    )
    try:
        proof_store = append_git_mutation_proof_receipt(
            request.repo_root,
            mutation_proof,
        )
    # broad-except: allow reason=proof receipt store boundary must return typed failure fallback=ActionResult
    except Exception as exc:
        return CommitMutationProofResult(
            artifact_paths=request.artifact_paths,
            failure_result=_proof_write_failure(
                action_id=request.action_id,
                completed=completed,
                artifact_paths=request.artifact_paths,
                persist_pipeline_contract_only=request.persist_pipeline_contract_only,
                result_builder=request.result_builder,
                error=exc,
            ),
        )

    next_paths = request.artifact_paths
    if proof_store not in next_paths:
        next_paths = (*next_paths, proof_store)
    if mutation_proof.verified:
        return CommitMutationProofResult(artifact_paths=next_paths)
    return CommitMutationProofResult(
        artifact_paths=next_paths,
        failure_result=_proof_verification_failure(
            action_id=request.action_id,
            completed=completed,
            artifact_paths=next_paths,
            persist_pipeline_contract_only=request.persist_pipeline_contract_only,
            result_builder=request.result_builder,
            failure_reason=mutation_proof.failure_reason,
        ),
    )


def _plan_row_id(completed: RemoteCommitPipelineContract) -> str:
    plan = completed.intent.validation_plan
    return string_value(plan.plan_id) if plan is not None else ""


def _proof_write_failure(
    *,
    action_id: str,
    completed: RemoteCommitPipelineContract,
    artifact_paths: tuple[str, ...],
    persist_pipeline_contract_only: PipelinePersister,
    result_builder: ResultBuilder,
    error: Exception,
) -> ActionResult:
    warnings = persist_pipeline_contract_only(
        replace(
            completed,
            state="push_blocked",
            blocked_reason="commit_proof_write_failed",
        )
    )
    warnings.append(f"git_mutation_proof_write_failed:{error}")
    return result_builder(
        action_id=action_id,
        ok=False,
        status=ActionOutcome.FAIL,
        reason="commit_proof_write_failed",
        operator_guidance=(
            "Git commit returned success, but the required "
            "GitMutationProofReceipt store could not be written. Repair the "
            "receipt store before treating this commit as proof."
        ),
        warnings=tuple(warnings),
        artifact_paths=artifact_paths,
    )


def _proof_verification_failure(
    *,
    action_id: str,
    completed: RemoteCommitPipelineContract,
    artifact_paths: tuple[str, ...],
    persist_pipeline_contract_only: PipelinePersister,
    result_builder: ResultBuilder,
    failure_reason: str,
) -> ActionResult:
    warnings = persist_pipeline_contract_only(
        replace(
            completed,
            state="push_blocked",
            blocked_reason="commit_proof_failed",
        )
    )
    warnings.append(f"git_mutation_proof_failed:{failure_reason}")
    return result_builder(
        action_id=action_id,
        ok=False,
        status=ActionOutcome.FAIL,
        reason="commit_proof_failed",
        operator_guidance=(
            "Git commit returned success, but the claimed commit SHA could "
            "not be verified as the current local HEAD. Inspect git state "
            "before treating this commit as proof."
        ),
        warnings=tuple(warnings),
        artifact_paths=artifact_paths,
    )
