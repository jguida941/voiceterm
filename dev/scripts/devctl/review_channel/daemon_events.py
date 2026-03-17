"""Daemon lifecycle event writers for review-channel runtime truth."""

from __future__ import annotations

import secrets
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .core import project_id_for_repo
from .daemon_reducer import DAEMON_EVENT_TYPES, KNOWN_DAEMON_KINDS
from .event_store import (
    DEFAULT_REVIEW_CHANNEL_PLAN_ID,
    DEFAULT_REVIEW_CHANNEL_SESSION_ID,
    ReviewChannelArtifactPaths,
    append_event,
    idempotency_key,
    load_events,
    next_event_id,
)
from ..time_utils import utc_timestamp

DAEMON_TRACE_PREFIX = "daemon"


@dataclass(frozen=True)
class DaemonEventContext:
    """Inputs that stay stable for one daemon lifecycle emitter."""

    repo_root: Path
    artifact_paths: ReviewChannelArtifactPaths | object
    daemon_kind: str
    pid: int


@dataclass(frozen=True)
class DaemonLifecycleEventRequest:
    """One lifecycle event append request."""

    event_type: str
    reviewer_mode: str = ""
    snapshots_emitted: int | None = None
    stop_reason: str = ""
    timestamp_utc: str | None = None


@dataclass(frozen=True)
class DaemonLifecycleEventRow:
    """Serialized daemon lifecycle event payload."""

    schema_version: int
    event_id: str
    session_id: str
    project_id: str
    trace_id: str
    timestamp_utc: str
    source: str
    plan_id: str
    controller_run_id: str | None
    event_type: str
    daemon_kind: str
    pid: int
    idempotency_key: str
    nonce: str
    reviewer_mode: str = ""
    snapshots_emitted: int | None = None
    stop_reason: str = ""
    metadata: dict[str, object] = field(default_factory=dict)


def append_daemon_lifecycle_event(
    context: DaemonEventContext,
    request: DaemonLifecycleEventRequest,
) -> dict[str, object] | None:
    """Best-effort lifecycle event append for daemon-backed review runtime."""
    if not isinstance(context.artifact_paths, ReviewChannelArtifactPaths):
        return None
    _validate_daemon_event_context(context, request)
    event_timestamp = request.timestamp_utc or utc_timestamp()
    try:
        existing_events = load_events(Path(context.artifact_paths.event_log_path))
    except (OSError, ValueError):
        # Bridge-backed lifecycle truth remains the active authority while the
        # daemon-event reducer is additive, so logging failures stay fail-open.
        return None
    event = _build_daemon_event_row(
        context=context,
        request=request,
        existing_events=existing_events,
        event_timestamp=event_timestamp,
    )
    try:
        append_event(
            Path(context.artifact_paths.event_log_path),
            event,
            existing_events=existing_events,
        )
    except (OSError, ValueError):
        return None
    return event


def append_daemon_started(
    context: DaemonEventContext,
    *,
    reviewer_mode: str,
    timestamp_utc: str,
) -> dict[str, object] | None:
    """Append a daemon_started lifecycle row."""
    return append_daemon_lifecycle_event(
        context,
        DaemonLifecycleEventRequest(
            event_type="daemon_started",
            reviewer_mode=reviewer_mode,
            timestamp_utc=timestamp_utc,
        ),
    )


def append_daemon_heartbeat(
    context: DaemonEventContext,
    *,
    reviewer_mode: str,
    snapshots_emitted: int,
    timestamp_utc: str,
) -> dict[str, object] | None:
    """Append a daemon_heartbeat lifecycle row."""
    return append_daemon_lifecycle_event(
        context,
        DaemonLifecycleEventRequest(
            event_type="daemon_heartbeat",
            reviewer_mode=reviewer_mode,
            snapshots_emitted=snapshots_emitted,
            timestamp_utc=timestamp_utc,
        ),
    )


def append_daemon_stopped(
    context: DaemonEventContext,
    *,
    reviewer_mode: str,
    snapshots_emitted: int,
    stop_reason: str,
) -> dict[str, object] | None:
    """Append a daemon_stopped lifecycle row."""
    return append_daemon_lifecycle_event(
        context,
        DaemonLifecycleEventRequest(
            event_type="daemon_stopped",
            reviewer_mode=reviewer_mode,
            snapshots_emitted=snapshots_emitted,
            stop_reason=stop_reason,
        ),
    )


def _validate_daemon_event_context(
    context: DaemonEventContext,
    request: DaemonLifecycleEventRequest,
) -> None:
    if context.daemon_kind not in KNOWN_DAEMON_KINDS:
        raise ValueError(f"Unsupported daemon kind: {context.daemon_kind}")
    if request.event_type not in DAEMON_EVENT_TYPES:
        raise ValueError(f"Unsupported daemon event type: {request.event_type}")
    if context.pid <= 0:
        raise ValueError(
            f"Daemon lifecycle events require a positive pid: {context.pid}"
        )


def _build_daemon_event_row(
    *,
    context: DaemonEventContext,
    request: DaemonLifecycleEventRequest,
    existing_events: list[dict[str, object]],
    event_timestamp: str,
) -> dict[str, object]:
    event = asdict(
        DaemonLifecycleEventRow(
            schema_version=1,
            event_id=next_event_id(existing_events),
            session_id=DEFAULT_REVIEW_CHANNEL_SESSION_ID,
            project_id=project_id_for_repo(context.repo_root),
            trace_id=f"{DAEMON_TRACE_PREFIX}_{context.daemon_kind}_{context.pid}",
            timestamp_utc=event_timestamp,
            source="review_channel",
            plan_id=DEFAULT_REVIEW_CHANNEL_PLAN_ID,
            controller_run_id=None,
            event_type=request.event_type,
            daemon_kind=context.daemon_kind,
            pid=context.pid,
            idempotency_key=_daemon_event_idempotency_key(
                context=context,
                request=request,
                event_timestamp=event_timestamp,
            ),
            nonce=secrets.token_hex(12),
            reviewer_mode=request.reviewer_mode,
            snapshots_emitted=request.snapshots_emitted,
            stop_reason=request.stop_reason,
        )
    )
    if not request.reviewer_mode:
        event.pop("reviewer_mode")
    if request.snapshots_emitted is None:
        event.pop("snapshots_emitted")
    if not request.stop_reason:
        event.pop("stop_reason")
    return event


def _daemon_event_idempotency_key(
    *,
    context: DaemonEventContext,
    request: DaemonLifecycleEventRequest,
    event_timestamp: str,
) -> str:
    if request.event_type == "daemon_heartbeat":
        return idempotency_key(
            request.event_type,
            context.daemon_kind,
            context.pid,
            request.snapshots_emitted or 0,
        )
    if request.event_type == "daemon_stopped":
        return idempotency_key(
            request.event_type,
            context.daemon_kind,
            context.pid,
            request.snapshots_emitted or 0,
            request.stop_reason or "unknown",
        )
    return idempotency_key(
        request.event_type,
        context.daemon_kind,
        context.pid,
        request.reviewer_mode or "unknown",
        event_timestamp,
    )
