"""Reducer and query helpers for event-backed review-channel state."""

from __future__ import annotations

import json
from pathlib import Path

from dataclasses import asdict

from ..common import display_path
from ..runtime.review_state_models import (
    CollaborationArbitrationState,
    CollaborationPeerReviewState,
    CollaborationRestartState,
    CollaborationSessionState,
    ReviewBridgeState,
    ReviewCurrentSessionState,
    ReviewSessionState,
    ReviewState,
)
from .core import DEFAULT_BRIDGE_REL, load_text, parse_lane_assignments
from .context_refs import normalize_context_pack_refs
from .event_models import ReviewChannelEventBundle, ReviewPacketRow
from .event_reducer_support import (
    build_agent_rows,
    hydrate_provider_job_state,
    initial_provider_state,
    legacy_agent_ids,
    record_provider_packet_state,
)
from .event_packet_rows import (
    apply_packet_transition,
    packet_from_event,
    summarize_packets,
)
from .pending_packets import live_pending_packets
from .event_projection import (
    build_event_queue_state,
    build_event_queue_summary,
    enrich_event_review_state,
)
from .event_store import (
    DEFAULT_REVIEW_CHANNEL_PLAN_ID,
    DEFAULT_REVIEW_CHANNEL_SESSION_ID,
    ReviewChannelArtifactPaths,
    load_agent_registry,
    load_events,
    write_legacy_projection_mirror,
)
from .state import (
    project_id_for_repo,
    write_projection_bundle,
)
from .daemon_reducer import (
    DAEMON_EVENT_TYPES,
    DaemonSnapshot,
    build_runtime_state,
    reduce_daemon_event,
)
from .session_liveness_events import SESSION_LIVENESS_EVENT_TYPES
from .topology import build_planned_topology, build_runtime_agent_registry
from ..time_utils import utc_timestamp

# Placeholder bridge state used during event reduction; the enrichment
# step replaces this with real values from bridge_liveness.
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

def load_or_refresh_event_bundle(
    *,
    repo_root: Path,
    review_channel_path: Path,
    artifact_paths: ReviewChannelArtifactPaths,
) -> ReviewChannelEventBundle:
    """Load the canonical event-backed state, rebuilding it when needed."""
    if Path(artifact_paths.event_log_path).exists():
        return refresh_event_bundle(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
        )
    state_path = Path(artifact_paths.state_path)
    if not state_path.exists():
        raise ValueError(
            "Event-backed review-channel state is unavailable: "
            f"{display_path(state_path, repo_root=repo_root)}"
        )
    try:
        review_state = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Invalid review-channel state JSON at "
            f"{display_path(state_path, repo_root=repo_root)}: {exc}"
        ) from exc
    if not isinstance(review_state, dict):
        raise ValueError("Invalid review-channel state JSON: expected top-level object")
    review_state, full_extras = enrich_event_review_state(
        review_state=review_state,
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        projections_root=Path(artifact_paths.projections_root),
        artifact_root=Path(artifact_paths.artifact_root),
    )
    agent_registry = load_agent_registry(Path(artifact_paths.projections_root))
    projection_paths = write_projection_bundle(
        output_root=Path(artifact_paths.projections_root),
        review_state=review_state,
        agent_registry=agent_registry,
        action="status",
        trace_events=[],
        full_extras=full_extras,
    )
    return ReviewChannelEventBundle(
        artifact_paths=artifact_paths,
        projection_paths=projection_paths,
        review_state=review_state,
        agent_registry=agent_registry,
        events=[],
    )


def refresh_event_bundle(
    *,
    repo_root: Path,
    review_channel_path: Path,
    artifact_paths: ReviewChannelArtifactPaths,
) -> ReviewChannelEventBundle:
    """Reduce the append-only event log into the current canonical state."""
    events = load_events(Path(artifact_paths.event_log_path))
    lanes = _load_lane_assignments(review_channel_path)
    review_state, agent_registry = reduce_events(
        events=events,
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        lanes=lanes,
    )
    review_state, full_extras = enrich_event_review_state(
        review_state=review_state,
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        projections_root=Path(artifact_paths.projections_root),
        artifact_root=Path(artifact_paths.artifact_root),
    )
    state_path = Path(artifact_paths.state_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(review_state, indent=2), encoding="utf-8")
    projection_paths = write_projection_bundle(
        output_root=Path(artifact_paths.projections_root),
        review_state=review_state,
        agent_registry=agent_registry,
        action="status",
        trace_events=events,
        full_extras=full_extras,
    )
    write_legacy_projection_mirror(
        repo_root=repo_root,
        canonical_projections_root=Path(artifact_paths.projections_root),
        review_state=review_state,
        agent_registry=agent_registry,
        trace_events=events,
    )
    return ReviewChannelEventBundle(
        artifact_paths=artifact_paths,
        projection_paths=projection_paths,
        review_state=review_state,
        agent_registry=agent_registry,
        events=events,
    )


