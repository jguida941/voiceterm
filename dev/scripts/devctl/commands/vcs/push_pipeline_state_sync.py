"""Sync remote commit-pipeline artifacts from governed push reports."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path

from ...repo_packs import active_path_config
from ...review_channel.event_store import resolve_artifact_paths
from ...review_channel.remote_commit_pipeline_artifact import (
    load_remote_commit_pipeline_contract,
    persist_remote_commit_pipeline_contract,
)
from ...runtime.remote_commit_pipeline_models import RemoteCommitPipelineContract
from ...runtime.remote_commit_pipeline_state import (
    AUTO_DELIVERY_TRANSITION_RULE,
    STATE_DELIVERED_LOCALLY_PENDING_PUBLISH,
)
from ...runtime.pipeline_recovery_receipt import utc_now_iso
from ...runtime.review_snapshot_refresh import (
    receipt_commit_ancestor_shas,
    receipt_commit_parent_sha,
)
from ...runtime.surface_snapshot import build_surface_snapshot_id, build_surface_zref
from .governed_executor_push_result import project_push_report


def sync_commit_pipeline_with_push_report(
    *,
    repo_root: Path,
    current_branch: str,
    current_remote: str,
    current_head_commit: str,
    approved_target_identity: str,
    report: Mapping[str, object],
    action_id: str = "vcs.push",
) -> bool:
    """Persist push-result truth onto the current matching pipeline artifact."""
    projections_root = Path(
        resolve_artifact_paths(repo_root=repo_root).projections_root
    )
    pipeline = load_remote_commit_pipeline_contract(output_root=projections_root)
    if not _pipeline_matches_current_push(
        repo_root=repo_root,
        pipeline=pipeline,
        current_branch=current_branch,
        current_remote=current_remote,
        current_head_commit=current_head_commit,
        approved_target_identity=approved_target_identity,
    ):
        return False

    projection = project_push_report(
        action_id=action_id,
        report=report,
        pipeline_artifact_relpath=_pipeline_artifact_relpath(
            repo_root=repo_root,
            projections_root=projections_root,
        ),
        pipeline_state=str(pipeline.state or "").strip(),
        local_commit_landed=bool(current_head_commit),
    )
    # Keep pipeline state monotonic: a no-op rerun on an already-published head
    # (e.g. reason=branch_already_pushed) must not regress a terminal
    # push_completed pipeline back to push_blocked.
    if (
        str(pipeline.state or "").strip() == "push_completed"
        and projection.next_state != "push_completed"
    ):
        return False
    update_fields: dict[str, object] = {}
    update_fields["state"] = projection.next_state
    update_fields["push_action_id"] = str(pipeline.push_action_id or action_id)
    update_fields["push_result"] = projection.push_result
    update_fields["push_pipeline_phases"] = projection.push_pipeline_phases
    update_fields["push_failure_transition"] = projection.push_failure_transition
    update_fields["push_report_path"] = projection.push_report_path
    update_fields["blocked_reason"] = projection.blocked_reason
    if _projection_auto_delivered_local(projection):
        update_fields.update(
            {
                "recovery_action_allowed": "",
                "local_delivery_reason": str(
                    projection.push_failure_transition.get("reason") or ""
                ),
                "delivered_at_utc": str(pipeline.delivered_at_utc or utc_now_iso()),
                "delivered_by": str(pipeline.delivered_by or "devctl.push"),
            }
        )
    updated = _attach_pipeline_surface_identity(
        repo_root=repo_root,
        projections_root=projections_root,
        pipeline=replace(pipeline, **update_fields),
        current_head_commit=current_head_commit,
    )
    if updated == pipeline:
        return False

    _persist_pipeline_contract(
        repo_root=repo_root,
        projections_root=projections_root,
        pipeline=updated,
    )
    return True


def _pipeline_matches_current_push(
    *,
    repo_root: Path,
    pipeline: RemoteCommitPipelineContract,
    current_branch: str,
    current_remote: str,
    current_head_commit: str,
    approved_target_identity: str,
) -> bool:
    if not str(pipeline.pipeline_id or "").strip():
        return False
    if current_branch and str(pipeline.branch or "").strip() != current_branch:
        return False
    pipeline_remote = str(pipeline.remote or "").strip()
    if current_remote and pipeline_remote and pipeline_remote != current_remote:
        return False
    pipeline_commit = str(pipeline.commit_sha or "").strip()
    if current_head_commit and pipeline_commit != current_head_commit:
        receipt_ancestors = receipt_commit_ancestor_shas(
            repo_root=repo_root,
            current_head=current_head_commit,
            governance=None,
        )
        receipt_parent = receipt_commit_parent_sha(
            repo_root=repo_root,
            current_head=current_head_commit,
            governance=None,
        )
        if pipeline_commit not in (*receipt_ancestors, receipt_parent):
            return False
    pipeline_target_identity = str(pipeline.approved_target_identity or "").strip()
    if (
        approved_target_identity
        and pipeline_target_identity
        and pipeline_target_identity != approved_target_identity
    ):
        return False
    return True


def _projection_auto_delivered_local(projection) -> bool:
    if projection.next_state != STATE_DELIVERED_LOCALLY_PENDING_PUBLISH:
        return False
    transition = projection.push_failure_transition
    return (
        str(transition.get("rule") or "") == AUTO_DELIVERY_TRANSITION_RULE
        and bool(transition.get("auto_transitioned"))
    )


def _persist_pipeline_contract(
    *,
    repo_root: Path,
    projections_root: Path,
    pipeline: RemoteCommitPipelineContract,
) -> None:
    persist_remote_commit_pipeline_contract(pipeline, output_root=projections_root)
    legacy_root = repo_root / active_path_config().review_status_dir_rel
    if legacy_root.resolve() != projections_root.resolve():
        persist_remote_commit_pipeline_contract(pipeline, output_root=legacy_root)


def _attach_pipeline_surface_identity(
    *,
    repo_root: Path,
    projections_root: Path,
    pipeline: RemoteCommitPipelineContract,
    current_head_commit: str,
) -> RemoteCommitPipelineContract:
    review_state = _load_mapping(projections_root / "review_state.json")
    compat = review_state.get("_compat") if isinstance(review_state, Mapping) else {}
    compat_mapping = compat if isinstance(compat, Mapping) else {}
    snapshot_id = build_surface_snapshot_id(
        reviewer_runtime=_mapping_or_none(review_state.get("reviewer_runtime")),
        commit_pipeline=pipeline,
        push_decision=_mapping_or_none(compat_mapping.get("push_decision")),
    )
    head_sha = (
        str(current_head_commit or "").strip()
        or _review_state_head_sha(review_state)
        or str(pipeline.commit_sha or "").strip()
    )
    return replace(
        pipeline,
        snapshot_id=snapshot_id,
        zref=build_surface_zref(snapshot_id=snapshot_id, head_sha=head_sha),
    )


def _load_mapping(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _mapping_or_none(value: object) -> Mapping[str, object] | None:
    return value if isinstance(value, Mapping) else None


def _review_state_head_sha(review_state: Mapping[str, object]) -> str:
    source_identity = review_state.get("source_identity")
    if isinstance(source_identity, Mapping):
        head_sha = str(source_identity.get("head_sha") or "").strip()
        if head_sha:
            return head_sha
    compat = review_state.get("_compat")
    if isinstance(compat, Mapping):
        push_decision = compat.get("push_decision")
        if isinstance(push_decision, Mapping):
            return str(push_decision.get("head_sha") or "").strip()
    return ""


def _pipeline_artifact_relpath(*, repo_root: Path, projections_root: Path) -> str:
    return str(
        (projections_root / "commit_pipeline.json")
        .resolve()
        .relative_to(repo_root.resolve())
    )
