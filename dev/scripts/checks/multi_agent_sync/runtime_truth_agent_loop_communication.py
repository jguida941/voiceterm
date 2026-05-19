"""Communication-only packet helpers for agent-loop instruction checks."""

from __future__ import annotations

from collections.abc import Mapping

from dev.scripts.devctl.runtime.value_coercion import coerce_text


def _active_focus_is_communication_only(
    active_rows: tuple[Mapping[str, str], ...],
    active_packets: frozenset[str],
    packet_index: Mapping[str, Mapping[str, object]],
) -> bool:
    for row in active_rows:
        packet_id = row.get("packet_id", "")
        if packet_id not in active_packets:
            continue
        if row.get("required_action") != "open_packet_body":
            continue
        if _packet_is_communication_only(packet_index.get(packet_id)):
            return True
    return False


def _packet_is_communication_only(packet: Mapping[str, object] | None) -> bool:
    if not packet:
        return False
    for key in ("durable_binding", "packet_creation_binding"):
        binding = packet.get(key)
        if not isinstance(binding, Mapping):
            continue
        if coerce_text(binding.get("binding_target_kind")) == "communication_only":
            return True
    return False
