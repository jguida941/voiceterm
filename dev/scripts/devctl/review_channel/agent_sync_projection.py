"""Build the review-channel ``agent_sync`` projection.

Per Codex rev_pkt_2235 + rev_pkt_2247 locked policy:
- Cursors come from event-log append order (rev_evt_NNNN), not timestamps.
- ACK/APPLY/DISMISS are weak/lower-bound consumption evidence — never promoted
  to a global consumed high-watermark.
- ``derived_status`` is computed from typed lifecycle state on the reduced
  ``ReviewPacketRow`` rows; no new event types in v1.
- Active acked action_requests stay live (slot-consuming) until applied,
  dismissed, failed, or apply-pending closure.
- ``awaiting_packet_id`` is weakly derived from this agent's most recent
  unacked outbound action_request to its partner.
"""

from __future__ import annotations

from collections.abc import Iterable

from .agent_sync_event_cursors import (
    _is_consumption_by_agent,
    _latest_event_id,
    _max_event_id_where,
)
from .agent_sync_models import AgentSyncProjection, AgentSyncRow
from .agent_sync_packet_classification import (
    _classify_active_split,
    _classify_inbound_packets,
    _derive_awaiting,
    _select_attention_packet,
)


def build_agent_sync_projection(
    *,
    events: list[dict[str, object]],
    packet_rows: list[dict[str, object]],
    registered_agent_ids: Iterable[str],
    refresh_seq: int,
    refreshed_at_utc: str,
) -> AgentSyncProjection:
    """Build the per-agent sync projection from append-only events + reduced rows.

    The single forward pass over ``events`` is O(N) and reuses data already
    consumed by the reducer's main pass — no extra disk reads.
    """
    agent_ids = sorted({a for a in registered_agent_ids if a})
    last_event_id = _latest_event_id(events)

    rows: dict[str, AgentSyncRow] = {}
    for agent_id in agent_ids:
        rows[agent_id] = _build_row(
            agent_id=agent_id,
            events=events,
            packet_rows=packet_rows,
        )

    return AgentSyncProjection(
        schema_version=1,
        contract_id="AgentSyncProjection",
        source_latest_event_id=last_event_id,
        event_index=last_event_id,
        projection_refresh_seq=refresh_seq,
        refreshed_at_utc=refreshed_at_utc,
        agents=rows,
    )


def _build_row(
    *,
    agent_id: str,
    events: list[dict[str, object]],
    packet_rows: list[dict[str, object]],
) -> AgentSyncRow:
    """Build one agent's sync row from raw events + reduced packet rows."""
    last_emitted = _max_event_id_where(
        events,
        lambda e: (
            str(e.get("event_type") or "") == "packet_posted"
            and str(e.get("from_agent") or "") == agent_id
        ),
    )
    last_consumed = _max_event_id_where(
        events,
        lambda e: _is_consumption_by_agent(e, agent_id, events),
    )

    pending_to_me, active_to_me = _classify_inbound_packets(
        agent_id=agent_id,
        packet_rows=packet_rows,
    )
    delivery_pending_to_me, executing_to_me = _classify_active_split(
        agent_id=agent_id,
        packet_rows=packet_rows,
    )
    awaiting_packet, awaiting_from = _derive_awaiting(
        agent_id=agent_id,
        packet_rows=packet_rows,
    )
    attention_packet_id = _select_attention_packet(
        agent_id=agent_id,
        packet_rows=packet_rows,
    )

    # Per Codex rev_pkt_2414: delivery_pending presence makes the agent
    # "working" (something to attend to), not just executing+acked. This
    # matches the new attention semantics — a freshly routed packet is
    # active work, even before lifecycle progresses to acknowledged.
    if active_to_me or delivery_pending_to_me:
        derived_status: str = "working"
    elif awaiting_packet:
        derived_status = "blocked"
    elif pending_to_me:
        derived_status = "polling"
    else:
        derived_status = "idle"

    return AgentSyncRow(
        agent_id=agent_id,
        last_packet_emitted_event_id=last_emitted,
        last_consumed_event_id_lower_bound=last_consumed,
        last_consumed_evidence_class="lower_bound" if last_consumed else "none",
        active_action_requests_to_me=sorted(active_to_me),
        delivery_pending_action_requests_to_me=sorted(delivery_pending_to_me),
        executing_action_requests_to_me=sorted(executing_to_me),
        attention_packet_id=attention_packet_id,
        pending_packets_to_me=sorted(pending_to_me),
        derived_status=derived_status,  # type: ignore[typeddict-item]
        awaiting_packet_id=awaiting_packet,
        awaiting_from_agent=awaiting_from,
        awaiting_evidence_class="weak" if awaiting_packet else "none",
    )
