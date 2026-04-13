"""Typed packet-inbox / attention reducer shared by review-state projections."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from hashlib import sha256
import json

_DEFAULT_AGENTS: tuple[str, ...] = ("codex", "claude", "cursor", "operator")
_INBOX_COMMAND_TEMPLATE = (
    "python3 dev/scripts/devctl.py review-channel --action inbox "
    "--target {agent} --terminal none --format md"
)


def build_packet_inbox_payload(
    packets: Sequence[object] | object,
    *,
    attention: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Build one canonical packet-inbox payload from reduced packet rows."""
    packet_rows = [dict(packet) for packet in _packet_rows(packets)]
    agent_payloads = [
        _build_agent_attention_payload(agent, packet_rows, attention=attention)
        for agent in _target_agents(packet_rows)
    ]
    return {
        "attention_revision": _digest_payload(
            {
                "agents": [
                    {
                        "agent": payload["agent"],
                        "attention_revision": payload["attention_revision"],
                    }
                    for payload in agent_payloads
                ],
                "global_attention_status": _normalized_global_attention_status(
                    attention
                ),
                "global_required_command": _global_required_command(attention),
            }
        ),
        "agents": agent_payloads,
    }


def _build_agent_attention_payload(
    agent: str,
    packet_rows: list[dict[str, object]],
    *,
    attention: Mapping[str, object] | None,
) -> dict[str, object]:
    targeted = [
        packet
        for packet in packet_rows
        if str(packet.get("to_agent") or "").strip().lower() == agent
    ]
    live_pending = [packet for packet in targeted if _is_live_pending(packet)]
    actionable = [packet for packet in live_pending if _is_actionable(packet)]
    selected_actionable = _select_actionable_packet(actionable)
    current_instruction_packet_id = _packet_id(selected_actionable)
    latest_finding_packet_id = _packet_id(
        _latest_packet(
            packet
            for packet in targeted
            if str(packet.get("kind") or "").strip() == "finding"
        )
    )
    pending_actionable_packet_ids = tuple(
        _packet_id(packet)
        for packet in _ordered_actionable_packets(actionable)
        if _packet_id(packet)
    )
    expired_unresolved_packet_ids = tuple(
        _packet_id(packet)
        for packet in targeted
        if _is_expired_unresolved(packet)
    )
    live_finding_packets = [
        packet
        for packet in live_pending
        if str(packet.get("kind") or "").strip() == "finding"
    ]
    attention_status, wake_reason, required_command = _agent_attention_state(
        agent=agent,
        selected_actionable=selected_actionable,
        live_finding_packets=live_finding_packets,
        expired_unresolved_packet_ids=expired_unresolved_packet_ids,
        attention=attention,
    )
    payload: dict[str, object] = {}
    payload["agent"] = agent
    payload["current_instruction_packet_id"] = current_instruction_packet_id
    payload["latest_finding_packet_id"] = latest_finding_packet_id
    payload["pending_actionable_packet_ids"] = list(pending_actionable_packet_ids)
    payload["expired_unresolved_packet_ids"] = list(expired_unresolved_packet_ids)
    payload["attention_status"] = attention_status
    payload["wake_reason"] = wake_reason
    payload["required_command"] = required_command
    payload["delivery_state"] = _delivery_state(
        selected_actionable,
        has_live_findings=bool(live_finding_packets),
        has_expired_unresolved=bool(expired_unresolved_packet_ids),
    )
    payload["attention_revision"] = _digest_payload(payload)
    return payload


def _agent_attention_state(
    *,
    agent: str,
    selected_actionable: Mapping[str, object] | None,
    live_finding_packets: list[dict[str, object]],
    expired_unresolved_packet_ids: tuple[str, ...],
    attention: Mapping[str, object] | None,
) -> tuple[str, str, str]:
    inbox_command = _INBOX_COMMAND_TEMPLATE.format(agent=agent)
    if selected_actionable is not None:
        kind = str(selected_actionable.get("kind") or "").strip() or "packet"
        return "wake_required", f"{kind}_pending", inbox_command
    if live_finding_packets:
        return "review_needed", "finding_pending", inbox_command
    if expired_unresolved_packet_ids:
        return "review_needed", "expired_unresolved_packet", inbox_command

    global_status = _normalized_global_attention_status(attention)
    if not global_status:
        return "none", "", ""
    return (
        global_status,
        str(attention.get("status") or global_status).strip(),
        _global_required_command(attention) or inbox_command,
    )


def _normalized_global_attention_status(
    attention: Mapping[str, object] | None,
) -> str:
    raw = str((attention or {}).get("status") or "").strip().lower()
    if raw in {"", "healthy", "inactive", "clear", "ready", "n/a"}:
        return ""
    if raw == "checkpoint_required":
        return "checkpoint_required"
    if raw in {"review_needed", "wake_required", "blocked"}:
        return raw
    return "blocked"


