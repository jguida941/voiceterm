"""Nominal wrappers for governance identifier strings."""

from __future__ import annotations

from typing import NewType, TypeAlias

from .value_coercion import coerce_string


PacketId = NewType("PacketId", str)
ReceiptId = NewType("ReceiptId", str)
PlanRowId = NewType("PlanRowId", str)

GovernanceId: TypeAlias = PacketId | ReceiptId | PlanRowId


def as_packet_id(value: object) -> PacketId:
    """Normalize an external value into a packet identifier."""
    return PacketId(coerce_string(value))


def as_receipt_id(value: object) -> ReceiptId:
    """Normalize an external value into a receipt identifier."""
    return ReceiptId(coerce_string(value))


def as_plan_row_id(value: object) -> PlanRowId:
    """Normalize an external value into a plan-row identifier."""
    return PlanRowId(coerce_string(value))


def id_text(value: GovernanceId | str) -> str:
    """Return the stable string representation of a governance identifier."""
    return coerce_string(value)


def packet_ref(packet_id: PacketId) -> str:
    """Return the canonical evidence ref for a packet identifier."""
    return _prefixed_ref("packet", packet_id)


def receipt_ref(receipt_id: ReceiptId) -> str:
    """Return the canonical evidence ref for a receipt identifier."""
    return _prefixed_ref("receipt", receipt_id)


def plan_row_ref(plan_row_id: PlanRowId) -> str:
    """Return the canonical evidence ref for a plan-row identifier."""
    return _prefixed_ref("plan_row", plan_row_id)


def _prefixed_ref(prefix: str, identifier: GovernanceId) -> str:
    token = id_text(identifier)
    if not token:
        return ""
    return f"{prefix}:{token}"


__all__ = [
    "GovernanceId",
    "PacketId",
    "PlanRowId",
    "ReceiptId",
    "as_packet_id",
    "as_plan_row_id",
    "as_receipt_id",
    "id_text",
    "packet_ref",
    "plan_row_ref",
    "receipt_ref",
]
