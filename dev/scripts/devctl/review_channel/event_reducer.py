"""Reducer and query helpers for event-backed review-channel state."""

from __future__ import annotations

import json
from pathlib import Path

from ..common import display_path
from ..runtime.collaboration_packet_kinds import (
    REVIEW_ACCEPTED_PACKET_KIND,
    REVIEW_STARTED_PACKET_KIND,
)
from .context_refs import normalize_context_pack_refs
from .event_models import ReviewChannelEventBundle, ReviewPacketRow
from .event_reducer_support import (
    hydrate_provider_job_state,
    initial_provider_state,
    record_provider_packet_state,
)
from .event_packet_rows import (
    PACKET_BODY_OBSERVATION_EVENT_TYPES,
    PACKET_WAKE_EVENT_TYPES,
    apply_packet_transition,
    packet_from_event,
    summarize_packets,
)
from .event_projection import (
    EventProjectionContext,
    enrich_event_review_state,
)
from .registry_context import AgentRegistryContext
from .event_reducer_inbox import (
    filter_history_events,
    filter_history_packets,
    filter_inbox_packets,
    packet_by_id,
)
from .event_reducer_lanes import (
    load_lane_assignments,
    load_prior_projection_review_state,
)
from .agent_sync_projection import build_agent_sync_projection
from .agent_work_board_projection import build_agent_work_board_projection
from .agent_loop_decision_projection import attach_agent_loop_decision_projections
from .event_reducer_state import ReducedReviewStateInputs, build_reduced_review_state
from .event_store import (
    DEFAULT_REVIEW_CHANNEL_PLAN_ID,
    DEFAULT_REVIEW_CHANNEL_SESSION_ID,
    ReviewChannelArtifactPaths,
    load_agent_registry,
    load_events,
)
from .instruction_transitions import maybe_record_instruction_transition
from .state import (
    write_projection_bundle,
)
from .projection_bundle import artifact_writes_suppressed, projection_paths_for_root
from .daemon_reducer import (
    DAEMON_EVENT_TYPES,
    DaemonSnapshot,
    build_runtime_state,
    reduce_daemon_event,
)
from .agent_session_outcome_events import AGENT_SESSION_OUTCOME_EVENT_TYPES
from .reviewer_authority_events import REVIEWER_AUTHORITY_EVENT_TYPES
from .implementer_ack_events import IMPLEMENTER_AUTHORITY_EVENT_TYPES
from .packet_lifecycle import ACTION_REQUEST_LIFECYCLE_EVENT_TYPES
from .packet_creation_binding import PACKET_CREATION_BINDING_EVENT_TYPES
from .packet_debt_remediation_contracts import PACKET_DURABLE_INGESTION_EVENT_TYPES
from .session_liveness_events import SESSION_LIVENESS_EVENT_TYPES
from .topology import build_runtime_agent_registry
from ..time_utils import utc_timestamp

_PACKET_TRANSITION_EVENT_TYPES = {
    "packet_acked",
    "packet_dismissed",
    "packet_applied",
    "packet_plan_ingestion_recorded",
    "packet_plan_ingestion_failed",
    "packet_plan_integration_recorded",
    "packet_plan_integration_failed",
    *PACKET_CREATION_BINDING_EVENT_TYPES,
    *PACKET_DURABLE_INGESTION_EVENT_TYPES,
    *PACKET_BODY_OBSERVATION_EVENT_TYPES,
    *ACTION_REQUEST_LIFECYCLE_EVENT_TYPES,
    *PACKET_WAKE_EVENT_TYPES,
}


def _projection_context(
    *,
    repo_root: Path,
    review_channel_path: Path,
    artifact_paths: ReviewChannelArtifactPaths,
    prior_review_state: dict[str, object] | None,
    events: tuple[dict[str, object], ...] = (),
) -> EventProjectionContext:
    return EventProjectionContext(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        projections_root=Path(artifact_paths.projections_root),
        artifact_root=Path(artifact_paths.artifact_root),
        prior_review_state=prior_review_state,
        events=events,
    )


def _event_timestamp(event: dict[str, object], fallback: str) -> str:
    return str(event.get("timestamp_utc") or fallback)


