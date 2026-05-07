"""Packet attention reader for the typed develop controller."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from ...runtime.master_plan_contract import PlanRow
from ...runtime.inbox_command_template import inbox_command_for_agent
from ...runtime.development_packet_failure_owner import class_owner_by_packet_failure
from ...runtime.packet_carry_forward_sources import (
    durable_packet_ids_from_plan_rows,
)
from ...runtime.review_packet_inbox import packet_inbox_from_review_state
from .models import DevelopmentPacketAttention
from .packet_attention_support import (
    PacketAttentionSummaryInput,
    PacketExitContext,
    durable_row_id_for_packet,
    expired_unresolved_packet_ids,
    latest_attention_packet_id,
    live_finding_packet_id,
    live_pending_packet_ids,
    packet_attention_satisfied_by_ingestion,
    packet_attention_summary,
    pending_actionable_packet_ids,
    required_command_for_record,
    wake_reason_for_packet,
)

_ATTENTION_REQUIRED_STATUSES = {
    "wake_required",
    "review_needed",
    "blocked",
    "checkpoint_required",
}

def packet_attention_from_review_state(
    review_state: Mapping[str, object],
    *,
    rows: tuple[PlanRow, ...],
    agent: str = "codex",
    terminal_receipt_by_packet: Mapping[str, str] | None = None,
) -> DevelopmentPacketAttention:
    """Return packet-driven wake state for a development controller actor."""
    terminal_receipts = terminal_receipt_by_packet or {}
    inbox = packet_inbox_from_review_state(review_state)
    record = inbox.for_agent(agent) if inbox is not None else None
    if record is None:
        return DevelopmentPacketAttention(agent=agent)
    exit_context = PacketExitContext(
        review_state=review_state,
        durable_packet_ids=frozenset(durable_packet_ids_from_plan_rows(rows)),
        class_owner_by_failure=class_owner_by_packet_failure(rows),
        terminal_receipt_by_packet=terminal_receipts,
    )
    expired_unresolved_ids = expired_unresolved_packet_ids(
        record.expired_unresolved_packet_ids,
        exit_context=exit_context,
    )
    packet_id = live_finding_packet_id(
        record,
        exit_context=exit_context,
    )
    delivery_packet_ids = live_pending_packet_ids(
        agent=agent,
        exit_context=exit_context,
    )
    status = record.attention_status
    wake_reason = record.wake_reason
    required_command = str(record.required_command or "").strip()
    if status == "none" and delivery_packet_ids:
        status = "wake_required"
        wake_reason = wake_reason_for_packet(
            review_state,
            packet_id=delivery_packet_ids[0],
        )
        required_command = inbox_command_for_agent(agent)
    durable_row_id = durable_row_id_for_packet(rows, packet_id)
    pending_packet_ids = pending_actionable_packet_ids(
        record.pending_actionable_packet_ids,
        exit_context=exit_context,
        latest_finding_packet_id=packet_id,
        wake_reason=wake_reason,
        attention_required=True,
    )
    latest_packet_id = latest_attention_packet_id(
        latest_finding_packet_id=packet_id,
        pending_actionable_packet_ids=pending_packet_ids,
        pending_delivery_packet_ids=delivery_packet_ids,
    )
    attention_required = (
        bool(pending_packet_ids)
        or bool(delivery_packet_ids)
        or bool(expired_unresolved_ids)
        or (
            status in _ATTENTION_REQUIRED_STATUSES
            and not (
                wake_reason == "expired_unresolved_packet"
                and not expired_unresolved_ids
            )
            and not packet_attention_satisfied_by_ingestion(
                record,
                exit_context=exit_context,
            )
        )
    )
    if not attention_required:
        status = "none"
        wake_reason = ""
        required_command = ""
    else:
        required_command = required_command_for_record(
            record,
            pending_packet_ids=pending_packet_ids,
            latest_finding_packet_id=packet_id,
            fallback_command=required_command,
        )
    return DevelopmentPacketAttention(
        attention_required=attention_required,
        agent=agent,
        attention_status=status,
        attention_reason=wake_reason,
        wake_reason=wake_reason,
        latest_attention_packet_id=latest_packet_id,
        latest_finding_packet_id=packet_id,
        pending_delivery_packet_ids=delivery_packet_ids,
        pending_actionable_packet_ids=pending_packet_ids,
        expired_unresolved_count=len(expired_unresolved_ids),
        required_command=required_command,
        durable_plan_row_id=durable_row_id,
        summary=packet_attention_summary(
            PacketAttentionSummaryInput(
                record=record,
                expired_unresolved_packet_ids=expired_unresolved_ids,
                durable_row_id=durable_row_id,
                latest_attention_packet_id=latest_packet_id,
                latest_finding_packet_id=packet_id,
                pending_delivery_packet_ids=delivery_packet_ids,
                pending_actionable_packet_ids=pending_packet_ids,
            )
        ),
    )


def review_state_payload(repo_root: Path) -> Mapping[str, object]:
    """Load the latest review-state projection as a typed-controller input."""
    path = repo_root / "dev/reports/review_channel/projections/latest/review_state.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


__all__ = ["packet_attention_from_review_state", "review_state_payload"]
