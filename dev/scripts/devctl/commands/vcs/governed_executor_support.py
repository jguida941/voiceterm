"""Commit-readiness helpers for the governed executor."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

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
) -> RemoteCommitPipelineContract:
    """Return the blocked pipeline shape for a failed governed commit."""
    return replace(
        pending_pipeline,
        state="push_blocked",
        commit_result=result_builder(
            action_id=action_id,
            ok=False,
            status=ActionOutcome.FAIL,
            reason="commit_failed",
            operator_guidance=_commit_failure_guidance(),
            warnings=((commit_error,) if commit_error else ()),
            artifact_paths=(artifact_relpath,),
        ),
        blocked_reason="commit_failed",
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
    commit_message: str


def evaluate_commit_readiness(
    *,
    pipeline: RemoteCommitPipelineContract,
    current_tree_hash: str,
    requested_commit_message: str,
) -> CommitReadiness | CommitBlock:
    """Validate commit preconditions after approval sync and runtime checks."""
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
    if not pipeline.approval_packet_id or not pipeline.decision_packet_id:
        return CommitBlock(
            pipeline=pipeline,
            reason="approval_packet_missing",
            guidance=(
                "The approved pipeline must carry both the approval request "
                "packet and the applied operator decision packet."
            ),
        )
    if current_tree_hash != pipeline.intent.staged_tree_hash:
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
    commit_message = requested_commit_message or pipeline.intent.commit_message_draft
    if not commit_message:
        return CommitBlock(
            pipeline=pipeline,
            reason="commit_message_missing",
            guidance="Set `commit_message_draft` during `vcs.stage` before committing.",
        )
    return CommitReadiness(pipeline=pipeline, commit_message=commit_message)


def _commit_failure_guidance() -> str:
    return "Inspect the git commit failure, repair the repo state, then recover the pipeline."
