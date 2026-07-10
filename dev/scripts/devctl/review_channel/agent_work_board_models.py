"""Typed contracts for the review-channel agent_sync v1.1 work-board projection.

Per Codex rev_pkt_2261, rev_pkt_2263, rev_pkt_2264, rev_pkt_2266:
- Work-board fans out one v1 ``AgentSyncRow`` into N concurrent session/lane rows.
- All rows are projection-only; no new event types are emitted by v1.1.
- ``confidence_class`` signals provenance (packet_derived > session_derived > mind_derived).
- ``LaneBarrierRow`` enumerates "this lane cannot proceed because X" with addressable IDs.
- Sibling to ``AgentSyncProjection`` (under ``review_state["agent_work_board"]``),
  not nested — independent schema_version + cursor evolution.
"""

from __future__ import annotations

from typing import Literal, TypedDict


WorkBoardStatus = Literal[
    "working",
    "polling",
    "blocked",
    "idle",
    "checkpointed",
]


MutationMode = Literal[
    "live_tree",
    "isolated_worktree",
    "read_only",
]


# Per Codex rev_pkt_2278: confidence_class taxonomy.
#  - direct_typed_event: row is sourced from a typed event in the event log
#    (packet_posted/_acked/_applied/etc.) addressed to/from this actor.
#  - derived_typed_event: row is computed from typed reducer state
#    (CollaborationSession participants, AuthorityRow grants, packet_rows).
#  - agent_mind_observation: row is inferred from agent-mind tool/event
#    telemetry (rollout JSONL or claude session JSONL); auxiliary, not
#    authoritative.
#  - inferred: row is best-guess from disk session file mtimes / process
#    rows / heuristic without typed evidence.
#  - stale: row was previously valid but its last_active_utc has exceeded
#    the role's stale_after threshold; kept for visibility, not authority.
#  - planned: row represents a planned lane that has not yet been backed
#    by any live participant, packet, or session trace.
# Legacy values (packet_derived / session_derived / telemetry / mind_derived)
# kept for back-compat during the rev_pkt_2278 migration; mapped to the new
# enum at projection-build time. Remove once all consumers are migrated.
ConfidenceClass = Literal[
    "direct_typed_event",
    "derived_typed_event",
    "agent_mind_observation",
    "inferred",
    "stale",
    "planned",
    "packet_derived",
    "session_derived",
    "telemetry",
    "mind_derived",
]


LaneBarrierKind = Literal[
    "awaiting_reviewer_ack",
    "awaiting_implementer_apply",
    "awaiting_guard_pass",
    "awaiting_operator_authority",
    "awaiting_packet_ttl",
    "awaiting_capability_grant",
    "awaiting_mutation_owner_release",
    "awaiting_lane_registration",
    "awaiting_lane_barrier_clear",
]


class AgentWorkBoardRow(TypedDict):
    """One per-session-or-lane work-board row.

    String fields use empty-string sentinel ("") rather than None to keep
    JSON serialization stable (matches v1 ``AgentSyncRow`` convention).
    """

    actor_id: str
    provider: str
    role: str
    declared_role: str
    authority_role: str
    role_source: str
    role_scope: str

    session_id: str
    subagent_id: str
    lane_id: str
    instance_num: int

    terminal_label: str
    started_utc: str
    last_active_utc: str
    idle_seconds: int

    parent_agent_id: str
    conductor_id: str
    integrator_id: str

    active_packet_id: str
    # Per Codex rev_pkt_2414/2420: typed attention-vs-execution split.
    # ``active_packet_id`` is kept as the legacy/deprecated alias of
    # ``attention_packet_id`` for one release cycle.
    # ``attention_packet_id`` = highest-priority live work for the actor
    # (where claude-loop should point operator attention).
    # ``executing_packet_id`` = what the actor has its hands on right now
    # (lifecycle in {in_progress, execution_pending,
    # apply_pending_after_execution} AND ``execution_started_by`` ==
    # actor_id). Empty when the actor is not currently executing
    # anything; the row may still have an ``attention_packet_id``.
    attention_packet_id: str
    executing_packet_id: str
    plan_row_id: str
    path_scope: list[str]
    worktree_identity: str
    branch: str

    current_command: str
    current_check: str
    current_file_or_module: str

    status: WorkBoardStatus
    elapsed_seconds: int
    stale_after_seconds: int
    blocker_or_wait_reason: str
    barrier_ids: list[str]

    mutation_mode: MutationMode
    granted_capabilities: list[str]
    expected_output: str

    source_event_id: str
    source_surface: str
    confidence_class: ConfidenceClass


class LaneBarrierRow(TypedDict):
    """One typed barrier explaining why a lane cannot proceed.

    Per rev_pkt_2266: addressable, kind-enumerated, clearable by a named
    signal. Consumers can render filtered views ("show all reviewer-blocked
    lanes") without re-parsing prose.
    """

    barrier_id: str
    lane_id: str
    actor_id: str
    kind: LaneBarrierKind
    target_packet_id: str
    target_capability: str
    target_actor_id: str
    raised_at_utc: str
    raised_by_event_id: str
    expected_clear_signal: str
    summary: str


class AgentWorkBoardProjection(TypedDict):
    """Top-level work-board projection (sibling of AgentSyncProjection)."""

    schema_version: int
    contract_id: str
    source_latest_event_id: str
    event_index: str
    projection_refresh_seq: int
    refreshed_at_utc: str
    rows: list[AgentWorkBoardRow]
    barriers: list[LaneBarrierRow]


# Default staleness policy (per role) — per rev_pkt_2263 "stale_after_seconds"
# field. Operators can override via CollaborationSessionState extensions
# in a future slice; for v1.1 these are the typed defaults.
DEFAULT_STALE_AFTER_SECONDS_BY_ROLE: dict[str, int] = {
    "implementer": 600,
    "reviewer": 900,
    "conductor": 600,
    "operator": 1800,
    "operator_channel": 1800,
    "dogfood": 1200,
    "subagent": 300,
}
