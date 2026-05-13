"""Packet ordering helpers for actor-scoped packet attention."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.review_packet_inbox_actionable import attention_urgency
from ..runtime.value_coercion import coerce_text as _text
from .event_models import event_id_rank
from .packet_loop_attention import packet_body_attention_required


def best_attention_packet(
    *,
    active_packet: Mapping[str, object],
    pending_packets: tuple[Mapping[str, object], ...],
) -> Mapping[str, object]:
    candidates: list[tuple[tuple[int, int, int, int, int], Mapping[str, object]]] = []
    if active_packet:
        candidates.append(
            (
                attention_priority_key(active_packet, source_rank=1, index=-1),
                active_packet,
            )
        )
    candidates.extend(
        (attention_priority_key(packet, source_rank=0, index=index), packet)
        for index, packet in enumerate(pending_packets)
    )
    if not candidates:
        return {}
    candidates.sort(reverse=True, key=lambda row: row[0])
    return candidates[0][1]


def body_open_packets(
    pending_packets: tuple[Mapping[str, object], ...],
    *,
    actor: str,
    role: str,
    session: str,
) -> tuple[Mapping[str, object], ...]:
    rows = [
        packet
        for packet in pending_packets
        if packet_body_attention_required(
            packet,
            actor=actor,
            role=role,
            session=session,
        )
    ]
    rows.sort(
        reverse=True,
        key=lambda packet: attention_priority_key(packet, source_rank=0, index=0),
    )
    return tuple(rows)


def best_body_open_packet(
    packets: tuple[Mapping[str, object], ...],
) -> Mapping[str, object]:
    return packets[0] if packets else {}


def attention_priority_key(
    packet: Mapping[str, object],
    *,
    source_rank: int,
    index: int,
) -> tuple[int, int, int, int, int]:
    urgency_rank = {"blocking": 5, "urgent": 4, "ambient": 0}
    command_lane_rank = {
        "action_request": 3,
        "instruction": 3,
        "approval_request": 3,
    }
    kind_rank = {
        "review_failed": 2,
        "finding": 2,
        "decision": 2,
        "task_progress": 1,
    }
    return (
        urgency_rank.get(attention_urgency(packet), 0),
        command_lane_rank.get(_text(packet.get("kind")).lower(), 0),
        event_id_rank(_text(packet.get("latest_event_id"))),
        kind_rank.get(_text(packet.get("kind")).lower(), 0) + source_rank,
        index,
    )


def latest_event_id(*values: str) -> str:
    best = ""
    best_rank = -1
    for value in values:
        text = _text(value)
        rank = event_id_rank(text)
        if text and rank >= best_rank:
            best = text
            best_rank = rank
    return best
