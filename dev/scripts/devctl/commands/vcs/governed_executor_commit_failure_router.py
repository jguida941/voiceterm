"""Failure-packet routing adapter for governed commit failures."""

from __future__ import annotations

from pathlib import Path

from ...review_channel.event_store import load_events, resolve_artifact_paths
from ...review_channel.failure_packet_router import (
    FailureRouterContext,
    route_action_result_failure,
)
from ...review_channel.state import project_id_for_repo
from ...runtime import ActionResult
from ...runtime.remote_commit_pipeline_models import RemoteCommitPipelineContract


def route_commit_failure_result(
    *,
    result: ActionResult,
    repo_root: Path,
    pending_pipeline: RemoteCommitPipelineContract,
) -> list[str]:
    """Route eligible commit failures through the shared packet adapter."""
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    try:
        written = route_action_result_failure(
            result=result.to_dict(),
            context=FailureRouterContext(
                repo_root=repo_root,
                artifact_paths=artifact_paths,
                project_id=project_id_for_repo(repo_root),
                session_id=pending_pipeline.pipeline_id or "governed-vcs-commit",
                controller_run_id=result.action_id,
            ),
            existing_events=load_events(Path(artifact_paths.event_log_path)),
            completed_handoff_session_id=(
                pending_pipeline.pipeline_id or "governed-vcs-commit"
            ),
        )
    # broad-except: allow reason=optional packet routing must not mask commit failure; fallback=return warning on original ActionResult.
    except Exception as exc:  # pragma: no cover - defensive failure reporting
        return [f"failure_packet_router_error={type(exc).__name__}:{exc}"]
    if not written:
        return []
    warnings = [f"failure_packet_router_events={len(written)}"]
    packet_id = str(written[0].get("packet_id") or "").strip()
    if packet_id:
        warnings.append(f"failure_packet_router_packet={packet_id}")
    return warnings
