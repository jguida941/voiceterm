"""Priority selection and control hints for live review packets."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone

from .pending_packets import live_pending_packets


def select_priority_pending_packet(
    packets: Sequence[object],
) -> tuple[dict[str, object] | None, dict[str, object]]:
    """Select the highest-priority live pending packet plus control metadata."""
    live_packets = [
        dict(packet)
        for packet in live_pending_packets(packets)
        if isinstance(packet, Mapping)
    ]
    if not live_packets:
        return None, {}
    action_requests = [
        packet for packet in live_packets if _is_action_request(packet)
    ]
    if action_requests:
        selected = min(action_requests, key=_action_request_priority_key)
        control_state = action_request_control_state(selected)
        return selected, {
            "selection_policy": "action_request_priority",
            "packet_class": "action_request",
            "control_state": control_state,
            "wake_required": control_state == "execution_pending",
            "delivery_required": control_state == "delivery_pending",
            "requested_action": str(selected.get("requested_action") or "").strip(),
            "delivery_observed_at_utc": str(
                selected.get("delivery_observed_at_utc") or ""
            ).strip(),
            "delivery_observed_by": str(
                selected.get("delivery_observed_by") or ""
            ).strip(),
            "execution_started_at_utc": str(
                selected.get("execution_started_at_utc") or ""
            ).strip(),
            "execution_started_by": str(
                selected.get("execution_started_by") or ""
            ).strip(),
        }
    selected = live_packets[0]
    return selected, {
        "selection_policy": "fifo_live_pending",
        "packet_class": str(selected.get("kind") or "packet").strip() or "packet",
        "control_state": "",
        "wake_required": False,
        "delivery_required": False,
    }


def action_request_control_state(packet: Mapping[str, object]) -> str:
    """Classify the current live control posture of one action_request packet."""
    execution_started_at_utc = str(
        packet.get("execution_started_at_utc") or ""
    ).strip()
    if execution_started_at_utc:
        return "in_progress"
    delivery_observed_at_utc = str(
        packet.get("delivery_observed_at_utc") or ""
    ).strip()
    if delivery_observed_at_utc:
        return "execution_pending"
    return "delivery_pending"


def format_priority_instruction(
    summary: str,
    *,
    selection_policy: str,
) -> str:
    """Render the human-facing queue instruction with priority framing."""
    text = summary.strip()
    if not text:
        return ""
    if selection_policy == "action_request_priority":
        return f"Priority action_request: {text}"
    return text


def _action_request_priority_key(packet: Mapping[str, object]) -> tuple[object, ...]:
    state_rank = {
        "execution_pending": 0,
        "delivery_pending": 1,
        "in_progress": 2,
    }
    return (
        state_rank.get(action_request_control_state(packet), 9),
        _parse_utc(packet.get("expires_at_utc")),
        _parse_utc(packet.get("posted_at")),
        str(packet.get("packet_id") or "").strip(),
    )


def _is_action_request(packet: Mapping[str, object]) -> bool:
    return str(packet.get("kind") or "").strip() == "action_request"


def _parse_utc(value: object) -> datetime:
    text = str(value or "").strip()
    if not text:
        return datetime.max.replace(tzinfo=timezone.utc)
    try:
        observed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return datetime.max.replace(tzinfo=timezone.utc)
    if observed.tzinfo is None:
        return observed.replace(tzinfo=timezone.utc)
    return observed.astimezone(timezone.utc)
