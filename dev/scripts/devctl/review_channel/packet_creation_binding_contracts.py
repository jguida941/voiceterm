"""Contracts for creation-time packet binding receipts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

PACKET_CREATION_BINDING_CONTRACT_ID = "PacketCreationBinding"
PACKET_CREATION_BINDING_SCHEMA_VERSION = 1
PACKET_CREATION_BINDING_SECTION = "## Generated Review Packet Creation Bindings"
PACKET_CREATION_BINDING_EVENT_TYPES = frozenset(
    {
        "packet_creation_binding_classified",
        "packet_creation_binding_recorded",
        "packet_creation_binding_deferred",
        "packet_creation_binding_failed",
    }
)


@dataclass(frozen=True, slots=True)
class PacketCreationBindingEvent:
    """Event payload emitted after a packet creation-binding attempt."""

    session_id: object
    project_id: str
    packet_id: object
    trace_id: object
    timestamp_utc: str
    plan_id: object
    controller_run_id: object
    event_type: str
    from_agent: object
    to_agent: object
    kind: object
    summary: object
    status: object
    packet_creation_binding: dict[str, object]
    reason: str
    schema_version: int = PACKET_CREATION_BINDING_SCHEMA_VERSION
    event_id: str = ""
    source: str = "review_channel"

    def to_event(self) -> dict[str, object]:
        payload: dict[str, Any] = asdict(self)
        payload["metadata"] = _metadata(self.reason)
        payload.pop("reason", None)
        return payload


def binding_result(status: str, reason: str, **extra: object) -> dict[str, object]:
    """Return a JSON-ready PacketCreationBinding receipt."""
    payload: dict[str, object] = {
        "schema_version": PACKET_CREATION_BINDING_SCHEMA_VERSION,
        "contract_id": PACKET_CREATION_BINDING_CONTRACT_ID,
        "status": status,
        "reason": reason,
    }
    payload.update(extra)
    return payload


def _metadata(reason: str) -> dict[str, str]:
    return {"actor": "system", "reason": reason}


__all__ = [
    "PACKET_CREATION_BINDING_CONTRACT_ID",
    "PACKET_CREATION_BINDING_EVENT_TYPES",
    "PACKET_CREATION_BINDING_SCHEMA_VERSION",
    "PACKET_CREATION_BINDING_SECTION",
    "PacketCreationBindingEvent",
    "binding_result",
]
