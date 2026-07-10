"""Typed agent-session outcome contract for review-channel lifecycle state."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

AGENT_SESSION_OUTCOME_CONTRACT_ID = "AgentSessionOutcome"
AGENT_SESSION_OUTCOME_SCHEMA_VERSION = 1

AGENT_SESSION_OUTCOME_COMPLETED_HANDOFF = "completed_handoff"
AGENT_SESSION_OUTCOME_PROCESS_DIED = "process_died"
AGENT_SESSION_OUTCOME_UNRESOLVED = "unresolved"

AGENT_SESSION_OUTCOMES = frozenset(
    {
        AGENT_SESSION_OUTCOME_COMPLETED_HANDOFF,
        AGENT_SESSION_OUTCOME_PROCESS_DIED,
        AGENT_SESSION_OUTCOME_UNRESOLVED,
    }
)


@dataclass(frozen=True, slots=True)
class AgentSessionOutcomeState:
    """Portable typed receipt for how one agent-owned session ended."""

    schema_version: int
    contract_id: str
    outcome: str
    reason: str
    provider: str
    session_actor_id: str
    session_actor_role: str
    session_id: str
    session_name: str
    observed_at_utc: str
    finished_at_utc: str
    source: str
    source_event_id: str = ""
    handoff_packet_id: str = ""
    handoff_requested_action: str = ""
    target_kind: str = ""
    target_ref: str = ""
    target_revision: str = ""
    metadata_path: str = ""
    log_path: str = ""
    workspace_root: str = ""
    prepared_at_utc: str = ""
    prepared_session_token: str = ""
    prepared_head_sha: str = ""
    prepared_instruction_revision: str = ""

    def is_completed_handoff(self) -> bool:
        return self.outcome == AGENT_SESSION_OUTCOME_COMPLETED_HANDOFF


class SessionOutcomeSource(Protocol):
    """Fixed-shape session row consumed by unresolved-outcome projection."""

    provider: str
    role: str
    session_name: str
    live: bool
    launch_authority_reason: str
    live_reason: str
    metadata_path: str
    log_path: str
    workspace_root: str
    prepared_at: str
    prepared_session_token: str
    prepared_head_sha: str
    prepared_instruction_revision: str


def agent_session_outcome_from_mapping(
    value: Mapping[str, object],
) -> AgentSessionOutcomeState | None:
    outcome = _text(value.get("outcome"))
    if outcome not in AGENT_SESSION_OUTCOMES:
        return None
    provider = _text(value.get("provider"))
    session_actor_id = _text(value.get("session_actor_id")) or provider
    if not (provider or session_actor_id):
        return None
    return AgentSessionOutcomeState(
        schema_version=_int(value.get("schema_version")) or 1,
        contract_id=(
            _text(value.get("contract_id")) or AGENT_SESSION_OUTCOME_CONTRACT_ID
        ),
        outcome=outcome,
        reason=_text(value.get("reason")),
        provider=provider or session_actor_id,
        session_actor_id=session_actor_id,
        session_actor_role=_text(value.get("session_actor_role")),
        session_id=_text(value.get("session_id")),
        session_name=_text(value.get("session_name")),
        observed_at_utc=(
            _text(value.get("observed_at_utc"))
            or _text(value.get("timestamp_utc"))
        ),
        finished_at_utc=(
            _text(value.get("finished_at_utc"))
            or _text(value.get("timestamp_utc"))
        ),
        source=_text(value.get("source")),
        source_event_id=_text(value.get("source_event_id")),
        handoff_packet_id=_text(value.get("handoff_packet_id")),
        handoff_requested_action=_text(value.get("handoff_requested_action")),
        target_kind=_text(value.get("target_kind")),
        target_ref=_text(value.get("target_ref")),
        target_revision=_text(value.get("target_revision")),
        metadata_path=_text(value.get("metadata_path")),
        log_path=_text(value.get("log_path")),
        workspace_root=_text(value.get("workspace_root")),
        prepared_at_utc=(
            _text(value.get("prepared_at_utc"))
            or _text(value.get("prepared_at"))
        ),
        prepared_session_token=_text(value.get("prepared_session_token")),
        prepared_head_sha=_text(value.get("prepared_head_sha")),
        prepared_instruction_revision=_text(
            value.get("prepared_instruction_revision")
        ),
    )


def agent_session_outcomes_from_value(
    value: object,
) -> tuple[AgentSessionOutcomeState, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    rows: list[AgentSessionOutcomeState] = []
    for row in value:
        if not isinstance(row, Mapping):
            continue
        outcome = agent_session_outcome_from_mapping(row)
        if outcome is not None:
            rows.append(outcome)
    return tuple(rows)


def latest_agent_session_outcome(
    outcomes: Sequence[AgentSessionOutcomeState],
    *,
    provider: str = "",
    outcome: str = "",
) -> AgentSessionOutcomeState | None:
    provider_key = provider.strip().lower()
    outcome_key = outcome.strip()
    candidates = [
        row
        for row in outcomes
        if (not provider_key or row.provider.lower() == provider_key)
        and (not outcome_key or row.outcome == outcome_key)
    ]
    return max(candidates, key=_outcome_sort_key, default=None)


def projected_unresolved_session_outcomes(
    sessions: Sequence[SessionOutcomeSource],
    existing_outcomes: Sequence[AgentSessionOutcomeState],
    *,
    observed_at_utc: str,
) -> tuple[AgentSessionOutcomeState, ...]:
    """Project dead/unresolved conductor sessions that lack an end receipt."""
    existing_keys = {_session_outcome_key(outcome) for outcome in existing_outcomes}
    projected: list[AgentSessionOutcomeState] = []
    for session in sessions:
        if session.live:
            continue
        key = _session_key(session)
        if key in existing_keys:
            continue
        provider, session_name, prepared_token = key
        if not provider:
            continue
        reason = (
            _text(session.launch_authority_reason)
            or _text(session.live_reason)
            or "session ended without typed handoff packet"
        )
        projected.append(
            AgentSessionOutcomeState(
                schema_version=AGENT_SESSION_OUTCOME_SCHEMA_VERSION,
                contract_id=AGENT_SESSION_OUTCOME_CONTRACT_ID,
                outcome=AGENT_SESSION_OUTCOME_UNRESOLVED,
                reason=f"unresolved_session_outcome: {reason}",
                provider=provider,
                session_actor_id=provider,
                session_actor_role=_text(session.role),
                session_id="",
                session_name=session_name,
                observed_at_utc=observed_at_utc,
                finished_at_utc=observed_at_utc,
                source="collaboration_session_projection",
                metadata_path=_text(session.metadata_path),
                log_path=_text(session.log_path),
                workspace_root=_text(session.workspace_root),
                prepared_at_utc=_text(session.prepared_at),
                prepared_session_token=prepared_token,
                prepared_head_sha=_text(session.prepared_head_sha),
                prepared_instruction_revision=_text(session.prepared_instruction_revision),
            )
        )
    return tuple(projected)


def _session_outcome_key(
    outcome: AgentSessionOutcomeState,
) -> tuple[str, str, str]:
    return (
        outcome.provider.lower(),
        outcome.session_name,
        outcome.prepared_session_token,
    )


def _session_key(session: SessionOutcomeSource) -> tuple[str, str, str]:
    provider = _text(session.provider).lower()
    session_name = _text(session.session_name)
    prepared_token = _text(session.prepared_session_token)
    return (provider, session_name, prepared_token)


def _outcome_sort_key(row: AgentSessionOutcomeState) -> tuple[str, str]:
    return (
        row.finished_at_utc or row.observed_at_utc,
        row.source_event_id,
    )


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


__all__ = [
    "AGENT_SESSION_OUTCOME_COMPLETED_HANDOFF",
    "AGENT_SESSION_OUTCOME_CONTRACT_ID",
    "AGENT_SESSION_OUTCOME_PROCESS_DIED",
    "AGENT_SESSION_OUTCOME_SCHEMA_VERSION",
    "AGENT_SESSION_OUTCOME_UNRESOLVED",
    "AGENT_SESSION_OUTCOMES",
    "AgentSessionOutcomeState",
    "SessionOutcomeSource",
    "agent_session_outcome_from_mapping",
    "agent_session_outcomes_from_value",
    "latest_agent_session_outcome",
    "projected_unresolved_session_outcomes",
]
