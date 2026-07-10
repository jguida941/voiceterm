"""Typed implementer ACK events for current-session authority.

The event is role-keyed, not provider-keyed. Concrete actor/provider names are
metadata that prove who wrote the ACK; the reducer consumes the durable
``implementer`` role and current instruction revision.
"""

from __future__ import annotations

import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from ..runtime.role_profile import TandemRole, normalize_tandem_role
from ..time_utils import utc_timestamp
from .event_store import next_event_id
from .state import project_id_for_repo


IMPLEMENTER_ACK_EVENT_TYPE = "review_channel.implementer_ack"
IMPLEMENTER_AUTHORITY_EVENT_TYPES = frozenset({IMPLEMENTER_ACK_EVENT_TYPE})

_REQUIRED_ENVELOPE_FIELDS = (
    "event_id",
    "event_type",
    "schema_version",
    "source",
    "session_id",
    "plan_id",
    "project_id",
    "timestamp_utc",
    "idempotency_key",
    "nonce",
)


@dataclass(frozen=True)
class ImplementerAckEventInput:
    repo_root: Path
    existing_events: list[dict[str, object]]
    actor: str
    revision: str
    notes: str
    session_id: str
    plan_id: str
    controller_run_id: object = None
    target_session_id: str = ""


def implementer_ack_idempotency_key(
    *,
    actor: str,
    session_id: str,
    revision: str,
    target_session_id: str = "",
) -> str:
    scope = target_session_id.strip() or session_id.strip()
    return (
        "review_channel.implementer_ack:"
        f"actor={actor.strip()}:session={scope}:revision={revision.strip()}"
    )


def build_implementer_ack_event(
    event_input: ImplementerAckEventInput,
) -> dict[str, object]:
    timestamp = utc_timestamp()
    canonical_notes = event_input.notes.strip()
    revision = event_input.revision.strip()
    ack_text = _ack_text(revision=revision, notes=canonical_notes)
    return dict(
        schema_version=1,
        event_id=next_event_id(event_input.existing_events),
        session_id=event_input.session_id,
        project_id=project_id_for_repo(event_input.repo_root),
        trace_id="",
        timestamp_utc=timestamp,
        source="review_channel",
        plan_id=event_input.plan_id,
        controller_run_id=event_input.controller_run_id,
        event_type=IMPLEMENTER_ACK_EVENT_TYPE,
        payload=dict(
            actor=event_input.actor.strip(),
            actor_role=TandemRole.IMPLEMENTER.value,
            target_role=TandemRole.IMPLEMENTER.value,
            target_session_id=event_input.target_session_id.strip(),
            current_instruction_revision=revision,
            acknowledged_at_utc=timestamp,
            notes=canonical_notes,
            implementer_ack=ack_text,
        ),
        status="current",
        semantic_zref=f"role:implementer_ack:{revision}",
        idempotency_key=implementer_ack_idempotency_key(
            actor=event_input.actor,
            session_id=event_input.session_id,
            revision=revision,
            target_session_id=event_input.target_session_id,
        ),
        nonce=secrets.token_hex(12),
        metadata=dict(
            source_contract="ReviewCurrentSessionState",
            plan_row_id="PKT-BIND-REV-PKT-2618",
        ),
    )


def find_matching_implementer_ack_event(
    events: list[dict[str, object]] | tuple[dict[str, object], ...],
    *,
    actor: str,
    session_id: str,
    revision: str,
    target_session_id: str = "",
) -> Mapping[str, object]:
    expected = implementer_ack_idempotency_key(
        actor=actor,
        session_id=session_id,
        revision=revision,
        target_session_id=target_session_id,
    )
    for event in reversed(events):
        if not isinstance(event, Mapping):
            continue
        if str(event.get("idempotency_key") or "") == expected:
            return event
    return {}


def latest_implementer_ack_payload(
    events: list[dict[str, object]] | tuple[dict[str, object], ...],
    *,
    current_instruction_revision: str = "",
) -> Mapping[str, object]:
    latest: dict[str, object] = {}
    expected_revision = current_instruction_revision.strip()
    for event in events:
        if not isinstance(event, Mapping):
            continue
        if str(event.get("event_type") or "").strip() != IMPLEMENTER_ACK_EVENT_TYPE:
            continue
        if not _has_canonical_envelope(event):
            continue
        payload = event.get("payload")
        if not isinstance(payload, Mapping):
            continue
        if normalize_tandem_role(payload.get("target_role")) != TandemRole.IMPLEMENTER:
            continue
        revision = str(payload.get("current_instruction_revision") or "").strip()
        if expected_revision and revision != expected_revision:
            continue
        latest = dict(
            actor=str(payload.get("actor") or ""),
            actor_role=str(payload.get("actor_role") or ""),
            target_role=str(payload.get("target_role") or ""),
            target_session_id=str(payload.get("target_session_id") or ""),
            current_instruction_revision=revision,
            acknowledged_at_utc=str(payload.get("acknowledged_at_utc") or ""),
            notes=str(payload.get("notes") or ""),
            implementer_ack=str(payload.get("implementer_ack") or ""),
            event_id=str(event.get("event_id") or ""),
            timestamp_utc=str(event.get("timestamp_utc") or ""),
        )
    return latest


def _ack_text(*, revision: str, notes: str) -> str:
    line = f"- acknowledged current instruction revision: `{revision.strip()}`"
    if notes:
        return f"{line}\n- notes: {notes}"
    return line


def _has_canonical_envelope(event: Mapping[str, object]) -> bool:
    for field in _REQUIRED_ENVELOPE_FIELDS:
        value = event.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            return False
    return str(event.get("source") or "").strip() == "review_channel"


__all__ = [
    "IMPLEMENTER_ACK_EVENT_TYPE",
    "IMPLEMENTER_AUTHORITY_EVENT_TYPES",
    "ImplementerAckEventInput",
    "build_implementer_ack_event",
    "find_matching_implementer_ack_event",
    "latest_implementer_ack_payload",
]
