"""Typed rows and bundle containers for event-backed review-channel state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from .event_store import ReviewChannelArtifactPaths
from .projection_bundle import ReviewChannelProjectionPaths


class ReviewPacketRow(TypedDict):
    """One reduced packet row written into review-channel state."""

    packet_id: object
    trace_id: object
    plan_id: object
    latest_event_id: object
    from_agent: object
    to_agent: object
    kind: object
    summary: object
    body: object
    evidence_refs: list[object]
    guidance_refs: list[object]
    context_pack_refs: list[dict[str, object]]
    confidence: float
    requested_action: object
    policy_hint: object
    approval_required: bool
    target_kind: object
    target_ref: object
    target_revision: object
    anchor_refs: list[object]
    intake_ref: object
    mutation_op: object
    target_role: object
    target_session_id: object
    pipeline_generation: object
    staged_snapshot_hash: object
    guard_results_summary: object
    full_guard_bundle_evidence: object
    plan_proposal: object
    semantic_zref: object
    source_identity: dict[str, object]
    status: object
    acked_by: object
    acked_at_utc: object
    applied_at_utc: object
    delivery_emitted_at_utc: object
    delivery_observed_at_utc: object
    delivery_observed_by: object
    execution_started_at_utc: object
    execution_started_by: object
    execution_failed_at_utc: object
    execution_failed_by: object
    execution_failed_reason: object
    apply_pending_after_execution_at_utc: object
    apply_pending_after_execution_by: object
    apply_pending_after_execution_reason: object
    posted_at: object
    expires_at_utc: object
    acknowledged_events: list[dict[str, object]]
    acted_on_events: list[dict[str, object]]
    lifecycle_current_state: object
    resolution_anchor: object
    disposition: dict[str, object]
    lifecycle_history: dict[str, object]
    reviewer_wake: dict[str, object]
    _sort_timestamp: object


class ReviewAgentRow(TypedDict):
    """One reduced agent row written into review-channel state."""

    agent_id: str
    display_name: str
    role: str
    status: str
    capabilities: list[str]
    lane: str
    last_seen_utc: str | None
    assigned_job: object
    job_status: str
    waiting_on: object
    last_packet_id_seen: object
    last_packet_id_applied: object
    script_profile: str


@dataclass(frozen=True)
class ReviewChannelEventBundle:
    """One reduced view of the current event-backed review state."""

    artifact_paths: ReviewChannelArtifactPaths
    projection_paths: ReviewChannelProjectionPaths
    review_state: dict[str, object]
    agent_registry: dict[str, object]
    events: list[dict[str, object]]


def event_id_rank(event_id: str) -> int:
    # Numeric ordering authority for `rev_evt_<int>` ids; non-matching ids
    # rank as -1 so callers can use `>` comparisons without worrying about
    # missing or malformed ids dragging the comparison forward.
    prefix = "rev_evt_"
    if not event_id.startswith(prefix):
        return -1
    try:
        return int(event_id[len(prefix):])
    except ValueError:
        return -1
