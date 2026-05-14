"""Derived session-status projection over existing runtime evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import TypeAlias, cast

from .agent_mind_slice import AgentMindSlice
from .agent_session_outcome import (
    AGENT_SESSION_OUTCOME_COMPLETED_HANDOFF,
    AGENT_SESSION_OUTCOME_PROCESS_DIED,
    AGENT_SESSION_OUTCOME_UNRESOLVED,
    AgentSessionOutcomeState,
    agent_session_outcome_from_mapping,
)
from .review_state_collaboration_models import (
    CollaborationParticipantState,
    CollaborationSessionState,
)
from .review_state_models import RecoveryAssessmentState, ReviewBridgeState
from .session_activity_log import SessionActivityEntry
from .session_liveness_signal import SessionLivenessSignal, SessionLivenessState

SESSION_STATUS_PROJECTION_CONTRACT_ID = "SessionStatusProjection"
SESSION_STATUS_PROJECTION_SCHEMA_VERSION = 1

SESSION_STATUS_TASK_COMPLETED = "task_completed"
SESSION_STATUS_MID_TASK_DEATH = "mid_task_death"
SESSION_STATUS_RUNNING = "running"
SESSION_STATUS_DETACHED_RUNTIME_ONLY = "detached_runtime_only"
SESSION_STATUS_UNKNOWN = "unknown"

_LIVE_LIVENESS_STATES = frozenset({"alive", "degraded"})
_DEAD_LIVENESS_STATES = frozenset({"dead"})
_DETACHED_LIVENESS_STATES = frozenset({"detached_runtime_only"})
_SESSION_LIVENESS_STATES = (
    _LIVE_LIVENESS_STATES | _DEAD_LIVENESS_STATES | _DETACHED_LIVENESS_STATES
)

_StatusParticipant: TypeAlias = CollaborationParticipantState | Mapping[str, object]
_StatusOutcome: TypeAlias = AgentSessionOutcomeState | Mapping[str, object]
_StatusLiveness: TypeAlias = SessionLivenessSignal | Mapping[str, object]
_StatusAgentMind: TypeAlias = AgentMindSlice | Mapping[str, object]


@dataclass(frozen=True, slots=True)
class SessionStatusRow:
    """One provider/session answer for completion versus mid-task death."""

    provider: str
    role: str
    status: str
    answer: str
    reason: str
    session_id: str = ""
    session_name: str = ""
    process_live: bool | None = None
    liveness_state: str = ""
    latest_task_complete_at: str = ""
    agent_mind_generated_at_utc: str = ""
    agent_mind_session_matches_current: bool | None = None
    agent_mind_stale: bool | None = None
    latest_session_outcome: str = ""
    latest_session_outcome_reason: str = ""
    latest_session_outcome_at_utc: str = ""
    head_sha: str = ""
    worktree_hash: str = ""
    worktree_dirty: bool | None = None
    session_path: str = ""
    log_path: str = ""
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["evidence_refs"] = list(self.evidence_refs)
        return {key: value for key, value in payload.items() if value is not None}


@dataclass(frozen=True, slots=True)
class SessionStatusProjection:
    """Single read model answering whether sessions completed or died."""

    generated_at_utc: str
    status: str
    answer: str
    rows: tuple[SessionStatusRow, ...] = ()
    head_sha: str = ""
    worktree_hash: str = ""
    worktree_dirty: bool | None = None
    evidence_refs: tuple[str, ...] = ()
    schema_version: int = SESSION_STATUS_PROJECTION_SCHEMA_VERSION
    contract_id: str = SESSION_STATUS_PROJECTION_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["rows"] = [row.to_dict() for row in self.rows]
        payload["evidence_refs"] = list(self.evidence_refs)
        return {key: value for key, value in payload.items() if value is not None}


def build_session_status_projection(
    *,
    generated_at_utc: str,
    collaboration: CollaborationSessionState | Mapping[str, object] | None = None,
    bridge_liveness: ReviewBridgeState | Mapping[str, object] | None = None,
    agent_minds: Mapping[str, AgentMindSlice | Mapping[str, object]] | None = None,
    recovery_assessment: RecoveryAssessmentState | None = None,
    session_activity_entries: Sequence[SessionActivityEntry] | None = None,
    head_sha: str = "",
    worktree_hash: str = "",
    worktree_dirty: bool | None = None,
) -> SessionStatusProjection:
    """Build the derived projection from liveness, outcome, and mind evidence."""
    push_enforcement = _mapping(_field_value(bridge_liveness, "push_enforcement"))
    resolved_head = head_sha or _text(push_enforcement.get("current_head_commit"))
    resolved_worktree_hash = (
        worktree_hash
        or _field_text(bridge_liveness, "last_worktree_hash")
        or _text(push_enforcement.get("current_worktree_identity"))
    )
    resolved_worktree_dirty = (
        worktree_dirty
        if worktree_dirty is not None
        else _optional_bool(push_enforcement, "worktree_dirty")
    )

    participants = _participants(collaboration)
    liveness_by_provider = _liveness_by_provider(bridge_liveness)
    outcomes_by_provider = _latest_outcomes_by_provider(collaboration)
    agent_minds_by_provider = _agent_minds_by_provider(agent_minds or {})
    activity_by_provider = _activity_entries_by_provider(session_activity_entries or ())
    providers = _ordered_unique(
        [
            *participants.keys(),
            *liveness_by_provider.keys(),
            *outcomes_by_provider.keys(),
            *agent_minds_by_provider.keys(),
            *activity_by_provider.keys(),
        ]
    )
    rows = tuple(
        _build_row(
            provider=provider,
            participant=participants.get(provider, {}),
            liveness=liveness_by_provider.get(provider, {}),
            outcome=outcomes_by_provider.get(provider, {}),
            agent_mind=agent_minds_by_provider.get(provider, {}),
            activity_entries=activity_by_provider.get(provider, ()),
            head_sha=resolved_head,
            worktree_hash=resolved_worktree_hash,
            worktree_dirty=resolved_worktree_dirty,
        )
        for provider in providers
    )
    status, answer = _overall_status(rows)
    return SessionStatusProjection(
        generated_at_utc=generated_at_utc,
        status=status,
        answer=answer,
        rows=rows,
        head_sha=resolved_head,
        worktree_hash=resolved_worktree_hash,
        worktree_dirty=resolved_worktree_dirty,
        evidence_refs=(
            *_projection_evidence(rows),
            *_recovery_assessment_evidence(recovery_assessment),
        ),
    )


def session_status_projection_from_mapping(
    value: object,
) -> dict[str, object]:
    """Return a normalized projection mapping for ReviewState addenda."""
    mapping = _mapping(value)
    if not mapping:
        return {}
    rows = [
        dict(row)
        for row in _sequence(mapping.get("rows"))
        if isinstance(row, Mapping)
    ]
    result = dict(mapping)
    result["contract_id"] = (
        _text(result.get("contract_id")) or SESSION_STATUS_PROJECTION_CONTRACT_ID
    )
    result["schema_version"] = _int(result.get("schema_version")) or 1
    result["status"] = _text(result.get("status")) or SESSION_STATUS_UNKNOWN
    result["answer"] = _text(result.get("answer")) or "unknown"
    result["rows"] = rows
    return result


def _build_row(
    *,
    provider: str,
    participant: _StatusParticipant,
    liveness: _StatusLiveness,
    outcome: _StatusOutcome,
    agent_mind: _StatusAgentMind,
    activity_entries: Sequence[SessionActivityEntry],
    head_sha: str,
    worktree_hash: str,
    worktree_dirty: bool | None,
) -> SessionStatusRow:
    latest_task_complete = _field_text(agent_mind, "latest_task_complete_at")
    session_matches_current = _agent_mind_session_matches_current(
        agent_mind=agent_mind,
        participant=participant,
        outcome=outcome,
    )
    agent_mind_stale = False if session_matches_current is not False else True
    latest_outcome = _field_text(outcome, "outcome")
    liveness_state = _field_text(liveness, "state")
    process_live = _field_bool(liveness, "process_live")
    if process_live is None and _has_field(participant, "live"):
        process_live = _field_bool(participant, "live")
    status, answer, reason = _classify_status(
        latest_task_complete=latest_task_complete,
        agent_mind_stale=agent_mind_stale,
        latest_outcome=latest_outcome,
        liveness_state=liveness_state,
        process_live=process_live,
    )
    role = (
        _field_text(participant, "role")
        or _field_text(liveness, "role")
        or _field_text(outcome, "session_actor_role")
        or _field_text(agent_mind, "role")
    )
    return SessionStatusRow(
        provider=provider,
        role=role,
        status=status,
        answer=answer,
        reason=reason,
        session_id=(
            _field_text(agent_mind, "session_id")
            or _field_text(outcome, "session_id")
            or _field_text(participant, "session_id")
        ),
        session_name=(
            _field_text(participant, "session_name")
            or _field_text(outcome, "session_name")
        ),
        process_live=process_live,
        liveness_state=liveness_state,
        latest_task_complete_at=latest_task_complete,
        agent_mind_generated_at_utc=_field_text(agent_mind, "generated_at_utc"),
        agent_mind_session_matches_current=session_matches_current,
        agent_mind_stale=agent_mind_stale,
        latest_session_outcome=latest_outcome,
        latest_session_outcome_reason=_field_text(outcome, "reason"),
        latest_session_outcome_at_utc=(
            _field_text(outcome, "finished_at_utc")
            or _field_text(outcome, "observed_at_utc")
        ),
        head_sha=head_sha,
        worktree_hash=worktree_hash,
        worktree_dirty=worktree_dirty,
        session_path=_field_text(agent_mind, "session_path"),
        log_path=(
            _field_text(participant, "log_path")
            or _field_text(outcome, "log_path")
        ),
        evidence_refs=_row_evidence(
            provider=provider,
            agent_mind=agent_mind,
            liveness=liveness,
            outcome=outcome,
            participant=participant,
            activity_entries=activity_entries,
        ),
    )


def _classify_status(
    *,
    latest_task_complete: str,
    agent_mind_stale: bool | None,
    latest_outcome: str,
    liveness_state: str,
    process_live: bool | None,
) -> tuple[str, str, str]:
    if latest_task_complete and agent_mind_stale is not True:
        return (
            SESSION_STATUS_TASK_COMPLETED,
            "task_complete",
            "agent_mind_task_complete_observed",
        )
    if latest_outcome == AGENT_SESSION_OUTCOME_COMPLETED_HANDOFF:
        return (
            SESSION_STATUS_TASK_COMPLETED,
            "task_complete",
            "agent_session_outcome_completed_handoff",
        )
    if latest_outcome in {
        AGENT_SESSION_OUTCOME_PROCESS_DIED,
        AGENT_SESSION_OUTCOME_UNRESOLVED,
    }:
        return (
            SESSION_STATUS_MID_TASK_DEATH,
            "mid_task_death",
            f"agent_session_outcome_{latest_outcome}",
        )
    if liveness_state in _DEAD_LIVENESS_STATES:
        return (
            SESSION_STATUS_MID_TASK_DEATH,
            "mid_task_death",
            "session_dead_without_task_complete",
        )
    if liveness_state in _DETACHED_LIVENESS_STATES:
        return (
            SESSION_STATUS_DETACHED_RUNTIME_ONLY,
            "runtime_detached",
            "runtime_activity_without_live_conductor",
        )
    if process_live is False:
        return (
            SESSION_STATUS_MID_TASK_DEATH,
            "mid_task_death",
            "session_dead_without_task_complete",
        )
    if liveness_state in _LIVE_LIVENESS_STATES or process_live is True:
        return (SESSION_STATUS_RUNNING, "still_running", "live_session_observed")
    if latest_task_complete and agent_mind_stale is True:
        return (
            SESSION_STATUS_UNKNOWN,
            "unknown",
            "stale_agent_mind_task_complete_ignored",
        )
    return (SESSION_STATUS_UNKNOWN, "unknown", "insufficient_session_evidence")


def _overall_status(rows: Sequence[SessionStatusRow]) -> tuple[str, str]:
    statuses = {row.status for row in rows}
    if SESSION_STATUS_MID_TASK_DEATH in statuses:
        return SESSION_STATUS_MID_TASK_DEATH, "mid_task_death"
    if SESSION_STATUS_TASK_COMPLETED in statuses:
        return SESSION_STATUS_TASK_COMPLETED, "task_complete"
    if SESSION_STATUS_RUNNING in statuses:
        return SESSION_STATUS_RUNNING, "still_running"
    if SESSION_STATUS_DETACHED_RUNTIME_ONLY in statuses:
        return SESSION_STATUS_DETACHED_RUNTIME_ONLY, "runtime_detached"
    return SESSION_STATUS_UNKNOWN, "unknown"


def _participants(
    collaboration: CollaborationSessionState | Mapping[str, object] | None,
) -> dict[str, _StatusParticipant]:
    if isinstance(collaboration, CollaborationSessionState):
        rows: Sequence[object] = collaboration.participants
    elif isinstance(collaboration, Mapping):
        rows = _sequence(collaboration.get("participants"))
    else:
        rows = ()
    result: dict[str, _StatusParticipant] = {}
    for row in rows or ():
        participant = _participant_from_value(row)
        provider = (
            _field_text(participant, "provider")
            or _field_text(participant, "agent_id")
        )
        if provider:
            result.setdefault(provider.lower(), participant)
    return result


def _latest_outcomes_by_provider(
    collaboration: CollaborationSessionState | Mapping[str, object] | None,
) -> dict[str, _StatusOutcome]:
    if isinstance(collaboration, CollaborationSessionState):
        rows: Sequence[object] = collaboration.session_outcomes
    elif isinstance(collaboration, Mapping):
        rows = _sequence(collaboration.get("session_outcomes"))
    else:
        rows = ()
    grouped: dict[str, _StatusOutcome] = {}
    for row in rows or ():
        outcome = _outcome_from_value(row)
        provider = (
            _field_text(outcome, "provider")
            or _field_text(outcome, "session_actor_id")
        )
        if not provider:
            continue
        key = provider.lower()
        if _outcome_sort_key(outcome) >= _outcome_sort_key(grouped.get(key, {})):
            grouped[key] = outcome
    return grouped


def _liveness_by_provider(
    bridge_liveness: ReviewBridgeState | Mapping[str, object] | None,
) -> dict[str, _StatusLiveness]:
    if isinstance(bridge_liveness, ReviewBridgeState):
        rows: Sequence[object] = bridge_liveness.session_liveness_signals
    else:
        rows = _sequence(
            _field_value(bridge_liveness, "session_liveness_signals")
            or _field_value(bridge_liveness, "participant_liveness")
        )
    result: dict[str, _StatusLiveness] = {}
    for row in rows:
        liveness = _liveness_from_value(row)
        provider = _field_text(liveness, "provider")
        if provider:
            result.setdefault(provider.lower(), liveness)
    return result


def _agent_minds_by_provider(
    agent_minds: Mapping[str, AgentMindSlice | Mapping[str, object]],
) -> dict[str, _StatusAgentMind]:
    result: dict[str, _StatusAgentMind] = {}
    for provider_hint, raw_mind in agent_minds.items():
        agent_mind = _agent_mind_from_value(raw_mind, provider_hint=provider_hint)
        provider = (
            _field_text(agent_mind, "agent_provider")
            or _field_text(agent_mind, "provider")
            or provider_hint
        )
        if provider:
            result.setdefault(provider.lower(), agent_mind)
    return result


def _activity_entries_by_provider(
    entries: Sequence[SessionActivityEntry],
) -> dict[str, tuple[SessionActivityEntry, ...]]:
    grouped: dict[str, list[SessionActivityEntry]] = {}
    for entry in entries:
        if not isinstance(entry, SessionActivityEntry):
            continue
        provider = entry.actor_id.strip().lower()
        if provider:
            grouped.setdefault(provider, []).append(entry)
    return {provider: tuple(rows) for provider, rows in grouped.items()}


def _projection_evidence(rows: Sequence[SessionStatusRow]) -> tuple[str, ...]:
    refs: list[str] = []
    for row in rows:
        refs.extend(row.evidence_refs)
    return tuple(dict.fromkeys(refs))


def _row_evidence(
    *,
    provider: str,
    agent_mind: _StatusAgentMind,
    liveness: _StatusLiveness,
    outcome: _StatusOutcome,
    participant: _StatusParticipant,
    activity_entries: Sequence[SessionActivityEntry],
) -> tuple[str, ...]:
    refs = []
    if agent_mind:
        refs.append(f"agent_mind:{provider}")
    if liveness:
        refs.append(f"session_liveness:{provider}")
    if outcome:
        refs.append(f"agent_session_outcome:{provider}")
    if participant:
        refs.append(f"collaboration_participant:{provider}")
    refs.extend(f"session_activity:{entry.entry_id}" for entry in activity_entries)
    return tuple(refs)


def _agent_mind_session_matches_current(
    *,
    agent_mind: _StatusAgentMind,
    participant: _StatusParticipant,
    outcome: _StatusOutcome,
) -> bool | None:
    """Compare agent-mind session identity only when comparable ids exist."""
    mind_session_id = _field_text(agent_mind, "session_id")
    if not mind_session_id:
        return None
    comparable_ids = {
        _field_text(outcome, "session_id"),
        _field_text(participant, "session_id"),
    }
    comparable_ids = {value for value in comparable_ids if value}
    if not comparable_ids:
        return None
    return mind_session_id in comparable_ids


def _recovery_assessment_evidence(
    recovery_assessment: RecoveryAssessmentState | None,
) -> tuple[str, ...]:
    if not isinstance(recovery_assessment, RecoveryAssessmentState):
        return ()
    diagnosis = recovery_assessment.diagnosis
    decision = recovery_assessment.decision
    refs = ["recovery_assessment"]
    if diagnosis.status:
        refs.append(f"recovery_assessment_status:{diagnosis.status}")
    if decision.action_id:
        refs.append(f"recovery_decision:{decision.action_id}")
    return tuple(refs)


def _ordered_unique(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = _text(value).lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def _outcome_sort_key(row: _StatusOutcome) -> tuple[str, str]:
    return (
        _field_text(row, "finished_at_utc") or _field_text(row, "observed_at_utc"),
        _field_text(row, "source_event_id"),
    )


def _participant_from_value(value: object) -> _StatusParticipant:
    if isinstance(value, CollaborationParticipantState):
        return value
    return _mapping(value)


def _outcome_from_value(value: object) -> _StatusOutcome:
    if isinstance(value, AgentSessionOutcomeState):
        return value
    if isinstance(value, Mapping):
        return agent_session_outcome_from_mapping(value) or value
    return _mapping(value)


def _liveness_from_value(value: object) -> _StatusLiveness:
    if isinstance(value, SessionLivenessSignal):
        return value
    mapping = _mapping(value)
    provider = _text(mapping.get("provider"))
    state = _text(mapping.get("state"))
    if provider and state in _SESSION_LIVENESS_STATES:
        return SessionLivenessSignal(
            provider=provider,
            role=_text(mapping.get("role")),
            state=cast(SessionLivenessState, state),
            reason=_text(mapping.get("reason")),
            process_live=_optional_bool(mapping, "process_live"),
            terminal_open=_optional_bool(mapping, "terminal_open"),
            poll_age_seconds=_optional_int(mapping.get("poll_age_seconds")),
            last_activity_utc=_text(mapping.get("last_activity_utc")) or None,
            timestamp_utc=_text(mapping.get("timestamp_utc")),
            contract_id=_text(mapping.get("contract_id")) or "SessionLivenessSignal",
            schema_version=_int(mapping.get("schema_version")) or 1,
        )
    return mapping


def _agent_mind_from_value(
    value: object,
    *,
    provider_hint: str = "",
) -> _StatusAgentMind:
    if isinstance(value, AgentMindSlice):
        return value
    mapping = _mapping(value)
    if not mapping:
        return {}
    if _text(mapping.get("contract_id")) == "AgentMindSlice" or any(
        key in mapping
        for key in (
            "agent_provider",
            "session_id",
            "session_path",
            "latest_task_complete_at",
        )
    ):
        events = _sequence(mapping.get("events") or mapping.get("latest_events"))
        event_count = _int(mapping.get("event_count")) or len(events)
        return AgentMindSlice(
            schema_version=_int(mapping.get("schema_version")) or 1,
            contract_id=_text(mapping.get("contract_id")) or "AgentMindSlice",
            agent_provider=(
                _text(mapping.get("agent_provider"))
                or _text(mapping.get("provider"))
                or provider_hint
            ),
            session_id=_text(mapping.get("session_id")),
            session_path=_text(mapping.get("session_path")),
            generated_at_utc=_text(mapping.get("generated_at_utc")),
            last_cursor=_text(mapping.get("last_cursor")),
            events=(),
            event_count=event_count,
            latest_task_complete_at=_text(mapping.get("latest_task_complete_at")),
            latest_escalation_at=_text(mapping.get("latest_escalation_at")),
            latest_error_at=_text(mapping.get("latest_error_at")),
            peer_awareness_policy=dict(_mapping(mapping.get("peer_awareness_policy"))),
            peer_awareness=dict(_mapping(mapping.get("peer_awareness"))),
        )
    return mapping


def _field_value(value: object, field_name: str) -> object:
    if isinstance(value, Mapping):
        return value.get(field_name)
    if value is None:
        return None
    return getattr(value, field_name, None)


def _field_text(value: object, field_name: str) -> str:
    return _text(_field_value(value, field_name))


def _field_bool(value: object, field_name: str) -> bool | None:
    if isinstance(value, Mapping):
        return _optional_bool(value, field_name)
    if not hasattr(value, field_name):
        return None
    raw = getattr(value, field_name)
    if raw is None:
        return None
    if isinstance(raw, bool):
        return raw
    return bool(raw)


def _has_field(value: object, field_name: str) -> bool:
    return (
        field_name in value
        if isinstance(value, Mapping)
        else hasattr(value, field_name)
    )


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(value)
    return ()


def _optional_bool(mapping: Mapping[str, object], key: str) -> bool | None:
    if key not in mapping:
        return None
    value = mapping.get(key)
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y", "on"}:
            return True
        if text in {"0", "false", "no", "n", "off"}:
            return False
    return bool(value)


def _text(value: object) -> str:
    return str(value or "").strip()


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


__all__ = [
    "SESSION_STATUS_DETACHED_RUNTIME_ONLY",
    "SESSION_STATUS_MID_TASK_DEATH",
    "SESSION_STATUS_PROJECTION_CONTRACT_ID",
    "SESSION_STATUS_PROJECTION_SCHEMA_VERSION",
    "SESSION_STATUS_RUNNING",
    "SESSION_STATUS_TASK_COMPLETED",
    "SESSION_STATUS_UNKNOWN",
    "SessionStatusProjection",
    "SessionStatusRow",
    "build_session_status_projection",
    "session_status_projection_from_mapping",
]
