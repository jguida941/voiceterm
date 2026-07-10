"""Push-authorization helpers for the governed VCS executor."""

from __future__ import annotations

from ...runtime.remote_commit_pipeline_models import (
    PushAuthorizationRecord,
    RemoteCommitPipelineContract,
)
from ...runtime.review_state_models import ReviewPacketState


def approved_target_identity(
    *,
    staged_tree_hash: str,
    decision_packet: ReviewPacketState,
    fallback_generation: str,
) -> str:
    """Build the reviewer-approved tree receipt carried into push recovery."""
    receipt_timestamp = (
        decision_packet.applied_at_utc
        or decision_packet.posted_at
        or fallback_generation
    )
    receipt_id = f"tree-receipt-{_safe_timestamp_token(receipt_timestamp)}"
    return f"{receipt_id}:{staged_tree_hash}"


def build_push_authorization(
    *,
    pipeline: RemoteCommitPipelineContract,
    commit_sha: str,
    decision_packet: ReviewPacketState,
    approval_mode: str,
    request_packet_id: str = "",
    override_reason: str = "",
) -> PushAuthorizationRecord:
    """Build the publication proof consumed by later governed pushes."""
    approved_at = (
        decision_packet.applied_at_utc
        or decision_packet.posted_at
        or pipeline.generation_id
    )
    authorization_id = f"push-auth-{_safe_timestamp_token(approved_at)}"
    guard_result = pipeline.guard_result
    return PushAuthorizationRecord(
        authorization_id=authorization_id,
        pipeline_id=pipeline.pipeline_id,
        generation_id=pipeline.generation_id,
        authorized_head_sha=commit_sha,
        approved_target_identity=pipeline.approved_target_identity,
        review_verdict=(
            "override_push_approved"
            if approval_mode == "override_push"
            else "approved"
        ),
        approval_mode=approval_mode,
        guard_action_id=pipeline.guard_action_id,
        guard_status=getattr(guard_result, "status", ""),
        guard_reason=getattr(guard_result, "reason", ""),
        request_packet_id=request_packet_id,
        decision_packet_id=decision_packet.packet_id,
        approved_by=decision_packet.from_agent,
        approved_at_utc=approved_at,
        expires_at_utc=(
            decision_packet.expires_at_utc or pipeline.approval_expires_at_utc
        ),
        override_reason=override_reason,
        worktree_identity=pipeline.worktree_identity,
    )


def _safe_timestamp_token(timestamp: str) -> str:
    return timestamp.replace("-", "").replace(":", "").replace(".", "").replace("+", "")
