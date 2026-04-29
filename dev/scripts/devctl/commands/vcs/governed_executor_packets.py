"""Typed packet helpers for the governed VCS executor."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass

from ...review_channel.packet_contract import (
    PacketGuardBundleEvidenceFields,
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


@dataclass(frozen=True, slots=True)
class CommitStageRequestFields:
    to_agent: str
    head_sha: str
    commit_message_draft: str
    stage_reason: str
    stage_warnings: Sequence[str] = ()
    expires_in_minutes: int = 30
    full_guard_bundle_evidence: str = "--profile ci"


def build_commit_stage_request(fields: CommitStageRequestFields) -> PacketPostRequest:
    """Build a typed handoff when sandbox policy blocks pipeline staging."""
    target_revision = str(fields.head_sha or "").strip()
    warning_summary = "\n".join(
        f"- {warning}" for warning in fields.stage_warnings if str(warning).strip()
    )
    body = (
        "The current lane could not create `.git/index.lock` while preparing "
        "the governed commit pipeline. Run the same governed commit from the "
        "remote-control lane with repo-approved filesystem access, then let "
        "the pipeline emit the normal guard, approval, commit, and push "
        "receipts."
    )
    if fields.commit_message_draft:
        body += f"\n\nCommit message draft: `{fields.commit_message_draft}`"
    if fields.stage_reason:
        body += f"\n\nStage block reason: `{fields.stage_reason}`"
    if warning_summary:
        body += f"\n\nWarnings:\n{warning_summary}"
    return PacketPostRequest(
        from_agent="system",
        to_agent=fields.to_agent,
        kind="action_request",
        summary="Run governed commit staging from remote-control lane",
        body=body,
        requested_action="stage_commit_pipeline",
        policy_hint="safe_auto_apply",
        approval_required=False,
        trace_id=f"devctl_commit:{target_revision}",
        expires_in_minutes=fields.expires_in_minutes,
        target=PacketTargetFields.from_values(
            target_kind="runtime",
            target_ref=commit_stage_target_ref(fields.head_sha),
            target_revision=target_revision,
        ),
        guard_bundle_evidence=PacketGuardBundleEvidenceFields.from_values(
            full_guard_bundle_evidence=fields.full_guard_bundle_evidence,
        ),
    )


def matching_commit_stage_request_packet(
    packets: Sequence[ReviewPacketState],
    *,
    to_agent: str,
    head_sha: str,
) -> ReviewPacketState | None:
    """Return an existing live stage handoff for the same agent and HEAD."""
    target_ref = commit_stage_target_ref(head_sha)
    target_revision = str(head_sha or "").strip()
    matches: list[ReviewPacketState] = []
    for packet in packets:
        if _packet_field(packet, "kind") != "action_request":
            continue
        if _packet_field(packet, "from_agent") != "system":
            continue
        if _packet_field(packet, "to_agent") != str(to_agent or "").strip():
            continue
        if _packet_field(packet, "requested_action") != "stage_commit_pipeline":
            continue
        if _packet_field(packet, "policy_hint") != "safe_auto_apply":
            continue
        if _packet_field(packet, "target_ref") != target_ref:
            continue
        if _packet_field(packet, "target_revision") != target_revision:
            continue
        if _packet_field(packet, "status") not in {"pending", "acked"}:
            continue
        matches.append(packet)
    if not matches:
        return None
    matches.sort(
        key=lambda packet: (
            _packet_field(packet, "applied_at_utc"),
            _packet_field(packet, "acked_at_utc"),
            _packet_field(packet, "posted_at"),
            _packet_field(packet, "latest_event_id"),
            _packet_field(packet, "packet_id"),
        )
    )
    return matches[-1]


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
        if (
            request_kind in {"decision", "override_decision"}
            and packet.approval_required
        ):
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


def _packet_field(packet: object, field: str) -> str:
    if isinstance(packet, dict):
        return str(packet.get(field) or "").strip()
    return str(getattr(packet, field, "") or "").strip()


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


def commit_stage_target_ref(head_sha: str) -> str:
    """Return the runtime packet target ref for pre-pipeline commit staging."""
    return f"devctl_commit:{str(head_sha or '').strip()}"


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
