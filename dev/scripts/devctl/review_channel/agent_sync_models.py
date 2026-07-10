"""Typed contracts for the review-channel agent_sync projection (MP377-P0).

Per Codex rev_pkt_2234/2235/2247:
- Projection-only in v1; no new event types are emitted by agent_sync itself.
- Cursors are event_id strings ("rev_evt_NNNN"), never timestamps.
- ACK/APPLY/DISMISS are lower-bound consumption evidence; do not promote any
  cursor to a global high-watermark.
- Status is derived from typed packet lifecycle state recorded on
  ``ReviewPacketRow.lifecycle_current_state`` and ``status``.
"""

from __future__ import annotations

from typing import Literal, TypedDict


# Lifecycle states classified per Codex's locked policy in rev_pkt_2247.
# Active = packet still consumes coordination attention from this side.
ACTIVE_LIFECYCLE_STATES: frozenset[str] = frozenset(
    {
        "pending",
        "delivery_pending",
        "execution_pending",
        "acknowledged",
        "in_progress",
        "apply_pending_after_execution",
    }
)

# Terminal success: packet reached committed disposition. Slot-consuming.
TERMINAL_SUCCESS_STATES: frozenset[str] = frozenset({"applied"})

# Terminal non-success: packet rejected, timed out, or failed execution.
# Coordination attention released; retry slot is open.
TERMINAL_NON_SUCCESS_STATES: frozenset[str] = frozenset(
    {"failed", "dismissed", "expired", "archived"}
)


class AgentSyncRow(TypedDict):
    """One per-agent sync projection row.

    All cursor fields are event_id strings or empty strings; never None.
    Empty string means "no observation yet" — explicitly typed to keep JSON
    serialization stable across v1 consumers.

    Per Codex rev_pkt_2414/2420: typed attention-vs-execution split.

    - ``delivery_pending_action_requests_to_me`` — packets in lifecycle
      ``delivery_pending`` (just routed, not yet acked).
    - ``executing_action_requests_to_me`` — packets the agent has its hands
      on right now: lifecycle in {in_progress, execution_pending,
      apply_pending_after_execution} AND ``execution_started_by`` populated.
    - ``attention_packet_id`` — the highest-priority live work for the
      agent (identity = ``active_packet_authority.current_active_packet_for_agent``).
    - ``active_action_requests_to_me`` (DEPRECATED) — kept as union of
      delivery_pending + executing for one release cycle so legacy
      consumers don't break.
    """

    agent_id: str
    last_packet_emitted_event_id: str
    last_consumed_event_id_lower_bound: str
    last_consumed_evidence_class: Literal["lower_bound", "weak", "none"]
    active_action_requests_to_me: list[str]
    delivery_pending_action_requests_to_me: list[str]
    executing_action_requests_to_me: list[str]
    attention_packet_id: str
    pending_packets_to_me: list[str]
    derived_status: Literal["working", "polling", "blocked", "idle"]
    awaiting_packet_id: str
    awaiting_from_agent: str
    awaiting_evidence_class: Literal["weak", "none"]


class AgentSyncProjection(TypedDict):
    """Top-level agent_sync field embedded inside review_state.json."""

    schema_version: int
    contract_id: str
    source_latest_event_id: str
    event_index: str
    projection_refresh_seq: int
    refreshed_at_utc: str
    agents: dict[str, AgentSyncRow]