def reduce_events(
    *,
    events: list[dict[str, object]],
    repo_root: Path,
    review_channel_path: Path,
    lanes: list | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    """Reduce the append-only event log into the latest packet/state snapshot."""
    packets_by_id: dict[str, ReviewPacketRow] = {}
    warnings: list[str] = []
    errors: list[str] = []
    latest_timestamp = utc_timestamp()
    latest_session_id = DEFAULT_REVIEW_CHANNEL_SESSION_ID
    latest_plan_id = DEFAULT_REVIEW_CHANNEL_PLAN_ID
    latest_controller_run_id = None
    provider_state = initial_provider_state(lanes)
    daemon_snapshots: dict[str, DaemonSnapshot] = {}
    last_daemon_event_utc = ""
    expired_liveness_sessions: set[tuple[str, str]] = set()
    for event in events:
        event_type = str(event.get("event_type") or "").strip()
        if event_type in DAEMON_EVENT_TYPES:
            reduce_daemon_event(daemon_snapshots, event)
            last_daemon_event_utc = str(
                event.get("timestamp_utc") or last_daemon_event_utc
            )
            latest_timestamp = str(event.get("timestamp_utc") or latest_timestamp)
            continue
        if event_type in SESSION_LIVENESS_EVENT_TYPES:
            expired_liveness_sessions.add(
                (
                    str(event.get("provider") or "").strip(),
                    str(event.get("session_name") or "").strip(),
                )
            )
            latest_timestamp = str(event.get("timestamp_utc") or latest_timestamp)
            continue
        packet_id = str(event.get("packet_id") or "").strip()
        if not packet_id:
            errors.append("Encountered review event without packet_id.")
            continue
        latest_timestamp = str(event.get("timestamp_utc") or latest_timestamp)
        latest_session_id = str(event.get("session_id") or latest_session_id)
        latest_plan_id = str(event.get("plan_id") or latest_plan_id)
        latest_controller_run_id = event.get("controller_run_id")
        if event_type == "packet_posted":
            packets_by_id[packet_id] = packet_from_event(event)
        elif event_type in {"packet_acked", "packet_dismissed", "packet_applied"}:
            packet = packets_by_id.get(packet_id)
            if packet is None:
                errors.append(
                    f"Encountered {event_type} before packet_posted for {packet_id}."
                )
                continue
            packets_by_id[packet_id] = apply_packet_transition(packet, event)
        elif event_type == "packet_expired":
            packet = packets_by_id.get(packet_id)
            if packet is None:
                errors.append(
                    f"Encountered packet_expired before packet_posted for {packet_id}."
                )
                continue
            expired_packet = dict(packet)
            expired_packet["latest_event_id"] = event.get("event_id")
            expired_packet["status"] = "expired"
            packets_by_id[packet_id] = expired_packet
        record_provider_packet_state(provider_state, event, packet_id)
    packet_rows, pending_counts, stale_packet_count = summarize_packets(packets_by_id)
    if stale_packet_count:
        warnings.append(
            "One or more pending review packets are past their expiry timestamp."
        )
    hydrate_provider_job_state(provider_state, pending_counts)
    registry_state = build_runtime_agent_registry(
        timestamp=latest_timestamp,
        plan_id=latest_plan_id,
        lanes=list(lanes or []),
        provider_state=provider_state,
    )
    runtime = build_runtime_state(daemon_snapshots, last_daemon_event_utc)
    bridge_path = repo_root / DEFAULT_BRIDGE_REL
    legacy_agents = build_agent_rows(
        packets=packet_rows,
        latest_timestamp=latest_timestamp,
        providers=legacy_agent_ids(lanes, packet_rows),
    )

    # Build typed sub-models so the reducer proves contract conformance
    # at construction time. Bridge and attention are placeholder defaults
    # here; the enrichment step replaces them with real values.
    typed_state = ReviewState(
        schema_version=1,
        contract_id="ReviewState",
        command="review-channel",
        action="status",
        timestamp=latest_timestamp,
        ok=not errors,
        review=ReviewSessionState(
            plan_id=latest_plan_id,
            controller_run_id=str(latest_controller_run_id or ""),
            session_id=latest_session_id,
            surface_mode="event-backed",
            active_lane="review",
            refresh_seq=len(events),
            bridge_path=display_path(bridge_path, repo_root=repo_root),
            review_channel_path=display_path(review_channel_path, repo_root=repo_root),
        ),
        queue=build_event_queue_state(pending_counts, stale_packet_count, packet_rows),
        current_session=_PLACEHOLDER_CURRENT_SESSION,
        collaboration=_PLACEHOLDER_COLLABORATION,
        bridge=_PLACEHOLDER_BRIDGE,
        attention=None,
        packets=(),
        registry=registry_state,
        warnings=tuple(warnings),
        errors=tuple(errors),
    )
    review_state: dict[str, object] = asdict(typed_state)
    # Compatibility boundary: raw packet rows carry richer data than the
    # typed ReviewPacketState (e.g. _sort_timestamp, trace metadata). The
    # canonical ReviewState model uses ReviewPacketState for the typed
    # contract, but emitted projections still carry the raw rows so
    # downstream consumers don't lose evidence. The closure guard
    # validates that raw rows are a superset of ReviewPacketState fields.
    review_state["packets"] = packet_rows
    # Compatibility extras kept separate from the canonical contract.
    review_state["_compat"] = {
        "project_id": project_id_for_repo(repo_root),
        "agents": legacy_agents,
        "runtime": runtime,
        "planned_topology": build_planned_topology(
            lanes=list(lanes or []),
            timestamp=latest_timestamp,
            plan_id=latest_plan_id,
            source_path=display_path(review_channel_path, repo_root=repo_root),
        ).to_dict(),
        "expired_liveness_sessions": sorted(
            {
                f"{provider}:{session_name}"
                for provider, session_name in expired_liveness_sessions
                if provider or session_name
            }
        ),
    }
    return review_state, review_state.get("registry", {})


def filter_inbox_packets(
    review_state: dict[str, object],
    *,
    target: str | None = None,
    status: str | None = None,
    limit: int | None = None,
) -> list[dict[str, object]]:
    """Filter the reduced packet list into one target/status inbox view.

    When filtering by status=pending, expired packets are excluded so the
    inbox matches pending_total, per-agent counts, and derived_next_instruction.
    """
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return []
    filtered = []
    packet_iter = live_pending_packets(packets) if status == "pending" else (
        packet for packet in packets if isinstance(packet, dict)
    )
    for packet in packet_iter:
        if target and packet.get("to_agent") != target:
            continue
        if status and packet.get("status") != status:
            continue
        filtered.append(packet)
    if limit is not None and limit >= 0:
        return filtered[:limit]
    return filtered


def filter_history_events(
    events: list[dict[str, object]],
    *,
    trace_id: str | None = None,
    limit: int | None = None,
) -> list[dict[str, object]]:
    """Filter the append-only event log into one history view."""
    filtered = [
        event
        for event in events
        if not trace_id or event.get("trace_id") == trace_id
    ]
    if limit is not None and limit >= 0:
        return filtered[-limit:]
    return filtered


def packet_by_id(
    review_state: dict[str, object],
    packet_id: str,
) -> dict[str, object] | None:
    """Look up one packet in the reduced state."""
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return None
    for packet in packets:
        if isinstance(packet, dict) and packet.get("packet_id") == packet_id:
            return packet
    return None


def load_lane_assignments(review_channel_path: Path) -> list:
    """Load lane assignments from the active review-channel markdown."""
    if not review_channel_path.exists():
        return []
    return parse_lane_assignments(load_text(review_channel_path))

def _load_lane_assignments(review_channel_path: Path) -> list:
    return load_lane_assignments(review_channel_path)