def _global_required_command(attention: Mapping[str, object] | None) -> str:
    return str((attention or {}).get("recommended_command") or "").strip()


def _delivery_state(
    selected_actionable: Mapping[str, object] | None,
    *,
    has_live_findings: bool,
    has_expired_unresolved: bool,
) -> str:
    if selected_actionable is not None:
        if str(selected_actionable.get("execution_started_at_utc") or "").strip():
            return "seen"
        if str(selected_actionable.get("delivery_observed_at_utc") or "").strip():
            return "notified"
        return "unseen"
    if has_live_findings or has_expired_unresolved:
        return "unseen"
    return "idle"


def _packet_rows(packets: Sequence[object] | object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(packets, Sequence) or isinstance(packets, (str, bytes)):
        return ()
    return tuple(packet for packet in packets if isinstance(packet, Mapping))


def _target_agents(packet_rows: list[dict[str, object]]) -> tuple[str, ...]:
    default_agents = list(_DEFAULT_AGENTS)
    extras = sorted(
        {
            str(packet.get("to_agent") or "").strip().lower()
            for packet in packet_rows
            if str(packet.get("to_agent") or "").strip()
        }
        - set(_DEFAULT_AGENTS)
    )
    return tuple(default_agents + extras)


def _ordered_actionable_packets(
    packets: Sequence[Mapping[str, object]],
) -> tuple[Mapping[str, object], ...]:
    action_requests = [packet for packet in packets if _is_action_request(packet)]
    instructions = [
        packet
        for packet in packets
        if str(packet.get("kind") or "").strip() == "instruction"
    ]
    return (
        *sorted(action_requests, key=_action_request_priority_key),
        *sorted(instructions, key=_latest_sort_key, reverse=True),
    )


def _select_actionable_packet(
    packets: Sequence[Mapping[str, object]],
) -> Mapping[str, object] | None:
    ordered = _ordered_actionable_packets(packets)
    return ordered[0] if ordered else None


def _latest_packet(
    packets: Sequence[Mapping[str, object]] | object,
) -> Mapping[str, object] | None:
    packet_rows = [
        packet
        for packet in packets
        if isinstance(packet, Mapping)
    ]
    if not packet_rows:
        return None
    return max(packet_rows, key=_latest_sort_key)


def _action_request_priority_key(packet: Mapping[str, object]) -> tuple[object, ...]:
    state_rank = {
        "execution_pending": 0,
        "delivery_pending": 1,
        "in_progress": 2,
    }
    return (
        state_rank.get(_action_request_state(packet), 9),
        _parse_utc(packet.get("expires_at_utc")),
        _parse_utc(packet.get("posted_at")),
        _packet_id(packet),
    )


def _latest_sort_key(packet: Mapping[str, object]) -> tuple[object, ...]:
    return (
        _parse_utc(packet.get("posted_at")),
        _packet_id(packet),
    )


def _action_request_state(packet: Mapping[str, object]) -> str:
    if str(packet.get("execution_started_at_utc") or "").strip():
        return "in_progress"
    if str(packet.get("delivery_observed_at_utc") or "").strip():
        return "execution_pending"
    return "delivery_pending"


def _is_actionable(packet: Mapping[str, object]) -> bool:
    return _is_action_request(packet) or str(packet.get("kind") or "").strip() == "instruction"


def _is_action_request(packet: Mapping[str, object]) -> bool:
    return str(packet.get("kind") or "").strip() == "action_request"


def _is_live_pending(packet: Mapping[str, object]) -> bool:
    if str(packet.get("status") or "").strip() != "pending":
        return False
    expires_at = _parse_utc(packet.get("expires_at_utc"))
    if expires_at is None:
        return True
    return expires_at > datetime.now(timezone.utc)


def _is_expired_unresolved(packet: Mapping[str, object]) -> bool:
    status = str(packet.get("status") or "").strip()
    if status == "expired":
        return True
    if status != "pending":
        return False
    expires_at = _parse_utc(packet.get("expires_at_utc"))
    return expires_at is not None and expires_at <= datetime.now(timezone.utc)


def _parse_utc(value: object) -> datetime:
    text = str(value or "").strip()
    if not text:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        stamp = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if stamp.tzinfo is None:
        return stamp.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc)


def _packet_id(packet: Mapping[str, object] | None) -> str:
    if packet is None:
        return ""
    return str(packet.get("packet_id") or "").strip()


def _digest_payload(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()[:12]


__all__ = ["build_packet_inbox_payload"]
