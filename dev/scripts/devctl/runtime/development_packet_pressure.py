"""Packet-pressure classification for the typed ``/develop`` controller."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone
from typing import Any

from ..time_utils import parse_utc_timestamp
from .development_collaboration_modes import PacketAttentionPressurePolicy
from .development_packet_pressure_classification import (
    classify_packet,
    has_durable_owner_gap,
    role_for_packet,
    row_owner_by_packet,
    selected_packets,
)
from .development_packet_pressure_models import (
    PACKET_ATTENTION_INGESTION_DECISION_CONTRACT_ID,
    PACKET_BACKLOG_PRESSURE_CONTRACT_ID,
    PACKET_INTENT_CLASSIFICATION_CONTRACT_ID,
    PacketAttentionIngestionDecision,
    PacketBacklogPressure,
    PacketIntentClassification,
)
from .master_plan_contract import PlanRow
from .packet_carry_forward import (
    durable_packet_ids_from_plan_rows,
    packet_carry_forward_debts,
)
from .review_packet_inbox_liveness import (
    is_expired_unresolved,
    is_live_pending,
)


def packet_pressure_report(
    review_state: Mapping[str, object],
    *,
    rows: tuple[PlanRow, ...],
    actor: str,
    policy: PacketAttentionPressurePolicy | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    """Return pressure, selected classifications, and ingestion decision."""
    pressure_policy = policy or PacketAttentionPressurePolicy()
    packets = _packet_rows(review_state.get("packets"))
    live_packets = [packet for packet in packets if is_live_pending(packet)]
    expired_packets = [packet for packet in packets if is_expired_unresolved(packet)]
    durable_ids = set(durable_packet_ids_from_plan_rows(rows))
    debts = packet_carry_forward_debts(packets, durable_packet_ids=durable_ids)
    debt_ids = {debt.packet_id for debt in debts}
    selected = selected_packets(live_packets, expired_packets, debt_ids)
    owners = row_owner_by_packet(rows)
    classifications = [
        classify_packet(packet, row_owner_by_packet=owners)
        for packet in selected
    ]
    pressure = _pressure(
        live_packets=live_packets,
        selected_classifications=classifications,
        expired_packets=expired_packets,
        debt_ids=debt_ids,
        policy=pressure_policy,
    )
    decision = _decision(
        pressure=pressure,
        classifications=classifications,
        actor=actor,
    )
    return (
        pressure.to_dict(),
        [item.to_dict() for item in classifications],
        decision.to_dict(),
    )


def _pressure(
    *,
    live_packets: list[Mapping[str, object]],
    selected_classifications: list[PacketIntentClassification],
    expired_packets: list[Mapping[str, object]],
    debt_ids: set[str],
    policy: PacketAttentionPressurePolicy,
) -> PacketBacklogPressure:
    durable_gaps = [
        item for item in selected_classifications if has_durable_owner_gap(item)
    ]
    actionable = [
        item for item in selected_classifications
        if item.classification not in {"communication-only", "lifecycle-only"}
    ]
    return PacketBacklogPressure(
        live_total=len(live_packets),
        actionable_total=len(actionable),
        near_ttl_total=sum(
            1 for packet in live_packets if _is_near_ttl(packet, policy=policy)
        ),
        expired_unresolved_total=len(expired_packets),
        carry_forward_total=len(debt_ids),
        durable_owner_gap_total=len(durable_gaps),
        per_kind=_counts(_text(packet.get("kind")) or "unknown" for packet in live_packets),
        per_role=_counts(role_for_packet(packet) for packet in live_packets),
        selected_packet_ids=tuple(item.packet_id for item in selected_classifications),
        pressure_state=_pressure_state(
            live_total=len(live_packets),
            expired_total=len(expired_packets),
            durable_gap_total=len(durable_gaps),
            policy=policy,
        ),
        soft_attention_budget=policy.soft_attention_budget,
        hard_attention_budget=policy.hard_attention_budget,
        near_ttl_minutes=policy.near_ttl_minutes,
    )


def _decision(
    *,
    pressure: PacketBacklogPressure,
    classifications: list[PacketIntentClassification],
    actor: str,
) -> PacketAttentionIngestionDecision:
    packet_ids = tuple(item.packet_id for item in classifications)
    if pressure.live_total >= pressure.hard_attention_budget:
        return PacketAttentionIngestionDecision(
            decision="fail_closed",
            reason_code="hard_attention_budget_crossed",
            required_action="classify_packets_before_continuing",
            fail_closed=True,
            selected_packet_ids=packet_ids,
            next_command=_inbox_command(actor),
        )
    if any(item.classification == "manual-triage-required" for item in classifications):
        return PacketAttentionIngestionDecision(
            decision="request_operator_decision",
            reason_code="manual_triage_required",
            required_action="operator_packet_triage",
            fail_closed=False,
            selected_packet_ids=packet_ids,
            next_command=_show_or_inbox_command(packet_ids, actor),
        )
    if any(has_durable_owner_gap(item) for item in classifications):
        return PacketAttentionIngestionDecision(
            decision="ingest_durable_intent",
            reason_code="durable_owner_gap_detected",
            required_action="write_typed_owner_or_terminal_receipt",
            fail_closed=False,
            selected_packet_ids=packet_ids,
            next_command=_ingest_or_inbox_command(classifications, actor),
        )
    if any(_requires_packet_review(item) for item in classifications):
        return PacketAttentionIngestionDecision(
            decision="pivot_to_packet_review",
            reason_code="pending_packet_requires_review",
            required_action="review_selected_packets",
            fail_closed=False,
            selected_packet_ids=packet_ids,
            next_command=_show_or_inbox_command(packet_ids, actor),
        )
    if (
        pressure.live_total >= pressure.soft_attention_budget
        or pressure.near_ttl_total
        or pressure.expired_unresolved_total
    ):
        return PacketAttentionIngestionDecision(
            decision="pivot_to_packet_review",
            reason_code=pressure.pressure_state,
            required_action="review_selected_packets",
            fail_closed=False,
            selected_packet_ids=packet_ids,
            next_command=_show_or_inbox_command(packet_ids, actor),
        )
    return PacketAttentionIngestionDecision(
        decision="continue_current_work",
        reason_code="below_budget_no_durable_gap",
        required_action="none",
        fail_closed=False,
        selected_packet_ids=packet_ids,
    )


def _requires_packet_review(item: PacketIntentClassification) -> bool:
    return item.classification not in {"communication-only"}


def _pressure_state(
    *,
    live_total: int,
    expired_total: int,
    durable_gap_total: int,
    policy: PacketAttentionPressurePolicy,
) -> str:
    if live_total >= policy.hard_attention_budget:
        return "hard_attention_budget_crossed"
    if durable_gap_total:
        return "durable_owner_gap"
    if expired_total:
        return "expired_unresolved"
    if live_total >= policy.soft_attention_budget:
        return "soft_attention_budget_crossed"
    return "below_budget"


def _is_near_ttl(
    packet: Mapping[str, object],
    *,
    policy: PacketAttentionPressurePolicy,
) -> bool:
    expires_at = _parse_utc(packet.get("expires_at_utc"))
    if expires_at is None:
        return False
    return expires_at <= datetime.now(timezone.utc) + timedelta(
        minutes=policy.near_ttl_minutes
    )


def _show_or_inbox_command(packet_ids: tuple[str, ...], actor: str) -> str:
    if packet_ids:
        return (
            "python3 dev/scripts/devctl.py review-channel --action show "
            f"--packet-id {packet_ids[0]} --terminal none --format md"
        )
    return _inbox_command(actor)


def _ingest_or_inbox_command(
    classifications: list[PacketIntentClassification],
    actor: str,
) -> str:
    for item in classifications:
        if has_durable_owner_gap(item):
            return (
                "python3 dev/scripts/devctl.py develop ingest-intent "
                f"--packet-id {item.packet_id} --format md"
            )
    return _inbox_command(actor)


def _inbox_command(actor: str) -> str:
    target = _text(actor) or "codex"
    return (
        "python3 dev/scripts/devctl.py review-channel --action inbox "
        f"--target {target} --actor {target} --status pending --terminal none --format md"
    )


def _packet_rows(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _counts(values) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value or "unknown").strip() or "unknown"
        counts[key] = counts.get(key, 0) + 1
    return counts


def _parse_utc(value: object):
    return parse_utc_timestamp(value)


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "PACKET_ATTENTION_INGESTION_DECISION_CONTRACT_ID",
    "PACKET_BACKLOG_PRESSURE_CONTRACT_ID",
    "PACKET_INTENT_CLASSIFICATION_CONTRACT_ID",
    "PacketAttentionIngestionDecision",
    "PacketBacklogPressure",
    "PacketIntentClassification",
    "packet_pressure_report",
]
