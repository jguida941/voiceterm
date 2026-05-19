"""Communication-only packet helpers for agent-loop instruction checks."""

from __future__ import annotations

from collections.abc import Mapping

from dev.scripts.devctl.runtime.value_coercion import coerce_text


_PACKET_LIFECYCLE_ACTIONS = frozenset(
    (
        "absorb_packet",
        "ingest_packet_semantics",
    )
)


def _active_lifecycle_focus_matches_candidates(
    active_rows: tuple[Mapping[str, str], ...],
    active_packets: frozenset[str],
    candidate_packet_ids: tuple[str, ...],
) -> bool:
    if not candidate_packet_ids:
        return False
    candidates = frozenset(candidate_packet_ids)
    for row in active_rows:
        packet_id = row.get("packet_id", "")
        if packet_id not in active_packets or packet_id not in candidates:
            continue
        if row.get("required_action") in _PACKET_LIFECYCLE_ACTIONS:
            return True
    return False


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
