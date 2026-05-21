"""Typed packet-inbox / attention reducer shared by review-state projections."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from hashlib import sha256
import json

from .inbox_command_template import inbox_command_for_agent as _inbox_command_for_agent
from .current_plan_authority import resolve_current_plan_authority
from .plan_packet_routing import packet_can_drive_current_plan
from .review_packet_inbox_actionable import (
    attention_urgency as _attention_urgency,
    ordered_actionable_packets as _ordered_actionable_packets,
    select_actionable_packet as _select_actionable_packet,
)
from .review_packet_inbox_lookup import latest_packet as _latest_packet, packet_id as _packet_id
from .review_packet_inbox_liveness import (
    is_expired_unresolved_attention as _is_expired_unresolved_attention,
    is_live_control_packet as _is_live_control_packet,
    is_live_pending as _is_live_pending,
)
from .review_packet_inbox_actionable import is_actionable as _is_actionable
from .review_packet_inbox_merge import merge_packet_inbox_states as _merge_packet_inbox_states
from .review_packet_inbox_rows import live_packet_ids as _live_packet_ids
from .review_state_packet_models import (
    PacketInboxState,
    packet_inbox_from_mapping,
)

_DEFAULT_AGENTS: tuple[str, ...] = ("codex", "claude", "cursor", "operator")


def build_packet_inbox_payload(
    packets: Sequence[object] | object,
    *,
    attention: Mapping[str, object] | None = None,
    plan_rows: Sequence[object] | object = (),
) -> dict[str, object]:
    """Build one canonical packet-inbox payload from reduced packet rows."""
    packet_rows = [dict(packet) for packet in _packet_rows(packets)]
    plan_row_tuple = tuple(_plan_rows(plan_rows))
    agent_payloads = [
        _build_agent_attention_payload(
            agent,
            packet_rows,
            attention=attention,
            plan_rows=plan_row_tuple,
        )
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


def packet_inbox_from_review_state(
    review_state: Mapping[str, object] | None,
):
    """Return packet-inbox truth, preferring a fresh rebuild from packet rows."""
    if not isinstance(review_state, Mapping):
        return None
    packets_present = "packets" in review_state
    raw_packets = review_state.get("packets", ())
    persisted = packet_inbox_from_mapping(review_state.get("packet_inbox"))
    rebuilt = packet_inbox_from_mapping(
        build_packet_inbox_payload(
            raw_packets,
            attention=_mapping(review_state.get("attention")),
        )
    )
    if rebuilt is None:
        return persisted
    if persisted is None:
        return rebuilt
    return _merge_packet_inbox_states(
        rebuilt=rebuilt,
        persisted=persisted,
        live_packet_ids=_live_packet_ids(raw_packets) if packets_present else None,
        live_packet_ids_by_agent=(
            _live_packet_ids_by_agent(raw_packets) if packets_present else None
        ),
    )


def summarize_packet_attention_open_findings(
    review_state: Mapping[str, object] | None,
    *,
    fallback: str = "",
    agent: str = "codex",
) -> str:
    """Project packet-backed finding summaries without reviving expired work."""
    normalized_fallback = str(fallback or "").strip()
    if normalized_fallback and not _is_packet_summary_text(normalized_fallback):
        return normalized_fallback

    queue = _mapping(review_state.get("queue")) if isinstance(review_state, Mapping) else {}
    pending_total = int(queue.get("pending_total") or 0)
    expired_total = _expired_unresolved_total(review_state, agent=agent)
    summary_parts: list[str] = []
    if pending_total > 0:
        summary_parts.append(f"{pending_total} pending review packet(s)")
    if expired_total > 0:
        summary_parts.append(f"{expired_total} expired unresolved review packet(s)")
    if summary_parts:
        return "; ".join(summary_parts)
    return "none"


def _build_agent_attention_payload(
    agent: str,
    packet_rows: list[dict[str, object]],
    *,
    attention: Mapping[str, object] | None,
    plan_rows: tuple[object, ...] = (),
) -> dict[str, object]:
    targeted = _targeted_packets(packet_rows, agent)
    live_pending = [packet for packet in targeted if _is_live_pending(packet)]
    live_control = [packet for packet in targeted if _is_live_control_packet(packet)]
    active_actionable = _plan_graph_attention_packets(
        _actionable_packets(live_control),
        plan_rows=plan_rows,
    )
    pending_actionable = _plan_graph_attention_packets(
        _actionable_packets(live_pending),
        plan_rows=plan_rows,
    )
    live_finding_packets = _plan_graph_attention_packets(
        _finding_packets(live_pending),
        plan_rows=plan_rows,
    )
    selected_actionable = _select_actionable_packet(active_actionable)
    current_instruction_packet_id = _packet_id(selected_actionable)
    latest_finding_packet_id = _packet_id(_latest_packet(live_finding_packets))
    pending_actionable_packet_ids = _packet_ids(
        _ordered_actionable_packets(pending_actionable)
    )
    expired_unresolved_packet_ids = _packet_ids(
        _expired_unresolved_packets(targeted)
    )
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


def _expired_unresolved_total(
    review_state: Mapping[str, object] | None,
    *,
    agent: str,
) -> int:
    packet_inbox = packet_inbox_from_review_state(review_state)
    if packet_inbox is None:
        return 0
    record = packet_inbox.for_agent(agent)
    if record is None:
        return 0
    return len(record.expired_unresolved_packet_ids)


def _is_packet_summary_text(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"", "none"}:
        return True
    return (
        "pending review packet" in normalized
        or "expired unresolved review packet" in normalized
    )


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _targeted_packets(
    packet_rows: list[dict[str, object]],
    agent: str,
) -> list[dict[str, object]]:
    return [
        packet
        for packet in packet_rows
        if str(packet.get("to_agent") or "").strip().lower() == agent
    ]


def _finding_packets(
    packet_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    return [
        packet
        for packet in packet_rows
        if str(packet.get("kind") or "").strip() == "finding"
    ]


def _actionable_packets(
    packet_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    return [packet for packet in packet_rows if _is_actionable(packet)]


def _expired_unresolved_packets(
    packet_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    return [
        packet
        for packet in packet_rows
        if _is_expired_unresolved_attention(packet)
    ]


def _packet_ids(packet_rows: Sequence[Mapping[str, object]]) -> tuple[str, ...]:
    return tuple(
        packet_id
        for packet_id in (_packet_id(packet) for packet in packet_rows)
        if packet_id
    )


def _agent_attention_state(
    *,
    agent: str,
    selected_actionable: Mapping[str, object] | None,
    live_finding_packets: list[dict[str, object]],
    expired_unresolved_packet_ids: tuple[str, ...],
    attention: Mapping[str, object] | None,
) -> tuple[str, str, str]:
    inbox_command = _inbox_command_for_agent(agent)
    if selected_actionable is not None:
        kind = str(selected_actionable.get("kind") or "").strip() or "packet"
        urgency = _attention_urgency(selected_actionable)
        if urgency in {"urgent", "blocking"}:
            return "wake_required", f"{urgency}_attention", inbox_command
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


def _plan_rows(rows: Sequence[object] | object) -> tuple[object, ...]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return ()
    return tuple(row for row in rows if row is not None)


def _plan_graph_attention_packets(
    packet_rows: list[dict[str, object]],
    *,
    plan_rows: tuple[object, ...],
) -> list[dict[str, object]]:
    if not plan_rows:
        return packet_rows
    authority = resolve_current_plan_authority(plan_rows, pending_packets=packet_rows)
    if not authority.has_executable_plan_row:
        return packet_rows
    result: list[dict[str, object]] = []
    for packet in packet_rows:
        allowed, _routing = packet_can_drive_current_plan(
            packet,
            plan_rows,
            current_authority=authority,
            authority_affecting=_packet_authority_affecting(packet),
        )
        if allowed:
            result.append(packet)
    return result


def _packet_authority_affecting(packet: Mapping[str, object]) -> bool:
    raw = str(packet.get("authority_affecting") or "").strip().lower()
    if raw in {"1", "true", "yes"}:
        return True
    kind = str(packet.get("kind") or "").strip()
    requested_action = str(packet.get("requested_action") or "").strip()
    if requested_action == "review_only":
        return False
    return kind in {"action_request", "approval_request", "commit_approval", "instruction"}


def _live_packet_ids_by_agent(
    packets: Sequence[object] | object,
) -> dict[str, frozenset[str]]:
    by_agent: dict[str, set[str]] = {}
    for packet in _packet_rows(packets):
        agent = str(packet.get("to_agent") or "").strip().lower()
        packet_id = _packet_id(packet)
        if not agent:
            continue
        live_ids = by_agent.setdefault(agent, set())
        if not packet_id:
            continue
        if _is_live_pending(packet) or _is_expired_unresolved_attention(packet):
            live_ids.add(packet_id)
    return {agent: frozenset(packet_ids) for agent, packet_ids in by_agent.items()}


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


def _digest_payload(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()[:12]


__all__ = ["build_packet_inbox_payload"]
