"""Event-backed sync-status action renderer."""

from __future__ import annotations

from ...review_channel.events import artifact_paths_to_dict
from ...review_channel.state import projection_paths_to_dict
from ...time_utils import utc_timestamp
from .sync_status_agent_loop import (
    agent_loop_decisions_for_work_board,
    apply_route_attention_scope_to_agents,
    canonical_active_packet_ambiguity,
    canonical_active_packets_for_sync_status,
    extract_reviewer_runtime_field,
    inbox_observation_for_sync_status,
    packet_attention_for_sync_status,
)
from .sync_status_routes import canonical_active_packet_routes
from .sync_status_queue import sync_status_queue
from .sync_status_sections import (
    coordination_section,
    diff_window,
    work_board_section,
)


def run_sync_status_action(*, args, bundle) -> tuple[dict, int]:
    """Render the ``agent_sync`` projection from the reduced review_state."""
    sync = bundle.review_state.get("agent_sync") or {}
    work_board = bundle.review_state.get("agent_work_board") or {}
    coordination = bundle.review_state.get("coordination_state") or {}
    agents_block = dict(sync.get("agents") or {})
    target_agent = (getattr(args, "for_agent", None) or "").strip()
    visible_agent_ids = (
        {target_agent: agents_block.get(target_agent, {})}
        if target_agent
        else agents_block
    )

    routes = canonical_active_packet_routes(
        review_state=bundle.review_state,
        target_agent=target_agent,
    )
    canonical_active_packets = canonical_active_packets_for_sync_status(
        review_state=bundle.review_state,
        agent_ids=visible_agent_ids,
        route_rows=routes,
    )
    agents_block = apply_route_attention_scope_to_agents(
        agents_block,
        route_rows=routes,
    )
    decisions = agent_loop_decisions_for_work_board(
        review_state=bundle.review_state,
        work_board=work_board,
        target_agent=target_agent,
    )
    pending_packets, queue = sync_status_queue(
        review_state=bundle.review_state,
        agents_block=agents_block,
        target_agent=target_agent,
    )
    if target_agent:
        agents_block = {target_agent: agents_block.get(target_agent, {})}

    report = {
        "command": "review-channel",
        "timestamp": utc_timestamp(),
        "action": "sync-status",
        "report_mode": "event-backed",
        "ok": True,
        "exit_ok": True,
        "exit_code": 0,
        "status": "ok",
        "execution_mode": "event-backed",
        "terminal": "none",
        "schema_version": int(sync.get("schema_version") or 0),
        "contract_id": str(sync.get("contract_id") or ""),
        "source_latest_event_id": str(sync.get("source_latest_event_id") or ""),
        "event_index": str(sync.get("event_index") or ""),
        "projection_refresh_seq": int(sync.get("projection_refresh_seq") or 0),
        "refreshed_at_utc": str(sync.get("refreshed_at_utc") or ""),
        "agents": agents_block,
        "for_agent": target_agent or None,
        "diff_window": diff_window(
            args=args,
            sync=sync,
            agents_block=agents_block,
        ),
        "canonical_active_packets": canonical_active_packets,
        "canonical_active_packet_ambiguity": canonical_active_packet_ambiguity(
            routes
        ),
        "canonical_active_packet_routes": routes,
        "queue": queue,
        "packets": pending_packets,
        "work_board": work_board_section(work_board, target_agent=target_agent),
        "coordination_state": coordination_section(coordination),
        "packet_attention": packet_attention_for_sync_status(
            bundle.review_state,
            target_agent=target_agent,
            agent_loop_decisions=decisions,
        ),
        "agent_runtime_clock": extract_reviewer_runtime_field(
            bundle.review_state, "agent_runtime_clock"
        ),
        "agent_dispatch_router": dict(
            bundle.review_state.get("agent_dispatch_router") or {}
        ),
        "inbox_observation": extract_reviewer_runtime_field(
            bundle.review_state, "inbox_observation"
        ) if not target_agent else inbox_observation_for_sync_status(
            bundle.review_state,
            target_agent=target_agent,
            agent_loop_decisions=decisions,
        ),
        "agent_loop_decisions": decisions,
        "projection_paths": projection_paths_to_dict(bundle.projection_paths),
        "artifact_paths": artifact_paths_to_dict(bundle.artifact_paths),
        "warnings": list(bundle.review_state.get("warnings", [])),
        "errors": list(bundle.review_state.get("errors", [])),
    }
    return report, 0
