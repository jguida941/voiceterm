"""Pipeline sync, approval, and projection-refresh logic for the executor."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ...governance.push_state_support import is_expired
from ...repo_packs import active_path_config
from ...review_channel.event_reducer import load_or_refresh_event_bundle, refresh_event_bundle
from ...review_channel.event_store import resolve_artifact_paths
from ...review_channel.remote_commit_pipeline_artifact import (
    persist_remote_commit_pipeline_contract,
)
from ...review_channel.state import refresh_status_snapshot
from ...runtime import review_state_from_payload
from ...runtime.remote_commit_pipeline_models import RemoteCommitPipelineContract
from ...runtime.review_state_models import ReviewPacketState
from .governed_executor_authorization import (
    approved_target_identity,
    build_push_authorization,
)
from .governed_executor_field_access import string_value
from .governed_executor_packets import (
    approval_decision_packet,
    latest_matching_packet,
)


def sync_pipeline_approval(
    pipeline: RemoteCommitPipelineContract,
    packets: tuple[ReviewPacketState, ...],
    *,
    approval_packet_kind: str,
) -> RemoteCommitPipelineContract:
    """Reconcile pipeline approval state against the latest event packets."""
    request_packet = latest_matching_packet(
        packets,
        pipeline,
        require_apply=False,
        request_kind="request",
        approval_packet_kind=approval_packet_kind,
    )
    decision_packet = latest_matching_packet(
        packets,
        pipeline,
        require_apply=True,
        request_kind="decision",
        approval_packet_kind=approval_packet_kind,
    )
    approval_state = "not_requested"
    next_state = pipeline.state
    blocked_reason = pipeline.blocked_reason
    approval_expires_at_utc = ""
    approved_identity = ""

    if request_packet is not None:
        approval_state = "pending"
        next_state = "operator_approval_pending"
        blocked_reason = ""
        approval_expires_at_utc = request_packet.expires_at_utc

    if decision_packet is not None:
        approval_expires_at_utc = (
            decision_packet.expires_at_utc or approval_expires_at_utc
        )
        if is_expired(decision_packet.expires_at_utc):
            approval_state = "expired"
            next_state = "push_blocked"
            blocked_reason = "approval_expired"
        elif decision_packet.requested_action == "reject_commit_pipeline":
            approval_state = "rejected"
            next_state = "rejected"
            blocked_reason = "approval_rejected"
        else:
            approval_state = "approved"
            next_state = "approved"
            blocked_reason = ""
            approved_identity = approved_target_identity(
                staged_tree_hash=pipeline.intent.staged_tree_hash,
                decision_packet=decision_packet,
                fallback_generation=pipeline.generation_id,
            )

    return replace(
        pipeline,
        state=next_state,
        approval_packet_id=(
            request_packet.packet_id if request_packet is not None else ""
        ),
        decision_packet_id=(
            decision_packet.packet_id if decision_packet is not None else ""
        ),
        approval_state=approval_state,
        approval_expires_at_utc=approval_expires_at_utc,
        approved_target_identity=approved_identity,
        blocked_reason=blocked_reason,
    )


def get_approval_decision_packet(
    packets: tuple[ReviewPacketState, ...],
    pipeline: RemoteCommitPipelineContract,
    *,
    approval_packet_kind: str,
) -> ReviewPacketState:
    """Return the latest matching approval decision packet."""
    return approval_decision_packet(
        packets,
        pipeline,
        approval_packet_kind=approval_packet_kind,
    )


def sync_pipeline_push_authorization(
    pipeline: RemoteCommitPipelineContract,
    packets: tuple[ReviewPacketState, ...],
    *,
    approval_packet_kind: str,
    persist_fn: object,
) -> RemoteCommitPipelineContract:
    """Re-check for override-push packets and update authorization."""
    if not pipeline.commit_sha:
        return pipeline
    override_packet = latest_matching_packet(
        packets,
        pipeline,
        require_apply=True,
        request_kind="override_decision",
        approval_packet_kind=approval_packet_kind,
        allowed_target_revisions=(pipeline.approved_target_identity,),
    )
    if override_packet is None or is_expired(override_packet.expires_at_utc):
        return pipeline
    authorization = build_push_authorization(
        pipeline=pipeline,
        commit_sha=pipeline.commit_sha,
        decision_packet=override_packet,
        approval_mode="override_push",
        override_reason=string_value(override_packet.summary)
        or string_value(override_packet.body),
    )
    if pipeline.push_authorization == authorization:
        return pipeline
    updated = replace(
        pipeline,
        push_authorization=authorization,
    )
    persist_fn(updated)  # type: ignore[operator]
    return updated


def persist_pipeline(
    pipeline: RemoteCommitPipelineContract,
    *,
    projections_root: Path,
    repo_root: Path,
    refresh_projections: bool,
    review_channel_path: Path | None,
    bridge_path: Path | None,
) -> list[str]:
    """Write the pipeline contract and refresh review projections."""
    persist_remote_commit_pipeline_contract(pipeline, output_root=projections_root)
    legacy_root = repo_root / active_path_config().review_status_dir_rel
    if legacy_root.resolve() != projections_root.resolve():
        persist_remote_commit_pipeline_contract(pipeline, output_root=legacy_root)
    return refresh_review_projections(
        repo_root=repo_root,
        refresh_projections=refresh_projections,
        review_channel_path=review_channel_path,
        bridge_path=bridge_path,
        projections_root=projections_root,
    )


def refresh_review_projections(
    *,
    repo_root: Path,
    refresh_projections: bool,
    review_channel_path: Path | None,
    bridge_path: Path | None,
    projections_root: Path,
) -> list[str]:
    """Refresh event bundle or status snapshot after pipeline changes."""
    if not refresh_projections or review_channel_path is None:
        return []
    warnings: list[str] = []
    try:
        artifact_paths = resolve_artifact_paths(repo_root=repo_root)
        event_log = Path(artifact_paths.event_log_path)
        state_path = Path(artifact_paths.state_path)
        if event_log.exists() or state_path.exists():
            refresh_event_bundle(
                repo_root=repo_root,
                review_channel_path=review_channel_path,
                artifact_paths=artifact_paths,
            )
        elif bridge_path is not None and bridge_path.exists():
            refresh_status_snapshot(
                repo_root=repo_root,
                bridge_path=bridge_path,
                review_channel_path=review_channel_path,
                output_root=projections_root,
            )
    except (OSError, ValueError) as exc:
        warnings.append(f"projection_refresh_failed: {exc}")
    return warnings


def load_event_packets(
    *,
    repo_root: Path,
    review_channel_path: Path | None,
) -> tuple[ReviewPacketState, ...]:
    """Load review-channel event packets for approval sync."""
    if review_channel_path is None or not review_channel_path.exists():
        return ()
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    event_log = Path(artifact_paths.event_log_path)
    state_path = Path(artifact_paths.state_path)
    if not event_log.exists() and not state_path.exists():
        return ()
    try:
        bundle = load_or_refresh_event_bundle(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        )
    except ValueError:
        return ()
    return review_state_from_payload(bundle.review_state).packets