def _is_legacy_manual_packet_snapshot(event: dict[str, object], event_type: str) -> bool:
    """Ignore old hand-written packet snapshot rows that predate event_type."""
    if event_type:
        return False
    return bool(
        str(event.get("packet_id") or "").strip()
        and (
            str(event.get("packet_summary") or "").strip()
            or str(event.get("packet_body") or "").strip()
        )
    )


def _record_expired_liveness_session(
    expired_liveness_sessions: set[tuple[str, str]],
    event: dict[str, object],
) -> None:
    expired_liveness_sessions.add(
        (
            str(event.get("provider") or "").strip(),
            str(event.get("session_name") or "").strip(),
        )
    )


def _apply_packet_event(
    *,
    packets_by_id: dict[str, ReviewPacketRow],
    event: dict[str, object],
    event_type: str,
    packet_id: str,
    errors: list[str],
) -> None:
    if event_type == "packet_posted":
        posted_event = _event_with_review_started_evidence(
            event=event,
            packets=packets_by_id.values(),
        )
        packets_by_id[packet_id] = packet_from_event(posted_event)
        return

    packet = packets_by_id.get(packet_id)
    if packet is None:
        errors.append(f"Encountered {event_type} before packet_posted for {packet_id}.")
        return

    if event_type in _PACKET_TRANSITION_EVENT_TYPES:
        packets_by_id[packet_id] = apply_packet_transition(packet, event)
        return

    if event_type == "packet_expired":
        expired_packet = dict(packet)
        expired_packet["latest_event_id"] = event.get("event_id")
        expired_packet["status"] = "expired"
        packets_by_id[packet_id] = apply_packet_transition(expired_packet, event)


def _event_with_review_started_evidence(
    *,
    event: dict[str, object],
    packets,
) -> dict[str, object]:
    if _text(event.get("kind")) != REVIEW_ACCEPTED_PACKET_KIND:
        return event
    if _has_review_started_ref(event):
        return event
    match = _matching_review_started_packet(event=event, packets=packets)
    if match is None:
        return event
    packet_id = _text(match.get("packet_id"))
    if not packet_id:
        return event
    enriched = dict(event)
    refs = [
        *_rows(event.get("evidence_refs")),
        f"packet:{packet_id}#review_in_progress",
    ]
    enriched["evidence_refs"] = _dedupe(refs)
    return enriched


def _matching_review_started_packet(
    *,
    event: dict[str, object],
    packets,
) -> dict[str, object] | None:
    candidates = [
        packet
        for packet in packets
        if _text(packet.get("kind")) == REVIEW_STARTED_PACKET_KIND
        and _text(packet.get("plan_id")) == _text(event.get("plan_id"))
        and _review_scope_matches(packet=packet, event=event)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda packet: _text(packet.get("posted_at")))


def _review_scope_matches(
    *,
    packet: dict[str, object],
    event: dict[str, object],
) -> bool:
    packet_target_ref = _text(packet.get("target_ref"))
    event_target_ref = _text(event.get("target_ref"))
    if packet_target_ref and event_target_ref and packet_target_ref == event_target_ref:
        return True
    shared_anchors = set(_rows(packet.get("anchor_refs"))) & set(
        _rows(event.get("anchor_refs"))
    )
    if shared_anchors:
        return True
    packet_session_id = _text(packet.get("target_session_id"))
    event_session_id = _text(event.get("target_session_id"))
    if not packet_session_id or packet_session_id != event_session_id:
        return False
    packet_role = _text(packet.get("target_role"))
    event_role = _text(event.get("target_role"))
    return bool(packet_role and event_role and packet_role == event_role)


