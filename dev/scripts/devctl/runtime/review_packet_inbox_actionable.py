"""Actionable-packet ordering helpers for the typed packet inbox."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .review_packet_inbox_lookup import packet_id as _packet_id, _parse_utc
from .session_termination_policy import SESSION_TERMINATION_PACKET_KINDS


def ordered_actionable_packets(
    packets: Sequence[Mapping[str, object]],
) -> tuple[Mapping[str, object], ...]:
    """Return actionable packets in delivery/execution priority order."""
    action_requests = [packet for packet in packets if is_action_request(packet)]
    instructions = [packet for packet in packets if _packet_kind(packet) == "instruction"]
    attention_packets = [
        packet
        for packet in packets
        if attention_urgency(packet) in {"urgent", "blocking"}
        and not is_action_request(packet)
        and _packet_kind(packet) != "instruction"
    ]
    return (
        *sorted(action_requests, key=_action_request_priority_key),
        *sorted(instructions, key=_latest_sort_key, reverse=True),
        *sorted(attention_packets, key=_attention_priority_key),
    )


def select_actionable_packet(
    packets: Sequence[Mapping[str, object]],
) -> Mapping[str, object] | None:
    """Return the highest-priority actionable packet when one exists."""
    ordered = ordered_actionable_packets(packets)
    return ordered[0] if ordered else None


def is_action_request(packet: Mapping[str, object]) -> bool:
    """Return True when one packet is an action request."""
    return _packet_kind(packet) == "action_request"


def is_actionable(packet: Mapping[str, object]) -> bool:
    """Return True when one packet can drive the current instruction lane."""
    if _packet_is_communication_only(packet):
        return False
    if _packet_kind(packet) in SESSION_TERMINATION_PACKET_KINDS:
        return False
    return (
        is_action_request(packet)
        or _packet_kind(packet) == "instruction"
        or attention_urgency(packet) in {"urgent", "blocking"}
    )


def attention_urgency(packet: Mapping[str, object]) -> str:
    explicit = _normalized_text(packet.get("attention_urgency")).lower()
    if explicit in {"ambient", "urgent", "blocking"}:
        return explicit
    legacy = _normalized_text(packet.get("urgency")).lower()
    if legacy in {"ambient", "urgent", "blocking"}:
        return legacy
    return "ambient"


def _action_request_priority_key(packet: Mapping[str, object]) -> tuple[object, ...]:
    """Mirror review-channel active-packet priority for inbox instruction focus."""
    state_rank = {
        "apply_pending_after_execution": 0,
        "execution_pending": 1,
        "delivery_pending": 2,
        "in_progress": 3,
        "failed": 4,
    }
    return (
        state_rank.get(_action_request_state(packet), 9),
        -_event_id_rank(str(packet.get("latest_event_id") or "")),
        _parse_utc(packet.get("expires_at_utc")),
        _parse_utc(packet.get("posted_at")),
        _packet_id(packet),
    )


def _latest_sort_key(packet: Mapping[str, object]) -> tuple[object, ...]:
    return (
        _parse_utc(packet.get("posted_at")),
        _packet_id(packet),
    )


def _attention_priority_key(packet: Mapping[str, object]) -> tuple[object, ...]:
    urgency_rank = {"blocking": 0, "urgent": 1, "ambient": 2}
    return (
        urgency_rank.get(attention_urgency(packet), 9),
        -_event_id_rank(str(packet.get("latest_event_id") or "")),
        _parse_utc(packet.get("posted_at")),
        _packet_id(packet),
    )


def _action_request_state(packet: Mapping[str, object]) -> str:
    if str(packet.get("apply_pending_after_execution_at_utc") or "").strip():
        return "apply_pending_after_execution"
    if str(packet.get("execution_failed_at_utc") or "").strip():
        return "failed"
    if str(packet.get("execution_started_at_utc") or "").strip():
        return "in_progress"
    if str(packet.get("delivery_observed_at_utc") or "").strip():
        return "execution_pending"
    return "delivery_pending"


def _packet_kind(packet: Mapping[str, object]) -> str:
    return _normalized_text(packet.get("kind"))


def _packet_is_communication_only(packet: Mapping[str, object]) -> bool:
    for key in ("durable_binding", "packet_creation_binding"):
        binding = packet.get(key)
        if not isinstance(binding, Mapping):
            continue
        if _normalized_text(binding.get("binding_target_kind")) == "communication_only":
            return True
    return False


def _event_id_rank(event_id: str) -> int:
    from ..review_channel.event_models import event_id_rank

    return event_id_rank(event_id)


def _normalized_text(value: object) -> str:
    return str(value or "").strip()
