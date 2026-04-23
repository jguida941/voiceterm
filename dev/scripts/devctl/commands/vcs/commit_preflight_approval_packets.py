"""Typed approval packet helpers for governed commit preflight."""

from __future__ import annotations

from ...review_channel.events import post_packet, resolve_artifact_paths, transition_packet
from ...review_channel.packet_contract import PacketTransitionRequest
from .governed_executor import GovernedVcsExecutor
from .governed_executor_actions import APPROVAL_PACKET_KIND
from .governed_executor_packets import (
    build_commit_approval_decision,
    build_commit_approval_request,
)
from .governed_executor_sync import sync_pipeline_approval


def ensure_approval_request(
    executor: GovernedVcsExecutor,
    pipeline,
    *,
    to_agent: str = "operator",
) -> str:
    """Post the typed approval request once per governed pipeline."""
    synced = sync_pipeline_approval(
        pipeline,
        executor._event_packets(),
        approval_packet_kind=APPROVAL_PACKET_KIND,
    )
    if synced.approval_packet_id or synced.approval_state == "approved":
        executor._persist_pipeline(synced)
        return synced.approval_packet_id
    artifact_paths = resolve_artifact_paths(repo_root=executor.repo_root)
    _, event = post_packet(
        repo_root=executor.repo_root,
        review_channel_path=executor.review_channel_path,
        artifact_paths=artifact_paths,
        request=build_commit_approval_request(
            pipeline,
            to_agent=to_agent,
        ),
    )
    return str(event.get("packet_id") or "").strip()


def apply_local_approval(
    executor: GovernedVcsExecutor,
    pipeline,
    *,
    approval_actor: str = "operator",
    authority_reason: str = "",
) -> None:
    """Record request + applied approval for trusted local or delegated modes."""
    summary = f"Local terminal approval for `{pipeline.pipeline_id}`"
    body = (
        "The local terminal operator approved the guarded staged "
        "snapshot for governed commit execution."
    )
    if authority_reason == "remote_control_operator_delegate":
        actor_label = str(approval_actor or "operator").strip()
        summary = f"Remote-control delegated approval for `{pipeline.pipeline_id}`"
        body = (
            "The active remote-control operator delegate "
            f"`{actor_label}` approved the guarded staged snapshot for "
            "governed commit execution."
        )
    record_operator_approval(
        executor,
        pipeline,
        summary=summary,
        body=body,
        approval_actor=approval_actor,
    )


def record_operator_approval(
    executor: GovernedVcsExecutor,
    pipeline,
    *,
    summary: str,
    body: str,
    approval_actor: str = "operator",
) -> None:
    """Post and apply one typed operator approval for the current pipeline."""
    artifact_paths = resolve_artifact_paths(repo_root=executor.repo_root)
    actor = str(approval_actor or "operator").strip() or "operator"
    request_packet_id = ensure_approval_request(
        executor,
        pipeline,
        to_agent=actor,
    )
    if request_packet_id:
        try:
            transition_packet(
                repo_root=executor.repo_root,
                review_channel_path=executor.review_channel_path,
                artifact_paths=artifact_paths,
                request=PacketTransitionRequest(
                    action="apply",
                    packet_id=request_packet_id,
                    actor=actor,
                ),
            )
        except ValueError:
            pass
    _, decision_event = post_packet(
        repo_root=executor.repo_root,
        review_channel_path=executor.review_channel_path,
        artifact_paths=artifact_paths,
        request=build_commit_approval_decision(
            pipeline,
            approved_by=actor,
            summary=summary,
            body=body,
        ),
    )
    transition_packet(
        repo_root=executor.repo_root,
        review_channel_path=executor.review_channel_path,
        artifact_paths=artifact_paths,
        request=PacketTransitionRequest(
            action="apply",
            packet_id=str(decision_event.get("packet_id") or ""),
            actor="operator",
        ),
    )
