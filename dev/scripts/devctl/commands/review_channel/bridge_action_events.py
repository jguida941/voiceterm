"""Lifecycle-event helpers for bridge-backed review-channel actions."""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ...review_channel.event_store import ReviewChannelArtifactPaths, event_state_exists
from ...review_channel.events import post_packet
from ...review_channel.packet_contract import PacketPostRequest


@dataclass(frozen=True)
class BridgeLifecycleEventContext:
    repo_root: Path
    review_channel_path: Path
    artifact_paths: ReviewChannelArtifactPaths | None
    sessions: list[dict[str, object]]


def post_session_lifecycle_event(
    *,
    action: str,
    context: BridgeLifecycleEventContext,
    post_packet_fn: Callable[..., object] | None = None,
    event_state_exists_fn: Callable[[ReviewChannelArtifactPaths], bool] | None = None,
) -> None:
    """Post a bridge launch/rollover notice into the review-channel event store."""
    if post_packet_fn is None:
        post_packet_fn = post_packet
    if event_state_exists_fn is None:
        event_state_exists_fn = event_state_exists
    if context.artifact_paths is None or not event_state_exists_fn(context.artifact_paths):
        return

    provider_names = [
        str(session.get("provider", "")).capitalize() for session in context.sessions
    ]
    label = "rollover" if action == "rollover" else "launch"
    summary = f"Session {label}: {', '.join(provider_names)} conductors started"
    lane_counts = [
        (
            f"{session.get('provider', '?')}: "
            f"{session.get('planned_lane_count', 0)} planned lanes"
        )
        for session in context.sessions
    ]
    worker_budgets = [
        (
            f"{session.get('provider', '?')}: "
            f"{session.get('requested_worker_budget', 0)} requested fanout"
        )
        for session in context.sessions
    ]
    body = (
        f"The operator {label}ed {len(context.sessions)} conductor session(s). "
        f"Planned topology: {'; '.join(lane_counts)}. "
        f"Requested fanout budget: {'; '.join(worker_budgets)}."
    )
    with contextlib.suppress(OSError, ValueError):
        post_packet_fn(
            repo_root=context.repo_root,
            review_channel_path=context.review_channel_path,
            artifact_paths=context.artifact_paths,
            request=PacketPostRequest(
                from_agent="system",
                to_agent="operator",
                kind="system_notice",
                summary=summary,
                body=body,
                evidence_refs=(),
                context_pack_refs=(),
                confidence=1.0,
                requested_action="review_only",
                policy_hint="review_only",
                approval_required=False,
                expires_in_minutes=60,
            ),
        )
