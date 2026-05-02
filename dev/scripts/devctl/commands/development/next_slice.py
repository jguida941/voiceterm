"""Next-slice selection for the typed develop controller."""

from __future__ import annotations

from ...runtime.master_plan_contract import DEFAULT_MASTER_PLAN_STORE_REL, PlanRow
from .models import DevelopmentNextSlice, DevelopmentPacketAttention


def select_next_slice(
    rows: tuple[PlanRow, ...],
    *,
    packet_attention: DevelopmentPacketAttention | None = None,
) -> DevelopmentNextSlice:
    """Select the next bounded development row from typed state."""
    packet_row = _packet_attention_row(rows, packet_attention)
    if packet_row is not None:
        return DevelopmentNextSlice(
            slice_id=packet_row.row_id,
            source=packet_row.source_doc_path or DEFAULT_MASTER_PLAN_STORE_REL,
            title=packet_row.title,
            target_ref=packet_row.target_ref,
            status=packet_row.status,
            reason=(
                "Selected because packet attention requires this durable packet-owned "
                "plan row before ordinary /develop work can continue."
            ),
        )
    if packet_attention is not None and packet_attention.attention_required:
        packet_id = (
            packet_attention.latest_attention_packet_id
            or packet_attention.latest_finding_packet_id
        )
        if packet_id:
            slice_id = f"packet:{packet_id}"
        elif packet_attention.wake_reason == "expired_unresolved_packet":
            slice_id = "packet-debt-audit"
        elif packet_attention.attention_status == "checkpoint_required":
            slice_id = "checkpoint-required"
        else:
            slice_id = "packet-attention"
        return DevelopmentNextSlice(
            slice_id=slice_id,
            source="ReviewState.packet_inbox",
            title=packet_attention.summary,
            target_ref=packet_attention.required_command,
            status="attention_required",
            reason="Packet attention preempts ordinary typed plan-row selection.",
        )
    selected = _first_row_with_status(rows, "in_progress")
    if selected is None:
        selected = _first_row_with_status(rows, "queued")
    if selected is None:
        return DevelopmentNextSlice(
            status="none",
            reason="No queued or in-progress typed plan rows found.",
        )
    return DevelopmentNextSlice(
        slice_id=selected.row_id,
        source=selected.source_doc_path or DEFAULT_MASTER_PLAN_STORE_REL,
        title=selected.title,
        target_ref=selected.target_ref,
        status=selected.status,
        reason="Selected from typed master-plan rows, preferring in-progress before queued.",
    )


def _first_row_with_status(rows: tuple[PlanRow, ...], status: str) -> PlanRow | None:
    for row in rows:
        if row.status == status:
            return row
    return None


def _packet_attention_row(
    rows: tuple[PlanRow, ...],
    packet_attention: DevelopmentPacketAttention | None,
) -> PlanRow | None:
    if packet_attention is None or not packet_attention.attention_required:
        return None
    row_id = packet_attention.durable_plan_row_id
    for row in rows:
        if row_id and row.row_id == row_id:
            return row
    packet_id = (
        packet_attention.latest_attention_packet_id
        or packet_attention.latest_finding_packet_id
    )
    if not packet_id:
        return None
    for row in rows:
        if packet_id in row.sourced_from_packets:
            return row
    return None


__all__ = ["select_next_slice"]
