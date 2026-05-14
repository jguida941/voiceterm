"""Typed event emitter for participant liveness TTL expiry.

Wires the existing liveness detection (PID probe + `_pid_is_alive` +
`SessionLivenessEvidence` + `detached_exit` auto-set) to the append-only
event log so dead participants become discrete, auditable transitions
instead of values inferred only at read time. Downstream reducers can
then track which sessions have crossed the liveness TTL without
re-running process probes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

from ..runtime.derived_state_invalidation import (
    REVIEW_CHANNEL_DERIVED_STATE_CONSUMERS,
    SESSION_LIVENESS_INVALIDATION_SOURCE,
    derived_state_invalidation_payload,
)
from ..time_utils import utc_timestamp
from .session_probe import ConductorSessionRecord, load_conductor_sessions

# Participant liveness events are reducer-visible but not packet-shaped;
# the reducer short-circuits them the same way it short-circuits daemon
# events so they do not trip the missing-packet_id contract.
SESSION_LIVENESS_EVENT_TYPES = frozenset({"participant_liveness_expired"})


@dataclass(frozen=True)
class ParticipantLivenessExpiredEvent:
    """Typed payload for one participant_liveness_expired event row."""

    event_id: str
    timestamp_utc: str
    provider: str
    role: str
    session_name: str
    metadata_path: str
    age_seconds: int | None
    live_reason: str
    script_probe_state: str
    terminal_window_state: str
    launch_authority_state: str
    idempotency_key: str
    derived_state_invalidation: dict[str, object] = field(default_factory=dict)
    schema_version: int = 1
    event_type: str = "participant_liveness_expired"
    source: str = "review_channel"
    metadata: dict[str, object] = field(default_factory=dict)

    def to_event(self) -> dict[str, object]:
        """Serialize into the append-only event row contract."""
        return asdict(self)


def emit_participant_liveness_expired(
    *,
    repo_root: Path,
    session_output_root: Path,
) -> list[dict[str, object]]:
    """Emit one ``participant_liveness_expired`` event per dead session.

    Returns the list of newly-written events. Idempotency key includes
    the session name plus the observed age bucket so repeated status
    polls do not re-emit the same expiry. Sessions that probe as live,
    or that lack enough metadata to be addressable, are skipped.
    """
    from .event_store import (
        append_event,
        load_events,
        resolve_artifact_paths,
    )

    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    records = load_conductor_sessions(session_output_root=session_output_root)
    dead = [record for record in records if not record.live and record.session_name]
    if not dead:
        return []
    event_log_path = Path(artifact_paths.event_log_path)
    existing_events = load_events(event_log_path) if event_log_path.exists() else []
    written: list[dict[str, object]] = []
    for record in dead:
        event = _build_liveness_expired_event(
            record=record,
            existing_events=existing_events,
        )
        try:
            new_event = append_event(
                event_log_path,
                event,
                existing_events=existing_events,
            )
        except ValueError:
            # Duplicate idempotency_key: a prior status tick already
            # recorded this transition. Skip without noise.
            continue
        written.append(new_event)
        existing_events.append(new_event)
    return written


def emit_status_tick_participant_liveness_events(
    *,
    repo_root: Path,
    session_output_root: Path,
) -> list[dict[str, object]]:
    """Emit liveness-expiry events for one explicit refresh tick."""
    try:
        return emit_participant_liveness_expired(
            repo_root=repo_root,
            session_output_root=session_output_root,
        )
    except (OSError, ValueError):
        return []


def summarize_participant_liveness_events(
    events: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Project newly emitted expiry rows into the bridge-liveness summary."""
    return [
        {
            "provider": event.get("provider"),
            "session_name": event.get("session_name"),
            "live_reason": event.get("live_reason"),
            "timestamp_utc": event.get("timestamp_utc"),
        }
        for event in events
    ]


def _build_liveness_expired_event(
    *,
    record: ConductorSessionRecord,
    existing_events: list[dict[str, object]],
) -> dict[str, object]:
    from .event_store import idempotency_key, next_event_id

    payload = ParticipantLivenessExpiredEvent(
        event_id=next_event_id(existing_events),
        timestamp_utc=utc_timestamp(),
        provider=record.provider,
        role=record.role,
        session_name=record.session_name,
        metadata_path=record.metadata_path,
        age_seconds=record.age_seconds,
        live_reason=record.live_reason,
        script_probe_state=record.script_probe_state,
        terminal_window_state=record.terminal_window_state,
        launch_authority_state=record.launch_authority_state,
        idempotency_key=idempotency_key(
            "participant_liveness_expired",
            record.provider,
            record.session_name,
            record.live_reason,
            record.age_seconds,
        ),
        derived_state_invalidation=derived_state_invalidation_payload(
            source=SESSION_LIVENESS_INVALIDATION_SOURCE,
            producer_id="review_channel.session_liveness",
            producer_kind="review_channel_event",
            invalidated_consumers=REVIEW_CHANNEL_DERIVED_STATE_CONSUMERS,
            next_consumer_action="reload_session_liveness_before_work_decision",
            source_event_id=next_event_id(existing_events),
            source_ref=f"session:{record.provider}:{record.session_name}",
            status=record.live_reason,
        ),
    )
    return payload.to_event()


__all__ = [
    "SESSION_LIVENESS_EVENT_TYPES",
    "emit_participant_liveness_expired",
    "emit_status_tick_participant_liveness_events",
    "summarize_participant_liveness_events",
]
