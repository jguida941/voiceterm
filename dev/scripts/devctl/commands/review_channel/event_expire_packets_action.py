"""Expire-packets action for the event-backed review-channel command."""

from __future__ import annotations

from ...review_channel.packet_expiry_materialization import (
    materialize_expired_packet_events,
)
from .event_action_support import EventActionContext


def run_expire_packets_action(
    *,
    context: EventActionContext,
) -> tuple[dict, int]:
    """Materialize bounded ``packet_expired`` events and report affected rows."""
    limit = getattr(context.args, "limit", None)
    bundle, materialization = materialize_expired_packet_events(
        repo_root=context.repo_root,
        review_channel_path=context.review_channel_path,
        artifact_paths=context.artifact_paths,
        limit=limit if isinstance(limit, int) and limit > 0 else None,
    )
    expired_packet_ids = set(materialization.packet_ids)
    packets = [
        packet
        for packet in bundle.review_state.get("packets", [])
        if isinstance(packet, dict)
        and str(packet.get("packet_id") or "").strip() in expired_packet_ids
    ]
    return context.build_event_report_fn(
        args=context.args,
        bundle=bundle,
        packets=packets,
        packet_expiry_materialization=materialization.to_dict(),
    )

