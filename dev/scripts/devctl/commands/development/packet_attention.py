"""Packet attention reader for the typed develop controller."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from ...runtime.peer_attention_window import _BLOCKING_KINDS
from ...runtime.master_plan_contract import PlanRow
from ...runtime.inbox_command_template import inbox_command_for_agent
from ...runtime.development_packet_failure_owner import class_owner_by_packet_failure
from ...runtime.packet_carry_forward_sources import (
    durable_packet_ids_from_plan_rows,
)
from ...runtime.review_packet_inbox import packet_inbox_from_review_state
from .models import DevelopmentPacketAttention
from .packet_attention_body_followup import (
    packet_body_followup_for_selection,
)
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
from .packet_attention_lifecycle import packet_by_id

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
    durable_row_id_by_packet: Mapping[str, str] | None = None,
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
    body_followup = packet_body_followup_for_selection(
        review_state,
        agent=agent,
        packet_id=latest_packet_id,
        exit_context=exit_context,
    )
    if body_followup.required and body_followup.packet_id:
        latest_packet_id = body_followup.packet_id
    attention_packet = packet_by_id(review_state, latest_packet_id)
    durable_row_id = durable_row_id_for_packet(
        rows,
        latest_packet_id,
        durable_row_id_by_packet=durable_row_id_by_packet,
        packet=attention_packet,
    )
    attention_required = (
        bool(pending_packet_ids)
        or bool(delivery_packet_ids)
        or bool(expired_unresolved_ids)
        or (
            status in _ATTENTION_REQUIRED_STATUSES
            and not _packet_specific_attention_without_packet(
                status=status,
                wake_reason=wake_reason,
                latest_finding_packet_id=packet_id,
                pending_packet_ids=pending_packet_ids,
                pending_delivery_packet_ids=delivery_packet_ids,
                expired_unresolved_packet_ids=expired_unresolved_ids,
            )
            and not (
                wake_reason == "expired_unresolved_packet"
                and not expired_unresolved_ids
            )
            and not packet_attention_satisfied_by_ingestion(
                record,
                exit_context=exit_context,
            )
        )
        or body_followup.required
    )
    if not attention_required:
        status = "none"
        wake_reason = ""
        required_command = ""
    elif body_followup.required and body_followup.command:
        status = "wake_required"
        wake_reason = body_followup.reason
        required_command = body_followup.command
    else:
        required_command = required_command_for_record(
            record,
            pending_packet_ids=pending_packet_ids,
            latest_finding_packet_id=packet_id,
            fallback_command=required_command,
            packet=attention_packet,
            route=body_followup.route,
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
        packet_kind=_packet_text(attention_packet, "kind"),
        requested_action=_packet_text(attention_packet, "requested_action"),
        authority_affecting=_authority_affecting_packet(
            attention_packet,
            durable_row_id=durable_row_id,
            rows=rows,
        ),
        summary=(
            f"Packet attention requires semantic ingestion for {latest_packet_id}."
            if body_followup.required
            and body_followup.reason == "packet_semantic_ingestion_required"
            else f"Packet attention requires absorption for {latest_packet_id}."
            if body_followup.required
            and body_followup.reason == "packet_absorption_required"
            else packet_attention_summary(
                PacketAttentionSummaryInput(
                    record=record,
                    expired_unresolved_packet_ids=expired_unresolved_ids,
                    durable_row_id=durable_row_id,
                    latest_attention_packet_id=latest_packet_id,
                    latest_finding_packet_id=packet_id,
                    pending_delivery_packet_ids=delivery_packet_ids,
                    pending_actionable_packet_ids=pending_packet_ids,
                )
            )
        ),
    )


def _authority_affecting_packet(
    packet: Mapping[str, object],
    *,
    durable_row_id: str,
    rows: tuple[PlanRow, ...],
) -> bool:
    kind = _packet_text(packet, "kind")
    requested_action = _packet_text(packet, "requested_action")
    if kind in _BLOCKING_KINDS:
        return True
    if kind == "instruction" and requested_action != "review_only":
        return True
    return _active_plan_row_bound(rows, durable_row_id)


def _active_plan_row_bound(rows: tuple[PlanRow, ...], row_id: str) -> bool:
    normalized = str(row_id or "").strip()
    if not normalized:
        return False
    return any(
        row.row_id == normalized and row.status in {"in_progress", "queued"}
        for row in rows
    )


def _packet_text(packet: Mapping[str, object], field: str) -> str:
    return str(packet.get(field) or "").strip()


def _packet_specific_attention_without_packet(
    *,
    status: str,
    wake_reason: str,
    latest_finding_packet_id: str,
    pending_packet_ids: tuple[str, ...],
    pending_delivery_packet_ids: tuple[str, ...],
    expired_unresolved_packet_ids: tuple[str, ...],
) -> bool:
    if (
        latest_finding_packet_id
        or pending_packet_ids
        or pending_delivery_packet_ids
        or expired_unresolved_packet_ids
    ):
        return False
    if status == "wake_required":
        return True
    return wake_reason in {"finding_pending", "expired_unresolved_packet"}


def review_state_payload(repo_root: Path) -> Mapping[str, object]:
    """Load the latest review-state projection as a typed-controller input."""
    path = repo_root / "dev/reports/review_channel/projections/latest/review_state.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


__all__ = ["packet_attention_from_review_state", "review_state_payload"]
