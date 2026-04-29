"""Registry helpers for typed review-state parsing."""

from __future__ import annotations

from collections.abc import Mapping

from .control_state import _string, _string_rows
from .review_state_packet_models import AgentRegistryState
from .review_state_parser_rows import registry_agents_from_value


def registry_state_from_payload(
    registry_payload: Mapping[str, object],
) -> AgentRegistryState:
    return AgentRegistryState(
        timestamp=_string(registry_payload.get("timestamp"))
        or _string(registry_payload.get("updated_at")),
        agents=registry_agents_from_value(registry_payload.get("agents")),
        snapshot_id=_string(registry_payload.get("snapshot_id")),
        zref=_string(registry_payload.get("zref")),
        source_identity=source_identity(registry_payload.get("source_identity")),
        source_contract=_string(registry_payload.get("source_contract")),
        source_command=_string(registry_payload.get("source_command")),
        observed_fields=_string_rows(registry_payload.get("observed_fields")),
        inferred_fields=_string_rows(registry_payload.get("inferred_fields")),
    )


def source_identity(value: object) -> dict[str, str]:
    return {
        str(key).strip(): _string(raw_value)
        for key, raw_value in _mapping_items(value)
        if str(key).strip() and _string(raw_value)
    }


def _mapping_items(value: object):
    return value.items() if isinstance(value, Mapping) else ()


__all__ = ["registry_state_from_payload", "source_identity"]
