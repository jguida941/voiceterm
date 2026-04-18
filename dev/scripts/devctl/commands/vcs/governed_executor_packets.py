"""Typed packet helpers for the governed VCS executor."""

from __future__ import annotations

import json
from collections.abc import Sequence

from ...review_channel.packet_contract import (
    PacketPostRequest,
    PacketRuntimeApprovalFields,
    PacketTargetFields,
)
from ...runtime import ActionResult
from ...runtime.remote_commit_pipeline_models import RemoteCommitPipelineContract
from ...runtime.review_state_models import ReviewPacketState


def build_commit_approval_request(
    pipeline: RemoteCommitPipelineContract,
    *,
    approval_packet_kind: str = "commit_approval",
    expires_in_minutes: int = 30,
    to_agent: str = "operator",
) -> PacketPostRequest:
    """Build the canonical operator approval request packet for one pipeline."""
    return PacketPostRequest(
        from_agent="system",
        to_agent=to_agent,
        kind=approval_packet_kind,
        summary=f"Approve governed commit pipeline `{pipeline.pipeline_id}`",
        body=(
            "Operator approval is required before the governed executor may "
            "commit the staged snapshot."
        ),
        requested_action="approve_commit_pipeline",
        policy_hint="operator_approval_required",
        approval_required=True,
        trace_id=pipeline.pipeline_id,
        expires_in_minutes=expires_in_minutes,
        target=PacketTargetFields.from_values(
            target_kind="runtime",
            target_ref=pipeline_target_ref(pipeline),
            target_revision=pipeline.generation_id,
        ),
        runtime_approval=PacketRuntimeApprovalFields.from_values(
            pipeline_generation=pipeline.generation_id,
            staged_snapshot_hash=pipeline.intent.staged_tree_hash,
            guard_results_summary=guard_results_summary(pipeline.guard_result),
        ),
    )


def build_commit_execution_request(
    pipeline: RemoteCommitPipelineContract,
    *,
    to_agent: str,
    summary: str = "",
    body: str = "",
    expires_in_minutes: int = 30,
) -> PacketPostRequest:
    """Build the canonical typed handoff packet for commit execution.

    This packet is used after the governed pipeline is already approved, but
    the current executor cannot write the git index locally. The runtime
    binding keeps the request scoped to the exact staged snapshot so the
    writable lane can resume the same governed pipeline instead of restaging.
    """
    pipeline_ref = pipeline_target_ref(pipeline)
    return PacketPostRequest(
        from_agent="system",
        to_agent=to_agent,
        kind="action_request",
        summary=summary
        or f"Execute governed commit pipeline `{pipeline.pipeline_id}`",
        body=body
        or (
            "Run the existing approved governed commit from the writable "
            "implementer terminal lane."
        ),
        requested_action="commit",
        policy_hint="safe_auto_apply",
        approval_required=False,
        trace_id=pipeline.pipeline_id,
        expires_in_minutes=expires_in_minutes,
        target=PacketTargetFields.from_values(
            target_kind="runtime",
            target_ref=pipeline_ref,
            target_revision=pipeline.generation_id,
        ),
        runtime_approval=PacketRuntimeApprovalFields.from_values(
            pipeline_generation=pipeline.generation_id,
            staged_snapshot_hash=pipeline.intent.staged_tree_hash,
            guard_results_summary=guard_results_summary(pipeline.guard_result),
        ),
    )


def build_commit_approval_decision(
    pipeline: RemoteCommitPipelineContract,
    *,
    approval_packet_kind: str = "commit_approval",
    approved_by: str = "operator",
    requested_action: str = "approve_commit_pipeline",
    summary: str = "",
    body: str = "",
) -> PacketPostRequest:
    """Build the canonical operator decision packet for one pipeline."""
    return PacketPostRequest(
        from_agent=approved_by,
        to_agent="system",
        kind=approval_packet_kind,
        summary=summary or f"Approve governed commit pipeline `{pipeline.pipeline_id}`",
        body=body or "Operator approved the guarded staged snapshot.",
        requested_action=requested_action,
        policy_hint="operator_approval_required",
        approval_required=False,
        trace_id=pipeline.pipeline_id,
        target=PacketTargetFields.from_values(
            target_kind="runtime",
            target_ref=pipeline_target_ref(pipeline),
            target_revision=pipeline.generation_id,
        ),
        runtime_approval=PacketRuntimeApprovalFields.from_values(
            pipeline_generation=pipeline.generation_id,
            staged_snapshot_hash=pipeline.intent.staged_tree_hash,
            guard_results_summary=guard_results_summary(pipeline.guard_result),
        ),
    )


