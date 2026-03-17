"""Reducer and query helpers for event-backed review-channel state."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ..common import display_path
from ..runtime.role_profile import role_for_provider
from .core import load_text, parse_lane_assignments
from .context_refs import normalize_context_pack_refs
from .event_models import ReviewAgentRow, ReviewChannelEventBundle, ReviewPacketRow
from .event_store import (
    DEFAULT_REVIEW_CHANNEL_PLAN_ID,
    DEFAULT_REVIEW_CHANNEL_SESSION_ID,
    ReviewChannelArtifactPaths,
    load_agent_registry,
    load_events,
    parse_utc,
    write_legacy_projection_mirror,
)
from .state import (
    build_agent_registry_from_lanes,
    project_id_for_repo,
    write_projection_bundle,
)
from .daemon_reducer import (
    DAEMON_EVENT_TYPES,
    DaemonSnapshot,
    build_runtime_state,
    reduce_daemon_event,
)
from ..time_utils import utc_timestamp

_ROLE_JOB_STATE: dict[str, str] = {
    "reviewer": "reviewing",
    "implementer": "implementing",
    "operator": "waiting",
}


def _agent_capabilities(agent_id: str) -> list[str]:
    """Return the declared capabilities for a known agent provider."""
    if agent_id == "codex":
        return ["review", "planning", "coordination"]
    if agent_id == "operator":
        return ["approval", "dispatch", "triage"]
    return ["implementation", "fixes", "handoff"]


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
    agent_registry = load_agent_registry(Path(artifact_paths.projections_root))
    projection_paths = write_projection_bundle(
        output_root=Path(artifact_paths.projections_root),
        review_state=review_state,
        agent_registry=agent_registry,
        action="status",
        trace_events=[],
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
    state_path = Path(artifact_paths.state_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(review_state, indent=2), encoding="utf-8")
    projection_paths = write_projection_bundle(
        output_root=Path(artifact_paths.projections_root),
        review_state=review_state,
        agent_registry=agent_registry,
        action="status",
        trace_events=events,
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


def _build_queue_summary(
    pending_counts: dict[str, int], stale_packet_count: int
) -> dict[str, object]:
    summary: dict[str, object] = {"pending_total": sum(pending_counts.values())}
    for provider, count in pending_counts.items():
        summary[f"pending_{provider}"] = count
    summary["stale_packet_count"] = stale_packet_count
    return summary


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
    provider_state = {"codex": {}, "claude": {}, "cursor": {}, "operator": {}}
    daemon_snapshots: dict[str, DaemonSnapshot] = {}
    last_daemon_event_utc = ""
    for event in events:
        event_type = str(event.get("event_type") or "").strip()
        if event_type in DAEMON_EVENT_TYPES:
            reduce_daemon_event(daemon_snapshots, event)
            last_daemon_event_utc = str(
                event.get("timestamp_utc") or last_daemon_event_utc
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
            packets_by_id[packet_id] = _packet_from_event(event)
        elif event_type in {"packet_acked", "packet_dismissed", "packet_applied"}:
            packet = packets_by_id.get(packet_id)
            if packet is None:
                errors.append(
                    f"Encountered {event_type} before packet_posted for {packet_id}."
                )
                continue
            packets_by_id[packet_id] = _apply_transition(packet, event)
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
        _record_provider_packet_state(provider_state, event, packet_id)
    packet_rows, pending_counts, stale_packet_count = _summarize_packets(packets_by_id)
    if stale_packet_count:
        warnings.append(
            "One or more pending review packets are past their expiry timestamp."
        )
    _hydrate_provider_job_state(provider_state, pending_counts)
    registry = build_agent_registry_from_lanes(
        list(lanes or []),
        timestamp=latest_timestamp,
        provider_state=provider_state,
    )
    runtime = build_runtime_state(daemon_snapshots, last_daemon_event_utc)
    review_state = {
        "schema_version": 1,
        "command": "review-channel",
        "project_id": project_id_for_repo(repo_root),
        "timestamp": latest_timestamp,
        "ok": not errors,
        "review": {
            "plan_id": latest_plan_id,
            "controller_run_id": latest_controller_run_id,
            "session_id": latest_session_id,
            "surface_mode": "event-backed",
            "active_lane": "review",
            "refresh_seq": len(events),
            "review_channel_path": display_path(review_channel_path, repo_root=repo_root),
        },
        "agents": _build_agents(packet_rows, latest_timestamp),
        "packets": packet_rows,
        "queue": _build_queue_summary(pending_counts, stale_packet_count),
        "runtime": runtime,
        "warnings": warnings,
        "errors": errors,
    }
    return review_state, registry


def filter_inbox_packets(
    review_state: dict[str, object],
    *,
    target: str | None = None,
    status: str | None = None,
    limit: int | None = None,
) -> list[dict[str, object]]:
    """Filter the reduced packet list into one target/status inbox view."""
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return []
    filtered = [
        packet
        for packet in packets
        if isinstance(packet, dict)
        and (not target or packet.get("to_agent") == target)
        and (not status or packet.get("status") == status)
    ]
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


def _record_provider_packet_state(
    provider_state: dict[str, dict[str, object]],
    event: dict[str, object],
    packet_id: str,
) -> None:
    provider_from = str(event.get("from_agent") or "").strip()
    provider_to = str(event.get("to_agent") or "").strip()
    if provider_from in provider_state:
        provider_state[provider_from]["last_packet_seen"] = packet_id
    if provider_to in provider_state:
        provider_state[provider_to]["last_packet_seen"] = packet_id
    if str(event.get("event_type") or "").strip() == "packet_applied":
        actor = str((event.get("metadata") or {}).get("actor") or "").strip()
        if actor in provider_state:
            provider_state[actor]["last_packet_applied"] = packet_id


def _summarize_packets(
    packets_by_id: dict[str, ReviewPacketRow],
) -> tuple[list[dict[str, object]], dict[str, int], int]:
    now_utc = datetime.now(timezone.utc)
    stale_packet_count = 0
    packet_rows: list[dict[str, object]] = []
    pending_counts = {"codex": 0, "claude": 0, "cursor": 0, "operator": 0}
    for packet in sorted(
        packets_by_id.values(),
        key=lambda item: str(item.get("_sort_timestamp") or ""),
        reverse=True,
    ):
        expires_at = parse_utc(packet.get("expires_at_utc"))
        if packet.get("status") == "pending":
            target = str(packet.get("to_agent") or "").strip()
            if target in pending_counts:
                pending_counts[target] += 1
            if expires_at is not None and expires_at <= now_utc:
                stale_packet_count += 1
        clean_packet = dict(packet)
        clean_packet.pop("_sort_timestamp", None)
        packet_rows.append(clean_packet)
    return packet_rows, pending_counts, stale_packet_count


def _hydrate_provider_job_state(
    provider_state: dict[str, dict[str, object]],
    pending_counts: dict[str, int],
) -> None:
    for provider in provider_state:
        role = role_for_provider(provider)
        active_label = _ROLE_JOB_STATE.get(role.value, "waiting")
        provider_state[provider].setdefault(
            "job_state",
            active_label if pending_counts.get(provider, 0) else "assigned",
        )
    for provider, count in pending_counts.items():
        if count and provider in provider_state:
            provider_state[provider]["waiting_on"] = provider


def _build_agents(
    packets: list[dict[str, object]],
    latest_timestamp: str,
) -> list[ReviewAgentRow]:
    pending_targets = {
        str(packet.get("to_agent") or "").strip()
        for packet in packets
        if packet.get("status") == "pending"
    }
    agent_ids = ("codex", "claude", "cursor", "operator")
    latest_packet_by_target = {
        agent_id: next(
            (
                packet
                for packet in packets
                if packet.get("to_agent") == agent_id
                or packet.get("from_agent") == agent_id
            ),
            None,
        )
        for agent_id in agent_ids
    }
    return [
        _agent_row(
            agent_id=agent_id,
            display_name=agent_id.title(),
            role=str(role_for_provider(agent_id)),
            pending=bool(agent_id in pending_targets),
            latest_packet=latest_packet_by_target[agent_id],
            latest_timestamp=latest_timestamp,
        )
        for agent_id in agent_ids
    ]


def _agent_row(
    *,
    agent_id: str,
    display_name: str,
    role: str,
    pending: bool,
    latest_packet: ReviewPacketRow | dict[str, object] | None,
    latest_timestamp: str,
) -> ReviewAgentRow:
    role_label = str(role_for_provider(agent_id))
    active_label = _ROLE_JOB_STATE.get(role_label, "waiting")
    if pending:
        job_status = active_label
    elif latest_packet is not None:
        job_status = "done"
    else:
        job_status = "waiting"
    return ReviewAgentRow(
        agent_id=agent_id,
        display_name=display_name,
        role=role,
        status="active" if pending else "idle",
        capabilities=_agent_capabilities(agent_id),
        lane=agent_id,
        last_seen_utc=latest_timestamp if latest_packet is not None else None,
        assigned_job=latest_packet.get("summary") if latest_packet else None,
        job_status=job_status,
        waiting_on=(
            latest_packet.get("from_agent")
            if latest_packet is not None and latest_packet.get("to_agent") == agent_id
            else None
        ),
        last_packet_id_seen=latest_packet.get("packet_id") if latest_packet else None,
        last_packet_id_applied=(
            latest_packet.get("packet_id")
            if latest_packet is not None and latest_packet.get("status") == "applied"
            else None
        ),
        script_profile="review-channel-event",
    )


def _packet_from_event(event: dict[str, object]) -> ReviewPacketRow:
    return ReviewPacketRow(
        packet_id=event.get("packet_id"),
        trace_id=event.get("trace_id"),
        latest_event_id=event.get("event_id"),
        from_agent=event.get("from_agent"),
        to_agent=event.get("to_agent"),
        kind=event.get("kind"),
        summary=event.get("summary"),
        body=event.get("body"),
        evidence_refs=list(event.get("evidence_refs") or []),
        context_pack_refs=normalize_context_pack_refs(
            event.get("context_pack_refs")
        ),
        confidence=float(event.get("confidence") or 0.0),
        requested_action=event.get("requested_action"),
        policy_hint=event.get("policy_hint"),
        approval_required=bool(event.get("approval_required")),
        status=event.get("status"),
        acked_by=None,
        acked_at_utc=None,
        applied_at_utc=None,
        expires_at_utc=event.get("expires_at_utc"),
        _sort_timestamp=event.get("timestamp_utc"),
    )


def _apply_transition(
    packet: dict[str, object],
    event: dict[str, object],
) -> dict[str, object]:
    next_packet = dict(packet)
    event_type = str(event.get("event_type") or "").strip()
    next_packet["latest_event_id"] = event.get("event_id")
    next_packet["_sort_timestamp"] = event.get("timestamp_utc")
    next_packet["status"] = event.get("status")
    if event.get("context_pack_refs") is not None or packet.get("context_pack_refs"):
        next_packet["context_pack_refs"] = normalize_context_pack_refs(
            event.get("context_pack_refs") or packet.get("context_pack_refs")
        )
    actor = str((event.get("metadata") or {}).get("actor") or "").strip()
    if event_type == "packet_acked":
        next_packet["acked_by"] = actor or packet.get("to_agent")
        next_packet["acked_at_utc"] = event.get("timestamp_utc")
    if event_type == "packet_applied":
        next_packet["applied_at_utc"] = event.get("timestamp_utc")
    return next_packet


def _load_lane_assignments(review_channel_path: Path) -> list:
    return load_lane_assignments(review_channel_path)
