"""Peer agent-mind context for the typed `/develop` controller."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from ...runtime.agent_mind_projection_read import (
    agent_mind_latest_age_seconds,
    read_agent_mind_projection,
)
from .models import DevelopmentPeerMindEvent, DevelopmentPeerMindSnapshot
from .peer_mind_commands import agent_mind_command, suggested_peer_mind_command
from .peer_mind_sessions import agent_loop_rows, append_provider, provider_session_counts
from .peer_mind_wake import peer_mind_wake_hint

_FRESH_SECONDS = 300
_DEFAULT_PROVIDER_IDS = ("codex", "claude")


def peer_mind_snapshots(
    repo_root: Path,
    review_state: Mapping[str, object],
    *,
    actor: str,
    limit: int = 4,
) -> tuple[DevelopmentPeerMindSnapshot, ...]:
    """Return recent peer-mind projections as auxiliary `/develop` context."""
    provider_ids = _provider_ids(review_state, actor=actor)
    session_counts = provider_session_counts(review_state)
    return tuple(
        _snapshot_for_provider(
            repo_root,
            provider=provider,
            actor=actor,
            known_session_count=session_counts.get(provider, 0),
        )
        for provider in provider_ids[: max(1, limit)]
    )


def _snapshot_for_provider(
    repo_root: Path,
    *,
    provider: str,
    actor: str,
    known_session_count: int,
) -> DevelopmentPeerMindSnapshot:
    projection = read_agent_mind_projection(repo_root, provider=provider)
    if not projection:
        return DevelopmentPeerMindSnapshot(
            provider=provider,
            known_session_count=known_session_count,
            attention_hint="refresh_agent_mind",
            wake_hint="refresh_agent_mind",
            suggested_command=agent_mind_command(provider),
        )
    events = tuple(_event_from_payload(event) for event in _event_payloads(projection))
    age_seconds = _age_seconds(projection)
    confidence = _confidence(age_seconds)
    latest_summary = _latest_summary(events)
    attention_hint = peer_mind_wake_hint(
        confidence=confidence,
        latest_summary=latest_summary,
        events=events,
    )
    return DevelopmentPeerMindSnapshot(
        provider=provider,
        session_id=_text(projection.get("session_id")),
        known_session_count=max(known_session_count, 1),
        covered_session_count=1,
        omitted_session_count=max(known_session_count - 1, 0),
        event_count=_int(projection.get("event_count")),
        age_seconds=age_seconds,
        confidence=confidence,
        attention_hint=attention_hint,
        wake_hint=attention_hint,
        suggested_command=suggested_peer_mind_command(
            provider=provider,
            actor=actor,
            wake_hint=attention_hint,
        ),
        latest_summary=latest_summary,
        events=events,
    )


def _provider_ids(
    review_state: Mapping[str, object],
    *,
    actor: str,
) -> tuple[str, ...]:
    providers: list[str] = []
    for provider in _DEFAULT_PROVIDER_IDS:
        append_provider(providers, provider)
    work_board = _mapping(review_state.get("agent_work_board"))
    rows = work_board.get("rows")
    if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)):
        for row in rows:
            if isinstance(row, Mapping):
                append_provider(providers, _text(row.get("provider")))
                append_provider(providers, _text(row.get("actor_id")))
    agent_sync = _mapping(review_state.get("agent_sync"))
    agents = _mapping(agent_sync.get("agents"))
    for provider in agents:
        append_provider(providers, str(provider))
    for row in agent_loop_rows(review_state):
        append_provider(providers, _text(row.get("actor_id")))
    return tuple(sorted(providers, key=lambda item: (item == actor, item)))


def _event_payloads(
    projection: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    events = projection.get("latest_events")
    if not isinstance(events, Sequence) or isinstance(events, (str, bytes)):
        events = projection.get("events")
    if not isinstance(events, Sequence) or isinstance(events, (str, bytes)):
        return ()
    payloads = [event for event in events if isinstance(event, Mapping)]
    return tuple(payloads[-3:])


def _event_from_payload(event: Mapping[str, object]) -> DevelopmentPeerMindEvent:
    return DevelopmentPeerMindEvent(
        timestamp=_text(event.get("timestamp")),
        event_type=_text(event.get("event_type") or event.get("raw_event_kind")),
        summary=_text(event.get("summary")),
        tool_name=_text(event.get("tool_name")),
        is_error=bool(event.get("is_error")),
        is_escalation=bool(event.get("is_escalation")),
    )


def _age_seconds(projection: Mapping[str, object]) -> int:
    value = agent_mind_latest_age_seconds(projection)
    if value is None:
        return -1
    return int(value)


def _confidence(age_seconds: int) -> str:
    if age_seconds < 0:
        return "missing_auxiliary"
    if age_seconds <= _FRESH_SECONDS:
        return "fresh_auxiliary"
    return "stale_auxiliary"


def _latest_summary(events: tuple[DevelopmentPeerMindEvent, ...]) -> str:
    for event in reversed(events):
        if event.summary:
            return event.summary
    return ""


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


def _int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


__all__ = ["peer_mind_snapshots"]
