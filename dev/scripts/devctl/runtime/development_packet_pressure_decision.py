"""Packet-pressure scheduling decisions for ``/develop``."""

from __future__ import annotations

from .development_packet_pressure_classification import has_durable_owner_gap
from .development_packet_pressure_models import (
    PacketAttentionIngestionDecision,
    PacketBacklogPressure,
    PacketIntentClassification,
)


def packet_attention_ingestion_decision(
    *,
    pressure: PacketBacklogPressure,
    classifications: list[PacketIntentClassification],
    actor: str,
) -> PacketAttentionIngestionDecision:
    """Select the next packet-intake action from pressure classifications."""
    packet_ids = tuple(item.packet_id for item in classifications)
    manual_packet_ids = tuple(
        item.packet_id
        for item in classifications
        if item.classification == "manual-triage-required"
        and not (item.durable_owner or item.terminal_receipt)
    )
    review_packet_ids = tuple(
        item.packet_id for item in classifications if _requires_packet_review(item)
    )
    unresolved_packet_ids = tuple(
        item.packet_id
        for item in classifications
        if not item.durable_owner and not item.terminal_receipt
    )
    if pressure.live_total >= pressure.hard_attention_budget:
        return _decision(
            decision="fail_closed",
            reason_code="hard_attention_budget_crossed",
            required_action="classify_packets_before_continuing",
            fail_closed=True,
            selected_packet_ids=packet_ids,
            next_command=_inbox_command(actor),
        )
    if manual_packet_ids:
        return _decision(
            decision="request_operator_decision",
            reason_code="manual_triage_required",
            required_action="operator_packet_triage",
            selected_packet_ids=packet_ids,
            next_command=_show_or_inbox_command(manual_packet_ids, actor),
        )
    if any(has_durable_owner_gap(item) for item in classifications):
        return _decision(
            decision="ingest_durable_intent",
            reason_code="durable_owner_gap_detected",
            required_action="write_typed_owner_or_terminal_receipt",
            selected_packet_ids=packet_ids,
            next_command=_ingest_or_inbox_command(classifications, actor),
        )
    if review_packet_ids:
        return _decision(
            decision="pivot_to_packet_review",
            reason_code="pending_packet_requires_review",
            required_action="review_selected_packets",
            selected_packet_ids=packet_ids,
            next_command=_show_or_inbox_command(review_packet_ids, actor),
        )
    if _pressure_requires_review(pressure, classifications):
        return _decision(
            decision="pivot_to_packet_review",
            reason_code=pressure.pressure_state,
            required_action="review_selected_packets",
            selected_packet_ids=packet_ids,
            next_command=_show_or_inbox_command(unresolved_packet_ids, actor),
        )
    return _decision(
        decision="continue_current_work",
        reason_code="below_budget_no_durable_gap",
        required_action="none",
        selected_packet_ids=packet_ids,
    )


def _decision(
    *,
    decision: str,
    reason_code: str,
    required_action: str,
    selected_packet_ids: tuple[str, ...],
    fail_closed: bool = False,
    next_command: str = "",
) -> PacketAttentionIngestionDecision:
    return PacketAttentionIngestionDecision(
        decision=decision,
        reason_code=reason_code,
        required_action=required_action,
        fail_closed=fail_closed,
        selected_packet_ids=selected_packet_ids,
        next_command=next_command,
    )


def _pressure_requires_review(
    pressure: PacketBacklogPressure,
    classifications: list[PacketIntentClassification],
) -> bool:
    if not any(not item.durable_owner and not item.terminal_receipt for item in classifications):
        return False
    return (
        pressure.live_total >= pressure.soft_attention_budget
        or bool(pressure.near_ttl_total)
        or bool(pressure.expired_unresolved_total)
    )


def _requires_packet_review(item: PacketIntentClassification) -> bool:
    if item.terminal_receipt:
        return False
    if item.kind in {"action_request", "approval_request", "commit_approval"}:
        if item.status in {"expired", "archived"} and item.durable_owner:
            return False
        return True
    if item.durable_owner:
        return False
    return item.classification not in {"communication-only", "lifecycle-only"}


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
    target = str(actor or "").strip() or "codex"
    return (
        "python3 dev/scripts/devctl.py review-channel --action inbox "
        f"--target {target} --actor {target} --status pending --terminal none --format md"
    )


__all__ = ["packet_attention_ingestion_decision"]
