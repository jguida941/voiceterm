"""Packet-pressure classification for the typed ``/develop`` controller."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone
from typing import Any

from ..time_utils import parse_utc_timestamp
from .development_collaboration_modes import PacketAttentionPressurePolicy
from .development_packet_failure_owner import class_owner_by_packet_failure
from .development_packet_pressure_classification import (
    classify_packet,
    has_durable_owner_gap,
    role_for_packet,
    row_owner_by_packet,
    selected_packets,
)
from .development_packet_pressure_decision import packet_attention_ingestion_decision
from .development_packet_ingest_decision import packet_ingest_decisions
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
from .packet_transport_expiry import (
    packet_has_explicit_transport_expiry,
    packet_kind_allows_optional_transport_expiry,
    packet_kind_uses_default_transport_expiry,
    packet_uses_transport_expiry,
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
    terminal_receipt_by_packet: Mapping[str, str] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    """Return pressure, classifications, aggregate decision, and packet decisions."""
    pressure_policy = policy or PacketAttentionPressurePolicy()
    terminal_receipts = terminal_receipt_by_packet or {}
    packets = _packet_rows(review_state.get("packets"))
    live_packets = [packet for packet in packets if is_live_pending(packet)]
    durable_ids = set(durable_packet_ids_from_plan_rows(rows))
    debts = packet_carry_forward_debts(packets, durable_packet_ids=durable_ids)
    debt_ids = {debt.packet_id for debt in debts}
    owners = row_owner_by_packet(rows)
    class_owners = class_owner_by_packet_failure(rows)
    expired_candidates = [packet for packet in packets if is_expired_unresolved(packet)]
    expired_packets = [
        packet
        for packet in expired_candidates
        if _expired_packet_requires_attention(
            packet,
            row_owner_by_packet=owners,
            class_owner_by_failure=class_owners,
            terminal_receipt_by_packet=terminal_receipts,
        )
    ]
    selected = selected_packets(live_packets, expired_candidates, debt_ids)
    classifications = [
        classify_packet(
            packet,
            row_owner_by_packet=owners,
            class_owner_by_failure=class_owners,
            terminal_receipt_by_packet=terminal_receipts,
        )
        for packet in selected
    ]
    live_pressure_packets = [
        packet
        for packet in live_packets
        if _live_packet_requires_pressure(
            packet,
            classifications_by_packet_id=_classifications_by_packet_id(
                classifications
            ),
        )
    ]
    pressure = _pressure(
        live_packets=live_pressure_packets,
        selected_classifications=classifications,
        expired_packets=expired_packets,
        debt_ids=debt_ids,
        policy=pressure_policy,
    )
    decision = packet_attention_ingestion_decision(
        pressure=pressure,
        classifications=classifications,
        actor=actor,
    )
    per_packet_decisions = packet_ingest_decisions(
        classifications,
        actor=actor,
    )
    return (
        pressure.to_dict(),
        [item.to_dict() for item in classifications],
        decision.to_dict(),
        [item.to_dict() for item in per_packet_decisions],
    )


def _expired_packet_requires_attention(
    packet: Mapping[str, object],
    *,
    row_owner_by_packet: Mapping[str, str],
    class_owner_by_failure: Mapping[str, str],
    terminal_receipt_by_packet: Mapping[str, str],
) -> bool:
    classification = classify_packet(
        packet,
        row_owner_by_packet=row_owner_by_packet,
        class_owner_by_failure=class_owner_by_failure,
        terminal_receipt_by_packet=terminal_receipt_by_packet,
    )
    return not (classification.durable_owner or classification.terminal_receipt)


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
        if _is_actionable_pressure_item(item)
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


def _is_actionable_pressure_item(item: PacketIntentClassification) -> bool:
    if item.durable_owner or item.terminal_receipt:
        return False
    return item.classification not in {"communication-only", "lifecycle-only"}


def _classifications_by_packet_id(
    classifications: list[PacketIntentClassification],
) -> dict[str, PacketIntentClassification]:
    return {
        item.packet_id: item
        for item in classifications
        if item.packet_id
    }


def _live_packet_requires_pressure(
    packet: Mapping[str, object],
    *,
    classifications_by_packet_id: Mapping[str, PacketIntentClassification],
) -> bool:
    packet_id = _text(packet.get("packet_id"))
    item = classifications_by_packet_id.get(packet_id)
    if item is None:
        return True
    if item.terminal_receipt:
        return False
    if item.durable_owner and not _packet_requires_runtime_lifecycle(packet):
        return False
    return True


def _packet_requires_runtime_lifecycle(packet: Mapping[str, object]) -> bool:
    kind = _text(packet.get("kind"))
    if packet_kind_uses_default_transport_expiry(kind):
        return True
    if packet_kind_allows_optional_transport_expiry(kind):
        return packet_has_explicit_transport_expiry(packet)
    return False


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
    if not packet_uses_transport_expiry(packet):
        return False
    expires_at = _parse_utc(packet.get("expires_at_utc"))
    if expires_at is None:
        return False
    return expires_at <= datetime.now(timezone.utc) + timedelta(
        minutes=policy.near_ttl_minutes
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
