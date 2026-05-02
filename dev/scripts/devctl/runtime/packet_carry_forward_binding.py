"""Creation-binding helpers for packet carry-forward analysis."""

from __future__ import annotations

from collections.abc import Mapping


def creation_binding(packet: Mapping[str, object]) -> Mapping[str, object]:
    """Return the strongest durable packet binding payload on a packet row."""
    binding = packet.get("packet_creation_binding")
    if not isinstance(binding, Mapping):
        binding = packet.get("packet_durable_ingestion_receipt")
    if not isinstance(binding, Mapping):
        binding = packet.get("durable_binding")
    if not isinstance(binding, Mapping):
        return {}
    return binding


def has_durable_packet_binding(packet: Mapping[str, object]) -> bool:
    """Return whether the packet already has a typed durable owner."""
    binding = creation_binding(packet)
    status = _text(binding.get("status"))
    target = _text(binding.get("binding_target"))
    return bool(target and status in {"inserted", "updated", "already_present"})


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["creation_binding", "has_durable_packet_binding"]
