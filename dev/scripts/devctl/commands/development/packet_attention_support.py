"""Support helpers for `/develop` packet attention."""

from __future__ import annotations

from collections.abc import Mapping

from ...runtime.master_plan_contract import PlanRow
from ...runtime.packet_carry_forward_sources import packet_ids_from_plan_row
from ...runtime.review_packet_inbox_liveness import is_live_pending
from .packet_attention_actionable import pending_actionable_packet_ids
from .packet_attention_commands import required_command_for_record, show_packet_command
from .packet_attention_lifecycle import (
    expired_packet_exits_next_pool,
    packet_exits_next_pool,
    packet_rows,
)
from .packet_attention_types import (
    NO_PENDING_ATTENTION_SUMMARY,
    PacketAttentionSummaryInput,
    PacketExitContext,
)


def durable_row_id_for_packet(
    rows: tuple[PlanRow, ...],
    packet_id: str,
    *,
    durable_row_id_by_packet: Mapping[str, str] | None = None,
    packet: Mapping[str, object] | None = None,
) -> str:
    packet_text = str(packet_id or "").strip()
    row_ids = {row.row_id for row in rows}
    for row in rows:
        if packet_text and packet_text in packet_ids_from_plan_row(row):
            return row.row_id
    receipt_row_id = str(
        (durable_row_id_by_packet or {}).get(packet_text) or ""
    ).strip()
    if receipt_row_id in row_ids:
        return receipt_row_id
    target_row_id = _target_row_id_for_packet(rows, packet or {})
    if target_row_id:
        return target_row_id
    return ""


def expired_unresolved_packet_ids(
    values: tuple[str, ...],
    *,
    exit_context: PacketExitContext,
) -> tuple[str, ...]:
    packet_ids: list[str] = []
    for value in values:
        packet_id = str(value or "").strip()
        if not packet_id:
            continue
        if expired_packet_exits_next_pool(exit_context, packet_id=packet_id):
            continue
        packet_ids.append(packet_id)
    return tuple(dict.fromkeys(packet_ids))


def live_finding_packet_id(record, *, exit_context: PacketExitContext) -> str:
    if record.wake_reason != "finding_pending":
        return ""
    packet_id = str(record.latest_finding_packet_id or "").strip()
    if packet_exits_next_pool(exit_context, packet_id=packet_id):
        return ""
    return packet_id


def packet_attention_satisfied_by_ingestion(
    record,
    *,
    exit_context: PacketExitContext,
) -> bool:
    if record.wake_reason != "finding_pending":
        return False
    packet_id = str(record.latest_finding_packet_id or "").strip()
    return packet_exits_next_pool(exit_context, packet_id=packet_id)


def packet_attention_summary(context: PacketAttentionSummaryInput) -> str:
    record = context.record
    summary = NO_PENDING_ATTENTION_SUMMARY
    if context.durable_row_id:
        summary = (
            f"Packet attention requires durable row {context.durable_row_id} from "
            f"{context.latest_finding_packet_id}."
        )
    elif context.latest_finding_packet_id:
        summary = f"Packet attention requires {context.latest_finding_packet_id}."
    elif context.pending_actionable_packet_ids:
        summary = f"Packet attention requires {context.pending_actionable_packet_ids[0]}."
    elif context.latest_attention_packet_id:
        summary = (
            "Packet attention requires inbox review for "
            f"{context.latest_attention_packet_id}."
        )
    elif context.pending_delivery_packet_ids:
        summary = (
            "Packet attention requires inbox review for "
            f"{context.pending_delivery_packet_ids[0]}."
        )
    elif getattr(record, "wake_reason", "") == "expired_unresolved_packet":
        count = len(context.expired_unresolved_packet_ids)
        if count:
            summary = f"Packet debt audit requires {count} expired unresolved packet(s)."
    elif getattr(record, "wake_reason", "") == "review_loop_relaunch_required":
        summary = "Review loop relaunch is required before /develop can continue."
    elif getattr(record, "attention_status", "") == "checkpoint_required":
        summary = (
            "Checkpoint attention requires startup authority repair before "
            "/develop can continue."
        )
    elif getattr(record, "attention_status", "") == "blocked":
        reason = str(getattr(record, "wake_reason", "") or "runtime_attention").strip()
        summary = f"Runtime attention is blocked by {reason}."
    return summary


def live_pending_packet_ids(
    *,
    agent: str,
    exit_context: PacketExitContext,
) -> tuple[str, ...]:
    normalized_agent = str(agent or "").strip().lower()
    packet_ids: list[str] = []
    for packet in packet_rows(exit_context.review_state.get("packets")):
        if str(packet.get("to_agent") or "").strip().lower() != normalized_agent:
            continue
        if not is_live_pending(packet):
            continue
        packet_id = str(packet.get("packet_id") or "").strip()
        if packet_id and not packet_exits_next_pool(
            exit_context,
            packet_id=packet_id,
        ):
            packet_ids.append(packet_id)
    return tuple(dict.fromkeys(packet_ids))


