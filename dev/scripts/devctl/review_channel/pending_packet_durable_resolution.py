"""Durable packet-resolution predicates for pending packet queues."""

from __future__ import annotations

from collections.abc import Mapping


def has_durable_resolution(packet: object) -> bool:
    if _has_durable_archive(packet):
        return True
    kind = str(_packet_value(packet, "kind") or "").strip()
    if kind in {"action_request", "approval_request", "commit_approval"}:
        return False
    return bool(_packet_value(packet, "durable_binding"))


def _has_durable_archive(packet: object) -> bool:
    lifecycle = str(_packet_value(packet, "lifecycle_current_state") or "").strip()
    disposition = _packet_value(packet, "disposition")
    if not isinstance(disposition, Mapping):
        return False
    return (
        lifecycle == "archived"
        and str(disposition.get("sink") or "").strip() == "archived"
        and str(disposition.get("archive_classification") or "").strip()
        == "expired_after_durable_binding"
    )


def _packet_value(packet: object, field_name: str) -> object:
    if isinstance(packet, Mapping):
        return packet.get(field_name)
    return getattr(packet, field_name, None)


__all__ = ["has_durable_resolution"]
