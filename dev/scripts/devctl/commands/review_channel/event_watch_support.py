"""Watch/inbox packet helpers for event-backed review-channel actions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...review_channel.action_request_delivery import (
    mark_action_request_packets_observed,
)
from ...review_channel.events import filter_inbox_packets, refresh_event_bundle


@dataclass(frozen=True)
class EventWatchContext:
    args: object
    bundle: object
    repo_root: Path
    review_channel_path: Path
    artifact_paths: object

    @classmethod
    def from_legacy(
        cls,
        *,
        args: object,
        bundle: object,
        repo_root: Path,
        review_channel_path: Path,
        artifact_paths: object,
    ) -> "EventWatchContext":
        return cls(
            args=args,
            bundle=bundle,
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        )


def load_target_packets(
    *,
    context: EventWatchContext,
    status_filter: str | None = None,
    target_override: str | None = None,
    observe_action_requests: bool = True,
) -> tuple[object, list[dict[str, object]]]:
    """Load target-filtered packets and refresh after action-request observation."""
    effective_status_filter = (
        status_filter
        if status_filter is not None
        else getattr(context.args, "status", None)
    )
    effective_target = (
        target_override
        if target_override is not None
        else getattr(context.args, "target", None)
    )
    packets = filter_inbox_packets(
        context.bundle.review_state,
        target=effective_target,
        status=effective_status_filter,
        limit=context.args.limit,
    )
    if _mark_targeted_action_request_observation(
        target=effective_target,
        artifact_paths=context.artifact_paths,
        packets=packets,
        status_filter=effective_status_filter,
        observe_action_requests=observe_action_requests,
    ):
        refreshed_bundle = refresh_event_bundle(
            repo_root=context.repo_root,
            review_channel_path=context.review_channel_path,
            artifact_paths=context.artifact_paths,
        )
        packets = filter_inbox_packets(
            refreshed_bundle.review_state,
            target=effective_target,
            status=effective_status_filter,
            limit=context.args.limit,
        )
        return refreshed_bundle, packets
    return context.bundle, packets


def watch_snapshot_signature(
    *,
    packets: list[dict[str, object]],
    review_state: object,
    target: str | None = None,
) -> tuple[frozenset[object], int, str]:
    """Return the watch-stream signature for live and stale queue state."""
    queue = {}
    packet_inbox = {}
    if isinstance(review_state, dict):
        queue = review_state.get("queue", {})
        packet_inbox = review_state.get("packet_inbox", {})
    stale_packet_count = 0
    if isinstance(queue, dict):
        stale_packet_count = int(queue.get("stale_packet_count", 0) or 0)
    packet_ids = frozenset(
        packet.get("packet_id")
        for packet in packets
        if isinstance(packet, dict)
    )
    return (
        packet_ids,
        stale_packet_count,
        _target_attention_revision(packet_inbox, target=target),
    )


def _target_attention_revision(packet_inbox: object, *, target: str | None) -> str:
    if not isinstance(packet_inbox, dict):
        return ""
    normalized_target = str(target or "").strip().lower()
    agents = packet_inbox.get("agents", ())
    if isinstance(agents, list):
        for record in agents:
            if not isinstance(record, dict):
                continue
            if str(record.get("agent") or "").strip().lower() != normalized_target:
                continue
            return str(record.get("attention_revision") or "").strip()
    return str(packet_inbox.get("attention_revision") or "").strip()


def _mark_targeted_action_request_observation(
    *,
    target: str | None,
    artifact_paths,
    packets: list[dict[str, object]],
    status_filter: str | None,
    observe_action_requests: bool,
) -> bool:
    if not observe_action_requests:
        return False
    target = str(target or "").strip()
    if not target:
        return False
    if status_filter not in {None, "", "pending"}:
        return False
    return mark_action_request_packets_observed(
        artifact_root=Path(artifact_paths.artifact_root),
        packets=packets,
        observer=target,
    )
