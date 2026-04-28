"""Reducer and query helpers for event-backed review-channel state."""

from __future__ import annotations

import json
from pathlib import Path

from ..common import display_path
from .context_refs import normalize_context_pack_refs
from .event_models import ReviewChannelEventBundle, ReviewPacketRow
from .event_reducer_support import (
    hydrate_provider_job_state,
    initial_provider_state,
    record_provider_packet_state,
)
from .event_packet_rows import (
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
from .event_reducer_state import ReducedReviewStateInputs, build_reduced_review_state
from .event_store import (
    DEFAULT_REVIEW_CHANNEL_PLAN_ID,
    DEFAULT_REVIEW_CHANNEL_SESSION_ID,
    ReviewChannelArtifactPaths,
    load_agent_registry,
    load_events,
    write_legacy_projection_mirror,
)
from .state import (
    write_projection_bundle,
)
from .daemon_reducer import (
    DAEMON_EVENT_TYPES,
    DaemonSnapshot,
    build_runtime_state,
    reduce_daemon_event,
)
from .agent_session_outcome_events import AGENT_SESSION_OUTCOME_EVENT_TYPES
from .session_liveness_events import SESSION_LIVENESS_EVENT_TYPES
from .topology import build_runtime_agent_registry
from ..time_utils import utc_timestamp

_PACKET_TRANSITION_EVENT_TYPES = {"packet_acked", "packet_dismissed", "packet_applied"}


def _projection_context(
    *,
    repo_root: Path,
    review_channel_path: Path,
    artifact_paths: ReviewChannelArtifactPaths,
    prior_review_state: dict[str, object] | None,
) -> EventProjectionContext:
    return EventProjectionContext(
        repo_root=repo_root,
        review_channel_path=review_channel_path,
        projections_root=Path(artifact_paths.projections_root),
        artifact_root=Path(artifact_paths.artifact_root),
        prior_review_state=prior_review_state,
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
        packets_by_id[packet_id] = packet_from_event(event)
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
        packets_by_id[packet_id] = expired_packet


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
        ),
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
            "One or more pending review packets are past their expiry timestamp."
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
        )
    )
    return review_state, review_state.get("registry", {})
