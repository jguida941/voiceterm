"""Side-effect orchestration for event-backed review-channel actions."""

from __future__ import annotations

from pathlib import Path

from ...review_channel.bridge_projection import render_bridge_projection
from ...review_channel.heartbeat import compute_non_audit_worktree_hash
from .event_action_support import EventActionContext
from .event_implementer_ack_action import run_implementer_ack_action
from .event_post_action import run_post_action
from .event_post_bridge_sync import (
    sync_bridge_after_implementer_ack,
    sync_bridge_after_posted_current_instruction,
)
from .event_post_wake import maybe_wake_posted_reviewer_packet


def run_post_action_with_side_effects(
    *,
    context: EventActionContext,
    args,
    repo_root: Path,
    paths: dict[str, object],
) -> tuple[dict, int, dict[str, object]]:
    report, exit_code, review_state_payload = run_post_action(context=context)
    _attach_post_side_effects(
        report=report,
        args=args,
        repo_root=repo_root,
        paths=paths,
        review_state_payload=review_state_payload,
    )
    return report, exit_code, review_state_payload


def run_implementer_ack_with_bridge_sync(
    *,
    context: EventActionContext,
    repo_root: Path,
    paths: dict[str, object],
) -> tuple[dict, int]:
    report, exit_code, review_state_payload = run_implementer_ack_action(
        context=context
    )
    event = report.get("event")
    if isinstance(event, dict):
        bridge_sync = sync_bridge_after_implementer_ack(
            repo_root=repo_root,
            paths=paths,
            event=event,
            review_state_payload=review_state_payload,
            compute_worktree_hash_fn=compute_non_audit_worktree_hash,
            render_bridge_projection_fn=render_bridge_projection,
        )
        if bridge_sync is not None:
            report["implementer_ack_bridge_sync"] = bridge_sync
    return report, exit_code


def _attach_post_side_effects(
    *,
    report: dict,
    args,
    repo_root: Path,
    paths: dict[str, object],
    review_state_payload: dict[str, object],
) -> None:
    packet = report.get("packet")
    if not isinstance(packet, dict):
        return
    bridge_sync = sync_bridge_after_posted_current_instruction(
        repo_root=repo_root,
        paths=paths,
        packet=packet,
        review_state_payload=review_state_payload,
        compute_worktree_hash_fn=compute_non_audit_worktree_hash,
        render_bridge_projection_fn=render_bridge_projection,
    )
    if bridge_sync is not None:
        report["post_bridge_sync"] = bridge_sync
    reviewer_wake = maybe_wake_posted_reviewer_packet(
        args=args,
        repo_root=repo_root,
        paths=paths,
        packet=packet,
        posted_review_state_payload=review_state_payload,
    )
    if reviewer_wake is not None:
        report["packet_attention"] = reviewer_wake
        report["reviewer_wake"] = reviewer_wake
