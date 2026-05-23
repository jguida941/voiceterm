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
        target_role=_target_role(context.args),
        target_session_id=_target_session_id(context.args),
        status=effective_status_filter,
        limit=context.args.limit,
        include_stale=bool(getattr(context.args, "include_stale", False)),
    )
    if _mark_targeted_action_request_observation(
        args=context.args,
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
            target_role=_target_role(context.args),
            target_session_id=_target_session_id(context.args),
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
) -> tuple[object, ...]:
    """Return the watch-stream signature for live and stale queue state."""
    queue = {}
    packet_inbox = {}
    current_session = {}
    bridge = {}
    if isinstance(review_state, dict):
        queue = review_state.get("queue", {})
        packet_inbox = review_state.get("packet_inbox", {})
        current_session = review_state.get("current_session", {})
        bridge = review_state.get("bridge", {})
    stale_packet_count = 0
    if isinstance(queue, dict):
        stale_packet_count = int(queue.get("stale_packet_count", 0) or 0)
    packet_transitions = tuple(
        sorted(
            _packet_transition_signature(packet)
            for packet in packets
            if isinstance(packet, dict)
        )
    )
    return (
        packet_transitions,
        stale_packet_count,
        _target_attention_revision(packet_inbox, target=target),
        _queue_instruction_signature(queue),
        _current_session_signature(current_session),
        _bridge_instruction_signature(bridge),
    )


def _packet_transition_signature(packet: dict[str, object]) -> tuple[str, ...]:
    return tuple(
        str(packet.get(key) or "").strip()
        for key in (
            "packet_id",
            "latest_event_id",
            "status",
            "delivery_observed_at_utc",
            "delivery_observed_by",
            "body_observed_at_utc",
            "body_observed_by",
            "body_observed_role",
            "body_observed_session_id",
            "body_observed_event_id",
            "body_digest",
            "acked_at_utc",
            "acked_by",
            "applied_at_utc",
            "execution_started_at_utc",
            "execution_started_by",
        )
    )


def _queue_instruction_signature(queue: object) -> tuple[str, ...]:
    if not isinstance(queue, dict):
        return ("", "", "")
    source = queue.get("derived_next_instruction_source", {})
    if not isinstance(source, dict):
        source = {}
    return (
        str(queue.get("derived_next_instruction") or "").strip(),
        str(source.get("packet_id") or "").strip(),
        str(source.get("control_state") or "").strip(),
    )


def _current_session_signature(current_session: object) -> tuple[str, ...]:
    if not isinstance(current_session, dict):
        return ("", "", "", "")
    return tuple(
        str(current_session.get(key) or "").strip()
        for key in (
            "current_instruction_revision",
            "implementer_ack_revision",
            "implementer_ack_state",
            "implementer_status",
        )
    )


def _bridge_instruction_signature(bridge: object) -> tuple[str, ...]:
    if not isinstance(bridge, dict):
        return ("", "", "", "")
    return tuple(
        str(bridge.get(key) or "").strip()
        for key in (
            "current_instruction_revision",
            "implementer_ack_revision",
            "implementer_ack_state",
            "reviewer_mode",
        )
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
    args: object,
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
    observer = _action_request_observer(args=args, target=target)
    if not observer:
        return False
    if status_filter not in {None, "", "pending"}:
        return False
    return mark_action_request_packets_observed(
        artifact_root=Path(artifact_paths.artifact_root),
        packets=packets,
        observer=observer,
    )


def _action_request_observer(*, args: object, target: str) -> str:
    """Return the agent allowed to stamp delivery for this targeted read."""
    actor = str(getattr(args, "actor", "") or "").strip()
    if not actor:
        return ""
    if actor.lower() != target.lower():
        return ""
    return actor


def _target_role(args: object) -> str:
    return str(getattr(args, "target_role", "") or "").strip()


def _target_session_id(args: object) -> str:
    return str(getattr(args, "target_session_id", "") or "").strip()
