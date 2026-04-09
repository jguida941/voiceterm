"""Typed contract for the cross-mind polling surface.

``AgentMindSlice`` is the portable projection of "what an agent was just
thinking" that sits one layer above the raw ``RolloutEvent`` stream. The
rollout-tail parser already distills provider JSONL into typed events;
this contract selects the decision-relevant subset and pins it behind a
schema that other agents, guards, and bridge projections can read without
re-walking the raw trace.

Keeping the schema thin and frozen is deliberate: the typed surface is
meant to be read by multiple consumers (other agents polling the JSON
projection, CI guards, bridge renderers) and a richer shape would drift
the contract between producers and consumers. If future phases need more
detail, extend via additive optional fields, never by mutating meaning of
existing ones.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


AGENT_MIND_CONTRACT_ID = "AgentMindSlice"
AGENT_MIND_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class AgentMindEvent:
    """One decision-relevant event from an agent's reasoning stream.

    Each event is the typed projection of a single rollout JSONL line
    after the agent-mind filter decides it is worth surfacing. Events
    retain enough traceability (``raw_event_kind``) that a downstream
    consumer can join back to the underlying ``RolloutEvent`` without
    re-reading the source file.
    """

    timestamp: str
    event_type: str
    summary: str
    tool_name: str = ""
    tool_command: str = ""
    is_escalation: bool = False
    is_error: bool = False
    raw_event_kind: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AgentMindSlice:
    """A typed snapshot of an agent's recent decisions.

    The slice is the unit of cross-mind polling: one agent reads the
    other's latest slice, looks at ``events`` to see what the peer has
    been reasoning about, and uses ``last_cursor`` to resume polling
    without re-scanning already-seen lines. ``latest_*`` timestamps give
    fast top-of-loop branching hints ("has the peer completed a task
    recently?", "is there a live escalation?") without forcing consumers
    to walk every event every poll.
    """

    schema_version: int
    contract_id: str
    agent_provider: str
    session_id: str
    session_path: str
    generated_at_utc: str
    last_cursor: str
    events: tuple[AgentMindEvent, ...] = field(default_factory=tuple)
    event_count: int = 0
    latest_task_complete_at: str = ""
    latest_escalation_at: str = ""
    latest_error_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the slice as a plain dict for JSON projection.

        Uses :func:`dataclasses.asdict` so new fields added to the
        contract inherit the projection automatically; the events tuple
        is converted to a list so downstream JSON serializers receive a
        sequence instead of a tuple-shaped array literal.
        """
        payload = asdict(self)
        payload["events"] = [event.to_dict() for event in self.events]
        return payload


__all__ = [
    "AGENT_MIND_CONTRACT_ID",
    "AGENT_MIND_SCHEMA_VERSION",
    "AgentMindEvent",
    "AgentMindSlice",
]
