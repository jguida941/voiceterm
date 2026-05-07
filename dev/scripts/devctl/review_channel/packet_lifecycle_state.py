"""Packet lifecycle current-state reducer."""

from __future__ import annotations

from collections.abc import Mapping

from .packet_lifecycle_binding import plan_ingestion_payload, plan_integration_recorded


def current_state(
    packet: Mapping[str, object],
    *,
    acknowledged_events: list[dict[str, object]],
    acted_on_events: list[dict[str, object]],
) -> str:
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
    if _text(packet.get("kind")) == "action_request":
        return action_request_current_state(
            packet,
            acknowledged_events=acknowledged_events,
        )
    if acknowledged_events:
        return "acknowledged"
    return _text(packet.get("status")) or "pending"


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


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["action_request_current_state", "current_state"]
