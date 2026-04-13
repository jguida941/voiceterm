"""Publish-truth helpers shared by reviewer doctor/readiness projections."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ..runtime.project_governance_push import (
    PushEnforcement,
    push_enforcement_from_mapping,
)
from ..runtime.remote_commit_pipeline_models import (
    RemoteCommitPipelineContract,
)
from ..runtime.startup_push_recovery import artifact_records_current_head_publish


@dataclass(frozen=True, slots=True)
class PublicationTruth:
    """Resolved publish truth projected from pipeline or persisted push artifacts."""

    published_remote: bool = False
    post_push_green: bool = False
    source: str = "none"
    push_report_path: str = ""


def resolve_publication_truth(
    *,
    pipeline: RemoteCommitPipelineContract,
    push_enforcement: Mapping[str, object] | None,
) -> PublicationTruth:
    """Resolve publish truth, preferring a live pipeline over persisted artifacts."""
    pipeline_is_current = pipeline_matches_current_publication_target(
        pipeline=pipeline,
        push_enforcement=push_enforcement,
    )
    pipeline_truth = PublicationTruth(
        published_remote=(
            _pipeline_published_remote(pipeline) if pipeline_is_current else False
        ),
        post_push_green=(
            _pipeline_post_push_green(pipeline) if pipeline_is_current else False
        ),
        source=(
            "commit_pipeline"
            if pipeline_is_current and _pipeline_published_remote(pipeline)
            else "none"
        ),
        push_report_path=(
            str(pipeline.push_report_path or "") if pipeline_is_current else ""
        ),
    )
    if pipeline_truth.published_remote:
        return pipeline_truth
    artifact_truth = _artifact_publication_truth(push_enforcement)
    if artifact_truth.published_remote:
        return artifact_truth
    if pipeline_truth.push_report_path:
        return pipeline_truth
    return artifact_truth


def resolve_publication_blocked_reason(
    *,
    pipeline: RemoteCommitPipelineContract,
    push_enforcement: Mapping[str, object] | None,
) -> str:
    """Resolve the most specific publish-stage blocked reason available."""
    reason = (
        str(pipeline.blocked_reason or "")
        if pipeline_matches_current_publication_target(
            pipeline=pipeline,
            push_enforcement=push_enforcement,
        )
        else ""
    )
    if reason and reason != "pipeline_unavailable":
        return reason
    enforcement = _push_enforcement(push_enforcement)
    if enforcement is None:
        return reason
    if not _artifact_matches_current_publication_target(enforcement):
        return reason
    return str(enforcement.latest_push_report_reason or reason)


def _pipeline_published_remote(pipeline: RemoteCommitPipelineContract) -> bool:
    if pipeline.state == "push_completed":
        return True
    if pipeline.push_result is None:
        return False
    if pipeline.push_result.partial_progress:
        return True
    return bool(pipeline.push_result.ok and pipeline.push_result.status == "pass")


def _pipeline_post_push_green(pipeline: RemoteCommitPipelineContract) -> bool:
    return pipeline.state == "push_completed" and _pipeline_published_remote(pipeline)


def current_pipeline_projection(
    *,
    pipeline: RemoteCommitPipelineContract,
    push_enforcement: Mapping[str, object] | None,
) -> RemoteCommitPipelineContract:
    """Return the live pipeline only when it still matches the current target."""
    if pipeline_matches_current_publication_target(
        pipeline=pipeline,
        push_enforcement=push_enforcement,
    ):
        return pipeline
    return RemoteCommitPipelineContract()


def _artifact_publication_truth(
    push_enforcement: Mapping[str, object] | None,
) -> PublicationTruth:
    enforcement = _push_enforcement(push_enforcement)
    if enforcement is None:
        return PublicationTruth()
    path = str(enforcement.latest_push_report_path or "")
    if not _artifact_matches_current_publication_target(enforcement):
        return PublicationTruth(push_report_path=path)
    return PublicationTruth(
        published_remote=True,
        post_push_green=bool(enforcement.latest_push_report_post_push_green),
        source="latest_push_report",
        push_report_path=path,
    )


def _push_enforcement(
    payload: Mapping[str, object] | None,
) -> PushEnforcement | None:
    if not isinstance(payload, Mapping):
        return None
    return push_enforcement_from_mapping(payload)


def pipeline_matches_current_publication_target(
    *,
    pipeline: RemoteCommitPipelineContract,
    push_enforcement: Mapping[str, object] | None,
) -> bool:
    """Return True when the pipeline still belongs to the current branch/HEAD target."""
    if not _pipeline_has_projection_state(pipeline):
        return False
    enforcement = _push_enforcement(push_enforcement)
    if enforcement is None:
        return True

    pipeline_branch = str(pipeline.branch or "").strip()
    if pipeline_branch and enforcement.current_branch:
        if pipeline_branch != enforcement.current_branch:
            return False

    pipeline_commit_sha = str(pipeline.commit_sha or "").strip()
    if pipeline_commit_sha and enforcement.current_head_commit:
        if pipeline_commit_sha != enforcement.current_head_commit:
            return False

    pipeline_target = str(pipeline.approved_target_identity or "").strip()
    if pipeline_target and enforcement.current_approved_target_identity:
        if pipeline_target != enforcement.current_approved_target_identity:
            return False

    pipeline_worktree = str(pipeline.worktree_identity or "").strip()
    if pipeline_worktree and enforcement.current_worktree_identity:
        if pipeline_worktree != enforcement.current_worktree_identity:
            return False

    pipeline_remote = str(pipeline.remote or "").strip()
    current_remote = _current_target_remote(enforcement)
    if pipeline_remote and current_remote and pipeline_remote != current_remote:
        return False

    return True


def _current_target_remote(push_enforcement: PushEnforcement) -> str:
    upstream_ref = str(getattr(push_enforcement, "upstream_ref", "") or "")
    if "/" in upstream_ref:
        return upstream_ref.split("/", 1)[0]
    return str(getattr(push_enforcement, "default_remote", "") or "")


def _pipeline_has_projection_state(pipeline: RemoteCommitPipelineContract) -> bool:
    """Return True when the pipeline carries any non-default projection state."""
    return bool(
        str(pipeline.pipeline_id or "").strip()
        or str(pipeline.branch or "").strip()
        or str(pipeline.remote or "").strip()
        or str(pipeline.commit_sha or "").strip()
        or str(pipeline.push_report_path or "").strip()
        or str(pipeline.approved_target_identity or "").strip()
        or str(pipeline.worktree_identity or "").strip()
        or str(pipeline.blocked_reason or "").strip() != "pipeline_unavailable"
        or pipeline.guard_result is not None
        or pipeline.commit_result is not None
        or pipeline.push_result is not None
        or pipeline.push_authorization is not None
        or str(pipeline.approval_state or "").strip() != "not_requested"
    )


def _artifact_matches_current_publication_target(
    enforcement: PushEnforcement,
) -> bool:
    return artifact_records_current_head_publish(enforcement)