def _has_review_started_ref(event: dict[str, object]) -> bool:
    refs = (
        *_rows(event.get("evidence_refs")),
        *_rows(event.get("guidance_refs")),
        *_rows(event.get("anchor_refs")),
    )
    return any(
        "review_started" in ref or "review_in_progress" in ref
        for ref in refs
    )


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _rows(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(
        str(item or "").strip()
        for item in value
        if str(item or "").strip()
    )


def _text(value: object) -> str:
    return str(value or "").strip()


def load_or_refresh_event_bundle(
    *,
    repo_root: Path,
    review_channel_path: Path,
    artifact_paths: ReviewChannelArtifactPaths,
) -> ReviewChannelEventBundle:
    """Load the canonical event-backed state, rebuilding it when needed."""
    prior_review_state = load_prior_projection_review_state(
        Path(artifact_paths.projections_root)
    )
    if Path(artifact_paths.event_log_path).exists():
        return refresh_event_bundle(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
            prior_review_state=prior_review_state,
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
        context=_projection_context(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
            prior_review_state=prior_review_state,
        ),
    )
    review_state = attach_agent_loop_decision_projections(review_state)
    agent_registry = load_agent_registry(Path(artifact_paths.projections_root))
    projections_root = Path(artifact_paths.projections_root)
    if artifact_writes_suppressed():
        projection_paths = projection_paths_for_root(projections_root)
    else:
        projection_paths = write_projection_bundle(
            output_root=projections_root,
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


def load_projected_event_bundle(
    *,
    artifact_paths: ReviewChannelArtifactPaths,
    include_events: bool = False,
) -> ReviewChannelEventBundle | None:
    """Load the latest projection without reducing the full event log."""
    projections_root = Path(artifact_paths.projections_root)
    review_state = load_prior_projection_review_state(projections_root)
    if review_state is None:
        return None
    event_log_path = Path(artifact_paths.event_log_path)
    events = load_events(event_log_path) if include_events and event_log_path.exists() else []
    return ReviewChannelEventBundle(
        artifact_paths=artifact_paths,
        projection_paths=projection_paths_for_root(projections_root),
        review_state=review_state,
        agent_registry=load_agent_registry(projections_root),
        events=events,
    )


def refresh_event_bundle(
    *,
    repo_root: Path,
    review_channel_path: Path,
    artifact_paths: ReviewChannelArtifactPaths,
    prior_review_state: dict[str, object] | None = None,
) -> ReviewChannelEventBundle:
    """Reduce the append-only event log into the current canonical state."""
    events = load_events(Path(artifact_paths.event_log_path))
    lanes = load_lane_assignments(review_channel_path)
    review_state, agent_registry = reduce_events(
        events=events,
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        lanes=lanes,
    )
    review_state, full_extras = enrich_event_review_state(
        review_state=review_state,
        context=_projection_context(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
            prior_review_state=prior_review_state,
            events=tuple(events),
        ),
    )
    maybe_record_instruction_transition(
        repo_root=repo_root,
        prior_review_state=prior_review_state,
        review_state=review_state,
    )
    review_state = attach_agent_loop_decision_projections(review_state)
    projections_root = Path(artifact_paths.projections_root)
    if artifact_writes_suppressed():
        projection_paths = projection_paths_for_root(projections_root)
    else:
        # Per Codex rev_pkt_2406/2409/2413/2424/2437/2446 atomic-publication series:
        # state.json is read by check_review_surface_consistency alongside the
        # write_projection_bundle outputs below. Plain Path.write_text races those
        # bundle writes and produces snapshot/zref drift in the cross-surface check.
        # Multi-file bundle transactionality (rev_pkt_2417 Tier 2) is the broader fix.
        from .projection_bundle_io import atomic_write_text

        state_path = Path(artifact_paths.state_path)
        atomic_write_text(state_path, json.dumps(review_state, indent=2))
        projection_paths = write_projection_bundle(
            output_root=projections_root,
            review_state=review_state,
            agent_registry=agent_registry,
            action="status",
            trace_events=events,
            full_extras=full_extras,
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
            last_daemon_event_utc = _event_timestamp(event, last_daemon_event_utc)
            latest_timestamp = _event_timestamp(event, latest_timestamp)
            continue

        if event_type in SESSION_LIVENESS_EVENT_TYPES:
            _record_expired_liveness_session(expired_liveness_sessions, event)
            latest_timestamp = _event_timestamp(event, latest_timestamp)
            continue

        if event_type in AGENT_SESSION_OUTCOME_EVENT_TYPES:
            latest_timestamp = _event_timestamp(event, latest_timestamp)
            continue

        if (
            event_type in REVIEWER_AUTHORITY_EVENT_TYPES
            or event_type in IMPLEMENTER_AUTHORITY_EVENT_TYPES
        ):
            # Per rev_pkt_2546 (Plan 4.1 Scope 1): reviewer heartbeat /
            # reviewer checkpoint events and role-keyed implementer ACK
            # events do not carry packet_id; they populate typed
            # current_session/liveness via downstream projection helpers
            # consuming the event stream directly.
            latest_timestamp = _event_timestamp(event, latest_timestamp)
            continue

        if _is_legacy_manual_packet_snapshot(event, event_type):
            latest_timestamp = _event_timestamp(event, latest_timestamp)
            continue

        packet_id = str(event.get("packet_id") or "").strip()
        if not packet_id:
            errors.append("Encountered review event without packet_id.")
            continue

        latest_timestamp = _event_timestamp(event, latest_timestamp)
        latest_session_id = str(event.get("session_id") or latest_session_id)
        latest_plan_id = str(event.get("plan_id") or latest_plan_id)
        latest_controller_run_id = event.get("controller_run_id")

        _apply_packet_event(
            packets_by_id=packets_by_id,
            event=event,
            event_type=event_type,
            packet_id=packet_id,
            errors=errors,
        )
        record_provider_packet_state(provider_state, event, packet_id)

    packet_rows, pending_counts, stale_packet_count = summarize_packets(packets_by_id)
    if stale_packet_count:
        warnings.append(
            "One or more pending runtime-transport review packets are past their expiry timestamp."
        )

    hydrate_provider_job_state(provider_state, pending_counts)
    registry_state = build_runtime_agent_registry(
        context=AgentRegistryContext(
            timestamp=latest_timestamp,
            plan_id=latest_plan_id,
        ),
        lanes=list(lanes or []),
        provider_state=provider_state,
    )
    runtime = build_runtime_state(daemon_snapshots, last_daemon_event_utc)

    agent_sync_projection = build_agent_sync_projection(
        events=events,
        packet_rows=packet_rows,
        registered_agent_ids=_registered_agent_ids_from_registry(registry_state),
        refresh_seq=len(events),
        refreshed_at_utc=latest_timestamp,
    )

    # Build review_state first WITHOUT work-board so the typed `collaboration`
    # block exists; then enrich with work-board which reads typed
    # CollaborationParticipantState. Per Codex rev_pkt_2271 #2: "v1.1 should
    # build/enrich the work-board after that runtime state exists, using
    # bundle.review_state rather than rescanning broad packet history."
    review_state = build_reduced_review_state(
        ReducedReviewStateInputs(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            lanes=lanes,
            latest_timestamp=latest_timestamp,
            latest_session_id=latest_session_id,
            latest_plan_id=latest_plan_id,
            latest_controller_run_id=latest_controller_run_id,
            errors=errors,
            warnings=warnings,
            events=events,
            packet_rows=packet_rows,
            pending_counts=pending_counts,
            stale_packet_count=stale_packet_count,
            registry_state=registry_state,
            runtime=runtime,
            expired_liveness_sessions=expired_liveness_sessions,
            agent_sync=dict(agent_sync_projection),
            agent_work_board=None,
        )
    )

    collaboration_block = review_state.get("collaboration")
    if not isinstance(collaboration_block, dict):
        collaboration_block = None
    agent_work_board_projection = build_agent_work_board_projection(
        events=events,
        packet_rows=packet_rows,
        agent_sync_payload=dict(agent_sync_projection),
        collaboration=collaboration_block,
        refresh_seq=len(events),
        refreshed_at_utc=latest_timestamp,
    )
    review_state["agent_work_board"] = dict(agent_work_board_projection)

    return review_state, review_state.get("registry", {})


def _registered_agent_ids_from_registry(registry_state: object) -> list[str]:
    """Iterate registered participant ids from the runtime agent registry.

    Per Codex rev_pkt_2247: never hardcode {codex, claude}; pull from typed
    registry state so bounded swarm lanes auto-extend agent_sync coverage.

    Accepts either the typed ``AgentRegistryState`` dataclass (with an
    ``agents`` tuple of ``AgentRegistryEntryState`` rows) or the post-asdict
    dict-of-dicts shape some callers may provide.
    """
    agents = (
        registry_state.get("agents")
        if isinstance(registry_state, dict)
        else getattr(registry_state, "agents", None)
    )
    if not agents:
        return []
    ids: list[str] = []
    for row in agents:
        agent_id = (
            row.get("agent_id") if isinstance(row, dict)
            else getattr(row, "agent_id", "")
        )
        agent_id_str = str(agent_id or "")
        if agent_id_str:
            ids.append(agent_id_str)
    return ids
