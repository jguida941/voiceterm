"""Commit-readiness helpers for the governed executor."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

from ...review_channel.service_identity import worktree_identity_for_repo
from ...runtime import ActionResult
from ...runtime.action_contracts import ActionOutcome
from ...runtime.remote_commit_pipeline_models import (
    PushAuthorizationRecord,
    RemoteCommitPipelineContract,
)


def commit_failed_pipeline(
    *,
    pending_pipeline: RemoteCommitPipelineContract,
    action_id: str,
    commit_error: str,
    artifact_relpath: str,
    result_builder: Callable[..., ActionResult],
    failure: CommitFailureDetails | None = None,
) -> RemoteCommitPipelineContract:
    """Return the blocked pipeline shape for a failed governed commit."""
    resolved_failure = failure or CommitFailureDetails()
    return replace(
        pending_pipeline,
        state="push_blocked",
        commit_result=result_builder(
            action_id=action_id,
            ok=False,
            status=ActionOutcome.FAIL,
            reason=resolved_failure.reason,
            operator_guidance=(
                resolved_failure.operator_guidance or _commit_failure_guidance()
            ),
            warnings=((commit_error,) if commit_error else ()),
            artifact_paths=(artifact_relpath,),
        ),
        blocked_reason=resolved_failure.reason,
    )


def commit_recorded_pipeline(
    *,
    pending_pipeline: RemoteCommitPipelineContract,
    action_id: str,
    commit_sha: str,
    push_authorization: PushAuthorizationRecord,
    artifact_relpath: str,
    result_builder: Callable[..., ActionResult],
) -> RemoteCommitPipelineContract:
    """Return the recorded pipeline shape for a successful governed commit."""
    return replace(
        pending_pipeline,
        state="commit_recorded",
        commit_result=result_builder(
            action_id=action_id,
            ok=True,
            status=ActionOutcome.PASS,
            reason="commit_recorded",
            operator_guidance="The approved staged snapshot is now committed.",
            artifact_paths=(artifact_relpath,),
        ),
        commit_sha=commit_sha,
        push_authorization=push_authorization,
        blocked_reason="",
    )


@dataclass(frozen=True, slots=True)
class CommitBlock:
    """Commit-stage blocker emitted by governed preflight checks."""

    pipeline: RemoteCommitPipelineContract
    reason: str
    guidance: str


@dataclass(frozen=True, slots=True)
class CommitReadiness:
    """Validated commit inputs ready for governed git commit execution."""

    pipeline: RemoteCommitPipelineContract
    git_commit_args: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CommitInvocation:
    """Typed commit request inputs used by readiness validation."""

    current_tree_hash: str
    requested_commit_message: str
    amend: bool = False
    allow_empty: bool = False
    no_edit: bool = False


@dataclass(frozen=True, slots=True)
class CommitFailureDetails:
    """Structured failure metadata for blocked governed commit results."""

    reason: str = "commit_failed"
    operator_guidance: str | None = None


def evaluate_commit_readiness(
    *,
    pipeline: RemoteCommitPipelineContract,
    repo_root,
    request: CommitInvocation,
) -> CommitReadiness | CommitBlock:
    """Validate commit preconditions after approval sync and runtime checks."""
    validation_block = _validation_contract_block(pipeline)
    if validation_block is not None:
        return validation_block
    if pipeline.guard_result is None or pipeline.guard_result.status != ActionOutcome.PASS:
        return CommitBlock(
            pipeline=pipeline,
            reason="guards_not_passed",
            guidance=(
                "Run the routed guard bundle and record a passing result before "
                "`vcs.commit`."
            ),
        )
    if pipeline.approval_state != "approved" or pipeline.state != "approved":
        return CommitBlock(
            pipeline=pipeline,
            reason="operator_approval_missing",
            guidance=(
                "Post and apply the matching `commit_approval` decision packet "
                "before `vcs.commit`."
            ),
        )
    current_worktree_identity = worktree_identity_for_repo(repo_root)
    if (
        pipeline.worktree_identity
        and current_worktree_identity
        and pipeline.worktree_identity != current_worktree_identity
    ):
        return CommitBlock(
            pipeline=replace(
                pipeline,
                state="push_blocked",
                blocked_reason="worktree_identity_mismatch",
            ),
            reason="worktree_identity_mismatch",
            guidance=(
                "The approved pipeline belongs to a different worktree. Resume the "
                "worker-lane checkout that staged the snapshot or recover and restage "
                "the pipeline in this worktree before committing."
            ),
        )
    if not pipeline.approval_packet_id or not pipeline.decision_packet_id:
        return CommitBlock(
            pipeline=pipeline,
            reason="approval_packet_missing",
            guidance=(
                "The approved pipeline must carry both the approval request "
                "packet and the applied operator decision packet."
            ),
        )
    if request.current_tree_hash != pipeline.intent.staged_tree_hash:
        return CommitBlock(
            pipeline=replace(
                pipeline,
                state="push_blocked",
                blocked_reason="staged_snapshot_changed",
            ),
            reason="staged_snapshot_changed",
            guidance=(
                "The staged snapshot drifted after approval. Recover and request "
                "a fresh approval packet."
            ),
        )
    commit_message = (
        request.requested_commit_message or pipeline.intent.commit_message_draft
    )
    if request.no_edit and not request.amend:
        return CommitBlock(
            pipeline=pipeline,
            reason="no_edit_requires_amend",
            guidance="`--no-edit` is only supported together with `--amend`.",
        )
    if not commit_message and not (request.amend and request.no_edit):
        return CommitBlock(
            pipeline=pipeline,
            reason="commit_message_missing",
            guidance="Set `commit_message_draft` during `vcs.stage` before committing.",
        )

    # The governed stage path already refreshes/stages ReviewSnapshot and runs
    # the required guard bundle before commit, so skipping repo hooks here
    # avoids re-entering the raw-git authority gate from the governed path.
    git_commit_args: list[str] = [
        "-c",
        "devctl.governed-commit=true",
        "commit",
        "--no-verify",
    ]
    if request.amend:
        git_commit_args.append("--amend")
    if request.allow_empty:
        git_commit_args.append("--allow-empty")
    if request.no_edit:
        git_commit_args.append("--no-edit")
    if commit_message:
        git_commit_args.extend(["-m", commit_message])
    return CommitReadiness(
        pipeline=pipeline,
        git_commit_args=tuple(git_commit_args),
    )


def _validation_contract_block(
    pipeline: RemoteCommitPipelineContract,
) -> CommitBlock | None:
    if pipeline.intent.validation_plan is None:
        return _blocked_pipeline(
            pipeline,
            reason="validation_plan_missing",
            guidance=(
                "Restage the governed pipeline so the validation plan is bound "
                "to the staged snapshot before committing."
            ),
        )
    if pipeline.validation_receipt is None:
        return _blocked_pipeline(
            pipeline,
            reason="validation_receipt_missing",
            guidance="Run and record the routed guard bundle before `vcs.commit`.",
        )
    if pipeline.validation_receipt.staged_tree_hash != pipeline.intent.staged_tree_hash:
        return _blocked_pipeline(
            pipeline,
            reason="validation_receipt_stale",
            guidance=(
                "The current validation receipt does not match the staged tree. "
                "Restage and rerun the guard bundle."
            ),
        )
    if not pipeline.validation_receipt.checkpoint_sufficient:
        return _blocked_pipeline(
            pipeline,
            reason="validation_receipt_insufficient",
            guidance=(
                "The recorded validation receipt is not sufficient for a "
                "governed commit."
            ),
        )
    return None


def _blocked_pipeline(
    pipeline: RemoteCommitPipelineContract,
    *,
    reason: str,
    guidance: str,
) -> CommitBlock:
    return CommitBlock(
        pipeline=replace(
            pipeline,
            state="push_blocked",
            blocked_reason=reason,
        ),
        reason=reason,
        guidance=guidance,
    )


def _commit_failure_guidance() -> str:
    return "Inspect the git commit failure, repair the repo state, then recover the pipeline."
