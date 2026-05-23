"""Event types emitted by the canonical peer-spawn driver.

Peer-spawn lifecycle events (``agent_spawn_requested``,
``agent_spawn_receipt``, ``agent_termination_receipt``) land in the
shared review-channel event log so the audit trail of "who spawned what
peer conductor under which bypass receipt" can be reconstructed
alongside packet activity. These events legitimately do NOT carry
``packet_id`` — they carry ``request_id`` / ``receipt_id`` keyed to the
typed ``AgentSpawnRequest`` / ``AgentSpawnReceipt`` /
``AgentTerminationReceipt`` contracts.

This module exists so the event reducer in
``review_channel/event_reducer.py`` can treat the peer-spawn family the
same way it already treats daemon, session-liveness, agent-session
outcome, reviewer-authority, and implementer-authority events: skip them
during packet reconstruction without raising
``"Encountered review event without packet_id."``.
"""

from __future__ import annotations

AGENT_SPAWN_EVENT_TYPES = frozenset(
    {
        "agent_spawn_requested",
        "agent_spawn_receipt",
        "agent_termination_receipt",
    }
)

__all__ = ["AGENT_SPAWN_EVENT_TYPES"]
