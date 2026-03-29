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
    latest_event_id: object
    from_agent: object
    to_agent: object
    kind: object
    summary: object
    body: object
    evidence_refs: list[object]
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
    status: object
    acked_by: object
    acked_at_utc: object
    applied_at_utc: object
    posted_at: object
    expires_at_utc: object
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
