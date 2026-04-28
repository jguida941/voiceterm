"""Event-backed agent-session outcome receipts for review-channel state."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from ..runtime.agent_session_outcome import (
    AGENT_SESSION_OUTCOME_COMPLETED_HANDOFF,
    AGENT_SESSION_OUTCOME_CONTRACT_ID,
    AGENT_SESSION_OUTCOME_SCHEMA_VERSION,
    AgentSessionOutcomeState,
    agent_session_outcome_from_mapping,
    latest_agent_session_outcome,
)
from .session_probe import ConductorSessionRecord, load_conductor_sessions

if TYPE_CHECKING:
    from .event_store import ReviewChannelArtifactPaths

AGENT_SESSION_OUTCOME_EVENT_TYPES = frozenset({"agent_session_outcome"})
_COMPLETED_HANDOFF_REASON = (
    "stage_commit_pipeline_posted_with_full_guard_bundle_evidence"
)


def append_agent_session_outcome_for_packet(
    *,
    repo_root: Path,
    artifact_paths: ReviewChannelArtifactPaths,
    packet_event: Mapping[str, object],
    existing_events: Sequence[dict[str, object]],
) -> dict[str, object] | None:
    """Append a typed completed-handoff outcome for qualifying stage packets."""
    outcome_event = completed_handoff_outcome_event_from_packet(
        artifact_paths=artifact_paths,
        packet_event=packet_event,
    )
    if outcome_event is None:
        return None
    del repo_root
    from .event_store import append_event

    return append_event(
        Path(artifact_paths.event_log_path),
        outcome_event,
        existing_events=list(existing_events),
    )


def completed_handoff_outcome_event_from_packet(
    *,
    artifact_paths: ReviewChannelArtifactPaths,
    packet_event: Mapping[str, object],
) -> dict[str, object] | None:
    if not _packet_emits_completed_handoff(packet_event):
        return None

    provider = _text(packet_event.get("from_agent")).lower()
    metadata = _load_session_metadata(
        Path(artifact_paths.projections_root),
        provider=provider,
    )
    timestamp = _text(packet_event.get("timestamp_utc"))

    outcome = AgentSessionOutcomeState(
        schema_version=AGENT_SESSION_OUTCOME_SCHEMA_VERSION,
        contract_id=AGENT_SESSION_OUTCOME_CONTRACT_ID,
        outcome=AGENT_SESSION_OUTCOME_COMPLETED_HANDOFF,
        reason=_COMPLETED_HANDOFF_REASON,
        provider=provider,
        session_actor_id=provider,
        session_actor_role=_metadata_text(metadata, "role"),
        session_id=_text(packet_event.get("session_id")),
        session_name=(
            _metadata_text(metadata, "session_name") or f"{provider}-conductor"
        ),
        observed_at_utc=timestamp,
        finished_at_utc=timestamp,
        source="review_channel_packet",
        source_event_id=_text(packet_event.get("event_id")),
        handoff_packet_id=_text(packet_event.get("packet_id")),
        handoff_requested_action=_text(packet_event.get("requested_action")),
        target_kind=_text(packet_event.get("target_kind")),
        target_ref=_text(packet_event.get("target_ref")),
        target_revision=_text(packet_event.get("target_revision")),
        metadata_path=_metadata_text(metadata, "_metadata_path"),
        log_path=_metadata_text(metadata, "log_path"),
        workspace_root=_metadata_text(metadata, "workspace_root"),
        prepared_at_utc=_metadata_text(metadata, "prepared_at"),
        prepared_session_token=_metadata_text(metadata, "prepared_session_token"),
        prepared_head_sha=_metadata_text(metadata, "prepared_head_sha"),
        prepared_instruction_revision=_metadata_text(
            metadata,
            "prepared_instruction_revision",
        ),
    )

    event = asdict(outcome)
    event["event_type"] = "agent_session_outcome"
    event["timestamp_utc"] = timestamp
    event["source"] = "review_channel"
    event["plan_id"] = _text(packet_event.get("plan_id"))
    event["project_id"] = _text(packet_event.get("project_id"))
    event["controller_run_id"] = packet_event.get("controller_run_id")
    event["metadata"] = {
        "source_contract": "ReviewPacket",
        "source_packet_event_id": _text(packet_event.get("event_id")),
    }
    return event


def load_agent_session_outcomes(
    *,
    events_path: Path,
) -> tuple[AgentSessionOutcomeState, ...]:
    from .event_store import load_events

    events = load_events(events_path)
    return agent_session_outcomes_from_events(events)


def agent_session_outcomes_from_events(
    events: Iterable[Mapping[str, object]],
) -> tuple[AgentSessionOutcomeState, ...]:
    rows: list[AgentSessionOutcomeState] = []
    for event in events:
        if _text(event.get("event_type")) not in AGENT_SESSION_OUTCOME_EVENT_TYPES:
            continue
        outcome = agent_session_outcome_from_mapping(event)
        if outcome is not None:
            rows.append(outcome)
    return tuple(rows)


def latest_current_completed_handoff_outcome(
    *,
    repo_root: Path,
) -> AgentSessionOutcomeState | None:
    """Return the latest completed handoff bound to current session metadata."""
    from .event_store import resolve_artifact_paths

    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    outcomes = load_agent_session_outcomes(
        events_path=Path(artifact_paths.event_log_path)
    )
    latest = latest_agent_session_outcome(
        outcomes,
        outcome=AGENT_SESSION_OUTCOME_COMPLETED_HANDOFF,
    )
    if latest is None:
        return None

    sessions = load_conductor_sessions(
        session_output_root=Path(artifact_paths.projections_root)
    )
    if not _outcome_matches_current_session(latest, sessions):
        return None

    return latest


def _packet_emits_completed_handoff(packet_event: Mapping[str, object]) -> bool:
    from .packet_contract import (
        ACTION_REQUEST_PACKET_KIND,
        STAGE_PIPELINE_ACTION_REQUEST_ACTIONS,
    )

    return (
        _text(packet_event.get("event_type")) == "packet_posted"
        and _text(packet_event.get("kind")) == ACTION_REQUEST_PACKET_KIND
        and _text(packet_event.get("requested_action"))
        in STAGE_PIPELINE_ACTION_REQUEST_ACTIONS
        and bool(_text(packet_event.get("full_guard_bundle_evidence")))
        and bool(_text(packet_event.get("from_agent")))
    )


def _load_session_metadata(
    projections_root: Path,
    *,
    provider: str,
) -> dict[str, object]:
    path = projections_root / "sessions" / f"{provider}-conductor.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    payload = dict(payload)
    payload["_metadata_path"] = str(path)
    return payload


def _outcome_matches_current_session(
    outcome: AgentSessionOutcomeState,
    sessions: Sequence[ConductorSessionRecord],
) -> bool:
    for session in sessions or ():
        provider = _text(session.provider).lower()
        if provider != outcome.provider.lower():
            continue

        session_name = _text(session.session_name)
        if (
            outcome.session_name
            and session_name
            and outcome.session_name != session_name
        ):
            continue

        if not _outcome_not_before_session(outcome, session):
            continue

        token = _text(session.prepared_session_token)
        if outcome.prepared_session_token and token:
            return outcome.prepared_session_token == token

        prepared_at = _text(session.prepared_at)
        if outcome.prepared_at_utc and prepared_at:
            return outcome.prepared_at_utc == prepared_at

        metadata_path = _text(session.metadata_path)
        if outcome.metadata_path and metadata_path:
            return _same_path(outcome.metadata_path, metadata_path)

    return False


def _outcome_not_before_session(
    outcome: AgentSessionOutcomeState,
    session: ConductorSessionRecord,
) -> bool:
    prepared_at = _parse_utc(_text(session.prepared_at))
    finished_at = _parse_utc(outcome.finished_at_utc or outcome.observed_at_utc)

    if prepared_at is None or finished_at is None:
        return True

    return finished_at >= prepared_at


def _same_path(left: str, right: str) -> bool:
    try:
        return Path(left).resolve() == Path(right).resolve()
    except OSError:
        return left == right


def _parse_utc(value: str) -> datetime | None:
    text = value.strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _metadata_text(payload: Mapping[str, object], key: str) -> str:
    return _text(payload.get(key))


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


__all__ = [
    "AGENT_SESSION_OUTCOME_EVENT_TYPES",
    "agent_session_outcomes_from_events",
    "append_agent_session_outcome_for_packet",
    "completed_handoff_outcome_event_from_packet",
    "latest_current_completed_handoff_outcome",
    "load_agent_session_outcomes",
]
