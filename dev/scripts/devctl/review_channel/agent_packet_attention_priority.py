"""Packet ordering helpers for actor-scoped packet attention.

v4.33 (rev_pkt_4707): ``attention_priority_key`` accepts ``current_plan_sha``
so current-plan-bound packets outrank stale packet debt.

v4.36 (rev_pkt_4708): the priority key also accepts ``row_snapshot_shas`` so
packets whose ``target_revision`` is in their target row's snapshot lineage
(but not the current canonical SHA) rank as LINEAGE_AMENDED — still
outranking truly stale debt, while triggering a typed refresh-required
blocker downstream. Backwards-compat: when both params are empty, the
priority key contributes 0 to the first dimension for every candidate and
the v4.32 5-dimension behavior is preserved verbatim.
"""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.plan_currency_authority import plan_currency_rank
from ..runtime.review_packet_inbox_actionable import attention_urgency
from ..runtime.value_coercion import coerce_text as _text
from .event_models import event_id_rank
from .packet_loop_attention import (
    packet_absorption_required,
    packet_body_attention_required,
    packet_semantic_ingestion_required,
)


def best_attention_packet(
    *,
    active_packet: Mapping[str, object],
    pending_packets: tuple[Mapping[str, object], ...],
    current_plan_sha: str = "",
    row_snapshot_shas: Mapping[str, frozenset[str] | set[str]] | None = None,
) -> Mapping[str, object]:
    candidates: list[
        tuple[tuple[int, int, int, int, int, int], Mapping[str, object]]
    ] = []
    if active_packet:
        candidates.append(
            (
                attention_priority_key(
                    active_packet,
                    source_rank=1,
                    index=-1,
                    current_plan_sha=current_plan_sha,
                    row_snapshot_shas=row_snapshot_shas,
                ),
                active_packet,
            )
        )
    candidates.extend(
        (
            attention_priority_key(
                packet,
                source_rank=0,
                index=index,
                current_plan_sha=current_plan_sha,
                row_snapshot_shas=row_snapshot_shas,
            ),
            packet,
        )
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
    current_plan_sha: str = "",
    row_snapshot_shas: Mapping[str, frozenset[str] | set[str]] | None = None,
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
        or packet_semantic_ingestion_required(
            packet,
            actor=actor,
            role=role,
            session=session,
        )
        or packet_absorption_required(
            packet,
            actor=actor,
            role=role,
            session=session,
        )
    ]
    rows.sort(
        reverse=True,
        key=lambda packet: (
            2
            if packet_absorption_required(
                packet,
                actor=actor,
                role=role,
                session=session,
            )
            else 0,
            1
            if packet_semantic_ingestion_required(
                packet,
                actor=actor,
                role=role,
                session=session,
            )
            else 0,
            *attention_priority_key(
                packet,
                source_rank=0,
                index=0,
                current_plan_sha=current_plan_sha,
                row_snapshot_shas=row_snapshot_shas,
            ),
        ),
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
    current_plan_sha: str = "",
    row_snapshot_shas: Mapping[str, frozenset[str] | set[str]] | None = None,
) -> tuple[int, int, int, int, int, int]:
    """Return the packet's priority key as a 6-tuple (v4.33+v4.36 schema).

    Dimensions, highest priority first:

    1. ``plan_currency`` — CURRENT (2), LINEAGE_AMENDED (1), or STALE (0).
       Reads ``packet["target_revision"]`` and compares against
       ``current_plan_sha`` exact-match, then falls back to lineage match in
       ``row_snapshot_shas[packet.target_ref]``. When both params are empty,
       this dimension is 0 for all packets and existing tiebreaks apply.
    2. ``urgency_rank`` — blocking=5, urgent=4, ambient=0.
    3. ``command_lane_rank`` — action_request/instruction/approval_request=3.
    4. ``event_id_rank`` — newer events outrank older.
    5. ``kind_rank + source_rank`` — finding/decision/review_failed=2,
       task_progress=1; source_rank=1 for active packet, 0 for pending.
    6. ``index`` — stable tiebreak.
    """
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
        plan_currency_rank(
            packet,
            current_plan_sha=current_plan_sha,
            row_snapshot_shas=row_snapshot_shas,
        ),
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
