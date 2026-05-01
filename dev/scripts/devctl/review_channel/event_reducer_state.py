"""Reduced review-state construction helpers for the event reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from ..common import display_path
from ..runtime.review_state_models import (
    CollaborationArbitrationState,
    CollaborationPeerReviewState,
    CollaborationRestartState,
    CollaborationSessionState,
    PacketInboxState,
    ReviewBridgeState,
    ReviewCurrentSessionState,
    ReviewSessionState,
    ReviewState,
)
from ..runtime.packet_continuity import build_packet_continuity_index
from .core import DEFAULT_BRIDGE_REL
from .event_projection import build_event_queue_state
from .event_reducer_ack_projection import project_stage_commit_pipeline_ack
from .event_reducer_support import build_agent_rows, legacy_agent_ids
from .event_store import (
    DEFAULT_REVIEW_CHANNEL_PLAN_ID,
    DEFAULT_REVIEW_CHANNEL_SESSION_ID,
)
from .state import project_id_for_repo
from .topology import build_planned_topology

_PLACEHOLDER_BRIDGE = ReviewBridgeState(
    overall_state="unknown", codex_poll_state="missing",
    reviewer_freshness="missing",
    reviewer_mode="tools_only", last_codex_poll_utc="",
    last_codex_poll_age_seconds=0, last_worktree_hash="",
    current_instruction="", open_findings="", claude_status="",
    claude_ack="", claude_ack_current=False,
    current_instruction_revision="", claude_ack_revision="",
    last_reviewed_scope="",
    launch_truth="",
    codex_conductor_active=False,
    claude_conductor_active=False,
)

_PLACEHOLDER_CURRENT_SESSION = ReviewCurrentSessionState(
    current_instruction="",
    current_instruction_revision="",
    implementer_status="",
    implementer_ack="",
    implementer_ack_revision="",
    implementer_ack_state="unknown",
    open_findings="",
    last_reviewed_scope="",
)

_PLACEHOLDER_COLLABORATION = CollaborationSessionState(
    schema_version=1,
    contract_id="CollaborationSession",
    session_id=DEFAULT_REVIEW_CHANNEL_SESSION_ID,
    plan_id=DEFAULT_REVIEW_CHANNEL_PLAN_ID,
    status="inactive",
    reviewer_mode="tools_only",
    operator_mode="manual",
    lead_agent="",
    review_agent="",
    coding_agent="",
    current_slice="",
    peer_review=CollaborationPeerReviewState(
        current_instruction="",
        current_instruction_revision="",
        open_findings="",
        implementer_status="",
        implementer_ack="",
        implementer_ack_state="unknown",
    ),
    arbitration=CollaborationArbitrationState(
        status="clear",
        summary="",
        owner="",
    ),
    restart=CollaborationRestartState(
        status="fresh_start",
        resumable=False,
        source="",
    ),
    ready_gates=(),
    role_assignments=(),
    participants=(),
    delegated_work=(),
)

_PLACEHOLDER_PACKET_INBOX = PacketInboxState()


@dataclass(frozen=True, slots=True)
class ReducedReviewStateInputs:
    repo_root: Path
    review_channel_path: Path
    lanes: list | None
    latest_timestamp: str
    latest_session_id: str
    latest_plan_id: str
    latest_controller_run_id: object
    errors: list[str]
    warnings: list[str]
    events: list[dict[str, object]]
    packet_rows: list[dict[str, object]]
    pending_counts: dict[str, int]
    stale_packet_count: int
    registry_state: dict[str, object]
    runtime: dict[str, object]
    expired_liveness_sessions: set[tuple[str, str]]
    agent_sync: dict[str, object] | None = None
    agent_work_board: dict[str, object] | None = None


def build_reduced_review_state(
    inputs: ReducedReviewStateInputs,
) -> dict[str, object]:
    """Build the typed reduced review-state payload prior to enrichment."""
    bridge_path = inputs.repo_root / DEFAULT_BRIDGE_REL
    typed_state = ReviewState(
        schema_version=1,
        contract_id="ReviewState",
        command="review-channel",
        action="status",
        timestamp=inputs.latest_timestamp,
        ok=not inputs.errors,
        review=ReviewSessionState(
            plan_id=inputs.latest_plan_id,
            controller_run_id=str(inputs.latest_controller_run_id or ""),
            session_id=inputs.latest_session_id,
            surface_mode="event-backed",
            active_lane="review",
            refresh_seq=len(inputs.events),
            bridge_path=display_path(bridge_path, repo_root=inputs.repo_root),
            review_channel_path=display_path(
                inputs.review_channel_path,
                repo_root=inputs.repo_root,
            ),
        ),
        queue=build_event_queue_state(
            inputs.pending_counts,
            inputs.stale_packet_count,
            inputs.packet_rows,
        ),
        current_session=project_stage_commit_pipeline_ack(
            _PLACEHOLDER_CURRENT_SESSION,
            packet_rows=inputs.packet_rows,
            events=inputs.events,
            repo_root=inputs.repo_root,
        ),
        collaboration=_PLACEHOLDER_COLLABORATION,
        bridge=_PLACEHOLDER_BRIDGE,
        attention=None,
        packets=(),
        registry=inputs.registry_state,
        packet_inbox=_PLACEHOLDER_PACKET_INBOX,
        warnings=tuple(inputs.warnings),
        errors=tuple(inputs.errors),
    )
    review_state: dict[str, object] = asdict(typed_state)
    review_state["packets"] = inputs.packet_rows
    review_state["packet_continuity"] = build_packet_continuity_index(
        inputs.packet_rows
    ).to_dict()
    if inputs.agent_sync is not None:
        review_state["agent_sync"] = inputs.agent_sync
    if inputs.agent_work_board is not None:
        review_state["agent_work_board"] = inputs.agent_work_board
    # Per rev_pkt_2546/2552/2556 (Plan 4.1 Scope 1): surface the latest typed
    # reviewer_checkpoint event payload so downstream projections (current
    # session, bridge liveness) can read the rotated instruction/revision
    # straight from the event log instead of parsing bridge.md as authority.
    from .reviewer_authority_events import (
        latest_reviewer_checkpoint_payload,
        latest_reviewer_heartbeat_payload,
    )

    checkpoint_payload = latest_reviewer_checkpoint_payload(inputs.events)
    if checkpoint_payload:
        review_state["latest_reviewer_checkpoint"] = dict(checkpoint_payload)
    heartbeat_payload = latest_reviewer_heartbeat_payload(inputs.events)
    if heartbeat_payload:
        review_state["latest_reviewer_heartbeat"] = dict(heartbeat_payload)
    review_state["_compat"] = _compat_payload(inputs)
    return review_state


def _compat_payload(inputs: ReducedReviewStateInputs) -> dict[str, object]:
    return {
        "project_id": project_id_for_repo(inputs.repo_root),
        "agents": build_agent_rows(
            packets=inputs.packet_rows,
            latest_timestamp=inputs.latest_timestamp,
            providers=legacy_agent_ids(inputs.lanes, inputs.packet_rows),
        ),
        "runtime": inputs.runtime,
        "planned_topology": build_planned_topology(
            lanes=list(inputs.lanes or []),
            timestamp=inputs.latest_timestamp,
            plan_id=inputs.latest_plan_id,
            source_path=display_path(
                inputs.review_channel_path,
                repo_root=inputs.repo_root,
            ),
        ).to_dict(),
        "expired_liveness_sessions": _expired_liveness_payload(
            inputs.expired_liveness_sessions
        ),
    }


def _expired_liveness_payload(
    expired_liveness_sessions: set[tuple[str, str]],
) -> list[str]:
    return sorted(
        {
            f"{provider}:{session_name}"
            for provider, session_name in expired_liveness_sessions
            if provider or session_name
        }
    )