def latest_matching_packet(
    packets: Sequence[ReviewPacketState],
    pipeline: RemoteCommitPipelineContract,
    *,
    require_apply: bool,
    request_kind: str,
    approval_packet_kind: str = "commit_approval",
    allowed_target_revisions: Sequence[str] = (),
) -> ReviewPacketState | None:
    """Return the latest packet that matches one governed pipeline request kind."""
    matches: list[ReviewPacketState] = []
    target_revisions = {
        "",
        pipeline.generation_id,
        pipeline.intent.staged_tree_hash,
        *[revision for revision in allowed_target_revisions if revision],
    }
    for packet in packets:
        if packet.kind != approval_packet_kind:
            continue
        if packet.target_kind != "runtime":
            continue
        if packet.target_ref != pipeline_target_ref(pipeline):
            continue
        if packet.pipeline_generation != pipeline.generation_id:
            continue
        if packet.staged_snapshot_hash != pipeline.intent.staged_tree_hash:
            continue
        if packet.target_revision not in target_revisions:
            continue
        if request_kind == "request" and not packet.approval_required:
            continue
        if request_kind == "decision" and packet.requested_action not in {
            "approve_commit_pipeline",
            "reject_commit_pipeline",
        }:
            continue
        if request_kind == "override_decision" and packet.requested_action != "override_push":
            continue
        if require_apply and packet.status != "applied":
            continue
        matches.append(packet)
    if not matches:
        return None
    matches.sort(
        key=lambda packet: (
            packet.applied_at_utc or "",
            packet.posted_at or "",
            packet.latest_event_id or "",
        )
    )
    return matches[-1]


def approval_decision_packet(
    packets: Sequence[ReviewPacketState],
    pipeline: RemoteCommitPipelineContract,
    *,
    approval_packet_kind: str = "commit_approval",
) -> ReviewPacketState:
    """Return the applied approval decision packet or a minimal fallback row."""
    packet = latest_matching_packet(
        packets,
        pipeline,
        require_apply=True,
        request_kind="decision",
        approval_packet_kind=approval_packet_kind,
    )
    if packet is not None:
        return packet
    return ReviewPacketState(
        packet_id=pipeline.decision_packet_id,
        kind=approval_packet_kind,
        from_agent="operator",
        to_agent="system",
        summary="",
        body="",
        status="applied",
        policy_hint="operator_approval_required",
        requested_action="approve_commit_pipeline",
        approval_required=False,
        posted_at="",
        target_kind="runtime",
        target_ref=pipeline_target_ref(pipeline),
        target_revision=pipeline.generation_id,
        pipeline_generation=pipeline.generation_id,
        staged_snapshot_hash=pipeline.intent.staged_tree_hash,
        guard_results_summary=guard_results_summary(pipeline.guard_result),
        applied_at_utc="",
        expires_at_utc=pipeline.approval_expires_at_utc,
    )


def pipeline_target_ref(pipeline: RemoteCommitPipelineContract) -> str:
    """Return the runtime packet target ref for one governed pipeline."""
    return f"remote_commit_pipeline:{pipeline.pipeline_id}"


def guard_results_summary(result: ActionResult | None) -> str:
    """Return one compact JSON guard summary for approval packets."""
    if result is None:
        return ""
    payload = {
        "action_id": result.action_id,
        "status": result.status,
        "reason": result.reason,
    }
    return json.dumps(payload, sort_keys=True)
