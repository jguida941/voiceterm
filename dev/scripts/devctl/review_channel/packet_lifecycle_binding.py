"""Packet lifecycle helpers for durable plan/binding evidence."""

from __future__ import annotations

from collections.abc import Mapping


def plan_integration_recorded(value: Mapping[str, object]) -> bool:
    status = _text(value.get("status"))
    return status in {"inserted", "updated", "already_present"}


def plan_ingestion_payload(packet: Mapping[str, object]) -> Mapping[str, object]:
    payload = _mapping(packet.get("plan_ingestion"))
    if payload:
        return payload
    return _mapping(packet.get("plan_integration"))


def has_creation_binding(packet: Mapping[str, object]) -> bool:
    binding = _mapping(packet.get("packet_creation_binding"))
    if not binding:
        binding = _mapping(packet.get("packet_durable_ingestion_receipt"))
    if not binding:
        binding = _mapping(packet.get("durable_binding"))
    status = _text(binding.get("status"))
    target = _text(binding.get("binding_target"))
    return bool(target and status in {"inserted", "updated", "already_present"})


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "has_creation_binding",
    "plan_ingestion_payload",
    "plan_integration_recorded",
]
