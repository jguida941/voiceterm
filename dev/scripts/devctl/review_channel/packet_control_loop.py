"""Priority selection and control hints for live review packets."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ..runtime.review_packet_inbox_liveness import (
    is_failed_action_request,
    is_live_control_packet,
)
from .packet_control_loop_action_request import (
    action_request_control_state,
    action_request_priority_key,
)


def select_priority_pending_packet(
    packets: Sequence[object],
) -> tuple[dict[str, object] | None, dict[str, object]]:
    """Select the highest-priority live packet plus control metadata.

    Pending packets are the normal actionable queue. Acknowledged action
    requests with execution-start evidence are still active control state until
    they are applied/dismissed; dropping them here erases the typed instruction
    revision while a peer is actively executing the request.
    """
    live_packets = _live_control_packets(packets)
    if not live_packets:
        return None, {}
    action_requests = [
        packet for packet in live_packets if _is_action_request(packet)
    ]
    if action_requests:
        selected = min(action_requests, key=action_request_priority_key)
        control_state = action_request_control_state(selected)
        return selected, {
            "selection_policy": "action_request_priority",
            "packet_class": "action_request",
            "control_state": control_state,
            "wake_required": control_state
            in {"execution_pending", "apply_pending_after_execution"},
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
            "execution_failed_at_utc": str(
                selected.get("execution_failed_at_utc") or ""
            ).strip(),
            "execution_failed_reason": str(
                selected.get("execution_failed_reason") or ""
            ).strip(),
            "apply_pending_after_execution_at_utc": str(
                selected.get("apply_pending_after_execution_at_utc") or ""
            ).strip(),
            "apply_pending_after_execution_reason": str(
                selected.get("apply_pending_after_execution_reason") or ""
            ).strip(),
        }
    instruction_packets = [
        packet for packet in live_packets if _is_instruction_like_packet(packet)
    ]
    if not instruction_packets:
        return None, {}
    selected = instruction_packets[0]
    return selected, {
        "selection_policy": "instruction_like_fifo",
        "packet_class": str(selected.get("kind") or "packet").strip() or "packet",
        "control_state": "",
        "wake_required": False,
        "delivery_required": False,
    }


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


def _live_control_packets(packets: Sequence[object]) -> list[dict[str, object]]:
    """Return packets that should still drive the current instruction."""
    selected: list[dict[str, object]] = []
    seen: set[str] = set()
    for packet in packets:
        if isinstance(packet, Mapping) and is_live_control_packet(packet):
            _append_packet(selected, seen, packet)
    return selected


def latest_failed_action_request(
    packets: Sequence[object],
) -> dict[str, object] | None:
    """Return the newest failed action_request for status-only rendering."""
    failed = [
        dict(packet)
        for packet in packets
        if isinstance(packet, Mapping) and is_failed_action_request(packet)
    ]
    if not failed:
        return None
    failed.sort(
        key=lambda packet: (
            str(packet.get("execution_failed_at_utc") or "").strip(),
            str(packet.get("packet_id") or "").strip(),
        )
    )
    return failed[-1]


def _append_packet(
    selected: list[dict[str, object]],
    seen: set[str],
    packet: Mapping[str, object],
) -> None:
    packet_id = str(packet.get("packet_id") or "").strip()
    if packet_id and packet_id in seen:
        return
    selected.append(dict(packet))
    if packet_id:
        seen.add(packet_id)


def _is_action_request(packet: Mapping[str, object]) -> bool:
    return str(packet.get("kind") or "").strip() == "action_request"


def _is_instruction_like_packet(packet: Mapping[str, object]) -> bool:
    if _is_action_request(packet):
        return True
    return str(packet.get("kind") or "").strip() == "instruction"
