"""Packet attention reader for the typed develop controller."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from ...runtime.master_plan_contract import PlanRow
from ...runtime.review_packet_inbox import packet_inbox_from_review_state
from .models import DevelopmentPacketAttention


def packet_attention_from_review_state(
    review_state: Mapping[str, object],
    *,
    rows: tuple[PlanRow, ...],
    agent: str = "codex",
) -> DevelopmentPacketAttention:
    """Return packet-driven wake state for a development controller actor."""
    inbox = packet_inbox_from_review_state(review_state)
    record = inbox.for_agent(agent) if inbox is not None else None
    if record is None:
        return DevelopmentPacketAttention(agent=agent)
    packet_id = _live_finding_packet_id(record)
    status = record.attention_status
    attention_required = status in {"wake_required", "review_needed", "blocked"}
    durable_row_id = _durable_row_id_for_packet(rows, packet_id)
    pending_packet_ids = _pending_actionable_packet_ids(
        record.pending_actionable_packet_ids,
        latest_finding_packet_id=packet_id,
        wake_reason=record.wake_reason,
        attention_required=attention_required,
    )
    required_command = _required_command_for_record(
        record,
        pending_packet_ids=pending_packet_ids,
        latest_finding_packet_id=packet_id,
    )
    return DevelopmentPacketAttention(
        attention_required=attention_required,
        agent=agent,
        attention_status=status,
        wake_reason=record.wake_reason,
        latest_finding_packet_id=packet_id,
        pending_actionable_packet_ids=pending_packet_ids,
        expired_unresolved_count=len(record.expired_unresolved_packet_ids),
        required_command=required_command,
        durable_plan_row_id=durable_row_id,
        summary=_packet_attention_summary(
            record,
            durable_row_id=durable_row_id,
            latest_finding_packet_id=packet_id,
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


def _durable_row_id_for_packet(rows: tuple[PlanRow, ...], packet_id: str) -> str:
    for row in rows:
        if packet_id and packet_id in row.sourced_from_packets:
            return row.row_id
    return ""


def _pending_actionable_packet_ids(
    values: tuple[str, ...],
    *,
    latest_finding_packet_id: str,
    wake_reason: str,
    attention_required: bool,
) -> tuple[str, ...]:
    packet_ids = [str(value or "").strip() for value in values if str(value or "").strip()]
    if (
        attention_required
        and wake_reason == "finding_pending"
        and latest_finding_packet_id
        and latest_finding_packet_id not in packet_ids
    ):
        packet_ids.insert(0, latest_finding_packet_id)
    return tuple(packet_ids)


def _live_finding_packet_id(record) -> str:
    if record.wake_reason == "finding_pending":
        return str(record.latest_finding_packet_id or "").strip()
    return ""


def _required_command_for_record(
    record,
    *,
    pending_packet_ids: tuple[str, ...],
    latest_finding_packet_id: str,
) -> str:
    command = str(record.required_command or "").strip()
    if record.wake_reason == "finding_pending":
        packet_id = latest_finding_packet_id or (pending_packet_ids[0] if pending_packet_ids else "")
        if packet_id:
            return _show_packet_command(packet_id)
    if record.wake_reason != "expired_unresolved_packet":
        return command
    if pending_packet_ids or latest_finding_packet_id:
        return command
    return "python3 dev/scripts/devctl.py develop audit-packets --format md"


def _show_packet_command(packet_id: str) -> str:
    return (
        "python3 dev/scripts/devctl.py review-channel --action show "
        f"--packet-id {packet_id} --terminal none --format md"
    )


def _packet_attention_summary(
    record,
    *,
    durable_row_id: str,
    latest_finding_packet_id: str,
) -> str:
    if durable_row_id:
        return (
            f"Packet attention requires durable row {durable_row_id} from "
            f"{latest_finding_packet_id}."
        )
    if latest_finding_packet_id:
        return f"Packet attention requires {latest_finding_packet_id}."
    if record.pending_actionable_packet_ids:
        return f"Packet attention requires {record.pending_actionable_packet_ids[0]}."
    if record.wake_reason == "expired_unresolved_packet":
        count = len(record.expired_unresolved_packet_ids)
        return f"Packet debt audit requires {count} expired unresolved packet(s)."
    return "Packet attention requires inbox review before ordinary /develop work."


__all__ = ["packet_attention_from_review_state", "review_state_payload"]
