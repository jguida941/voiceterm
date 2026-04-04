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
    pipeline_truth = PublicationTruth(
        published_remote=_pipeline_published_remote(pipeline),
        post_push_green=_pipeline_post_push_green(pipeline),
        source="commit_pipeline" if _pipeline_published_remote(pipeline) else "none",
        push_report_path=str(pipeline.push_report_path or ""),
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
    reason = str(pipeline.blocked_reason or "")
    if reason and reason != "pipeline_unavailable":
        return reason
    enforcement = _push_enforcement(push_enforcement)
    if enforcement is None:
        return reason
    if not _artifact_matches_current_head(enforcement):
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


def _artifact_publication_truth(
    push_enforcement: Mapping[str, object] | None,
) -> PublicationTruth:
    enforcement = _push_enforcement(push_enforcement)
    if enforcement is None:
        return PublicationTruth()
    path = str(enforcement.latest_push_report_path or "")
    if not _artifact_matches_current_head(enforcement):
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


def _artifact_matches_current_head(enforcement: PushEnforcement) -> bool:
    if not enforcement.latest_push_report_published_remote:
        return False
    branch_matches = enforcement.latest_push_report_matches_current_branch or bool(
        enforcement.current_branch
        and enforcement.latest_push_report_branch
        and enforcement.current_branch == enforcement.latest_push_report_branch
    )
    head_matches = enforcement.latest_push_report_matches_current_head or bool(
        enforcement.current_head_commit
        and enforcement.latest_push_report_head_commit
        and enforcement.current_head_commit == enforcement.latest_push_report_head_commit
    )
    remote_matches = (
        not enforcement.latest_push_report_remote
        or enforcement.latest_push_report_remote == enforcement.default_remote
    )
    return branch_matches and head_matches and remote_matches