def latest_attention_packet_id(
    *,
    latest_finding_packet_id: str,
    pending_actionable_packet_ids: tuple[str, ...],
    pending_delivery_packet_ids: tuple[str, ...],
) -> str:
    if latest_finding_packet_id:
        return latest_finding_packet_id
    if pending_actionable_packet_ids:
        return pending_actionable_packet_ids[0]
    if pending_delivery_packet_ids:
        return pending_delivery_packet_ids[0]
    return ""


def wake_reason_for_packet(
    review_state: Mapping[str, object],
    *,
    packet_id: str,
) -> str:
    for packet in packet_rows(review_state.get("packets")):
        if str(packet.get("packet_id") or "").strip() != packet_id:
            continue
        kind = str(packet.get("kind") or "").strip() or "packet"
        return f"{kind}_pending"
    return "packet_pending"


def _target_row_id_for_packet(
    rows: tuple[PlanRow, ...],
    packet: Mapping[str, object],
) -> str:
    if not packet:
        return ""
    for ref in _packet_binding_refs(packet):
        row_id = _row_id_for_ref(rows, ref, allow_row_id=True)
        if row_id:
            return row_id
    for ref in _packet_text_refs(packet, ("target_ref",)):
        row_id = _row_id_for_ref(rows, ref, allow_row_id=True)
        if row_id:
            return row_id
    for ref in _packet_anchor_refs(packet):
        row_id = _row_id_for_ref(rows, ref, allow_row_id=True)
        if row_id:
            return row_id
    for ref in _packet_text_refs(packet, ("intake_ref",)):
        row_id = _row_id_for_ref(rows, ref, allow_row_id=False)
        if row_id:
            return row_id
    return ""


def _packet_binding_refs(packet: Mapping[str, object]) -> tuple[str, ...]:
    refs: list[str] = []
    for field in ("durable_binding", "packet_creation_binding"):
        value = packet.get(field)
        if not isinstance(value, Mapping):
            continue
        for binding_field in ("binding_target", "target_ref", "plan_target"):
            ref = str(value.get(binding_field) or "").strip()
            if ref:
                refs.append(ref)
    return tuple(dict.fromkeys(refs))


def _packet_text_refs(
    packet: Mapping[str, object],
    fields: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            value
            for field in fields
            for value in (str(packet.get(field) or "").strip(),)
            if value
        )
    )


def _packet_anchor_refs(packet: Mapping[str, object]) -> tuple[str, ...]:
    anchor_refs = packet.get("anchor_refs")
    if not isinstance(anchor_refs, (list, tuple)):
        return ()
    return tuple(
        dict.fromkeys(str(ref or "").strip() for ref in anchor_refs if str(ref or "").strip())
    )


def _row_id_for_ref(
    rows: tuple[PlanRow, ...],
    ref: str,
    *,
    allow_row_id: bool,
) -> str:
    normalized = _normalize_plan_row_ref(ref)
    matches: list[str] = []
    for row in rows:
        if allow_row_id and row.row_id == normalized:
            matches.append(row.row_id)
            continue
        row_refs = _row_refs(row)
        if ref in row_refs or normalized in row_refs:
            matches.append(row.row_id)
    unique = tuple(dict.fromkeys(matches))
    return unique[0] if len(unique) == 1 else ""


def _row_refs(row: PlanRow) -> set[str]:
    refs = {str(row.target_ref or "").strip()}
    refs.update(str(ref or "").strip() for ref in row.anchor_refs if str(ref or "").strip())
    refs.update(_normalize_plan_row_ref(ref) for ref in tuple(refs))
    refs.discard("")
    return refs


def _normalize_plan_row_ref(ref: str) -> str:
    value = str(ref or "").strip()
    for prefix in ("plan:", "row:"):
        if value.startswith(prefix):
            return value[len(prefix) :].strip()
    return value


__all__ = [
    "NO_PENDING_ATTENTION_SUMMARY",
    "PacketAttentionSummaryInput",
    "PacketExitContext",
    "durable_row_id_for_packet",
    "expired_unresolved_packet_ids",
    "latest_attention_packet_id",
    "live_finding_packet_id",
    "live_pending_packet_ids",
    "packet_attention_satisfied_by_ingestion",
    "packet_attention_summary",
    "pending_actionable_packet_ids",
    "required_command_for_record",
    "wake_reason_for_packet",
]
