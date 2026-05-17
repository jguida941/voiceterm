"""Approval-request resolution predicates for pending packet queues."""

from __future__ import annotations

from collections.abc import Mapping


def approval_resolution_key(packet: object) -> tuple[str, str, str, str]:
    return (
        str(_packet_value(packet, "trace_id") or "").strip(),
        str(_packet_value(packet, "kind") or "").strip(),
        str(_packet_value(packet, "target_ref") or "").strip(),
        str(_packet_value(packet, "pipeline_generation") or "").strip(),
    )


def is_pending_approval_request(packet: object) -> bool:
    status = str(_packet_value(packet, "status") or "").strip()
    if status != "pending":
        return False
    if not bool(_packet_value(packet, "approval_required")):
        return False
    return _is_commit_approval_kind(packet)


def is_applied_approval_decision(packet: object) -> bool:
    status = str(_packet_value(packet, "status") or "").strip()
    if status != "applied":
        return False
    if bool(_packet_value(packet, "approval_required")):
        return False
    return _is_commit_approval_kind(packet)


def _is_commit_approval_kind(packet: object) -> bool:
    return str(_packet_value(packet, "kind") or "").strip() == "commit_approval"


def _packet_value(packet: object, field_name: str) -> object:
    if isinstance(packet, Mapping):
        return packet.get(field_name)
    return getattr(packet, field_name, None)


__all__ = [
    "approval_resolution_key",
    "is_applied_approval_decision",
    "is_pending_approval_request",
]
