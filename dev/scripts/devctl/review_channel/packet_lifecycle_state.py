"""Packet lifecycle current-state reducer."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.collaboration_packet_kinds import (
    COLLABORATION_LIFECYCLE_PACKET_KINDS,
    GOAL_PROGRESS_PACKET_KIND,
    OPERATOR_ROUTED_PACKET_KIND,
    PEER_HEARTBEAT_PACKET_KIND,
    PEER_OFFLINE_PACKET_KIND,
    PEER_SESSION_HANDSHAKE_PACKET_KIND,
    REVIEW_ACCEPTED_PACKET_KIND,
    REVIEW_FAILED_PACKET_KIND,
    REVIEW_STARTED_PACKET_KIND,
    SESSION_RESYNC_PACKET_KIND,
    TASK_BLOCKED_PACKET_KIND,
    TASK_PRODUCED_PACKET_KIND,
    TASK_PROGRESS_PACKET_KIND,
    TASK_STARTED_PACKET_KIND,
)
from .packet_lifecycle_binding import plan_ingestion_payload, plan_integration_recorded

WORKFLOW_LIFECYCLE_STATE_BY_KIND = {
    TASK_STARTED_PACKET_KIND: "task_started",
    TASK_PROGRESS_PACKET_KIND: "task_progress",
    TASK_PRODUCED_PACKET_KIND: "task_produced",
    TASK_BLOCKED_PACKET_KIND: "task_blocked",
    GOAL_PROGRESS_PACKET_KIND: "goal_progress",
    REVIEW_STARTED_PACKET_KIND: "review_in_progress",
    REVIEW_FAILED_PACKET_KIND: "review_failed",
    REVIEW_ACCEPTED_PACKET_KIND: "review_accepted",
    OPERATOR_ROUTED_PACKET_KIND: "operator_routed",
    PEER_SESSION_HANDSHAKE_PACKET_KIND: "peer_session_handshake",
    SESSION_RESYNC_PACKET_KIND: "session_resync",
    PEER_HEARTBEAT_PACKET_KIND: "peer_heartbeat",
    PEER_OFFLINE_PACKET_KIND: "peer_offline",
}


def current_state(
    packet: Mapping[str, object],
    *,
    acknowledged_events: list[dict[str, object]],
    acted_on_events: list[dict[str, object]],
) -> str:
    kind = _text(packet.get("kind"))
    if kind in COLLABORATION_LIFECYCLE_PACKET_KINDS:
        return collaboration_lifecycle_current_state(
            packet,
            kind=kind,
            acted_on_events=acted_on_events,
        )
    if acted_on_events:
        action = _text(acted_on_events[-1].get("action"))
        if (
            action == "applied"
            and _text(packet.get("target_kind")) == "plan"
            and not plan_integration_recorded(plan_ingestion_payload(packet))
        ):
            return "plan_ingestion_failed"
        if action == "archived":
            return "archived"
        return action or _text(packet.get("status")) or "acted_on"
    if _text(packet.get("status")) == "expired":
        return "archived"
    if kind == "action_request":
        return action_request_current_state(
            packet,
            acknowledged_events=acknowledged_events,
        )
    if acknowledged_events:
        return "acknowledged"
    return _text(packet.get("status")) or "pending"


def collaboration_lifecycle_current_state(
    packet: Mapping[str, object],
    *,
    kind: str,
    acted_on_events: list[dict[str, object]],
) -> str:
    action = _text(acted_on_events[-1].get("action")) if acted_on_events else ""
    if action in {"archived", "dismissed"}:
        return action
    if _text(packet.get("status")) == "expired":
        return "archived"
    if kind == REVIEW_ACCEPTED_PACKET_KIND:
        if not _has_review_started_evidence(packet):
            return "review_accepted_missing_review_started"
        if action == "applied":
            return "task_complete"
        return "review_accepted"
    fallback = action or _text(packet.get("status")) or "pending"
    return WORKFLOW_LIFECYCLE_STATE_BY_KIND.get(kind, fallback)


def action_request_current_state(
    packet: Mapping[str, object],
    *,
    acknowledged_events: list[dict[str, object]],
) -> str:
    if _text(packet.get("apply_pending_after_execution_at_utc")):
        return "apply_pending_after_execution"
    if _text(packet.get("execution_failed_at_utc")):
        return "failed"
    if _text(packet.get("applied_at_utc")) or _text(packet.get("status")) == "applied":
        return "applied"
    if _text(packet.get("execution_started_at_utc")):
        return "in_progress"
    if _text(packet.get("acked_at_utc")) or acknowledged_events:
        return "acknowledged"
    if _text(packet.get("delivery_observed_at_utc")):
        return "execution_pending"
    return "delivery_pending"


def _has_review_started_evidence(packet: Mapping[str, object]) -> bool:
    refs = (
        *_rows(packet.get("evidence_refs")),
        *_rows(packet.get("guidance_refs")),
        *_rows(packet.get("anchor_refs")),
    )
    return any(
        "review_started" in ref or "review_in_progress" in ref
        for ref in refs
    )


def _rows(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(
        str(item or "").strip()
        for item in value
        if str(item or "").strip()
    )


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "WORKFLOW_LIFECYCLE_STATE_BY_KIND",
    "action_request_current_state",
    "collaboration_lifecycle_current_state",
    "current_state",
]
