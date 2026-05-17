"""Advisory wake evidence helpers for collaboration profiles."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .review_packet_inbox import packet_inbox_from_review_state
from .review_state_packet_models import AgentAttentionRecord
from .reviewer_runtime_models import WakeEvidence, derive_wake_evidence_for_actor


def advisory_wake_evidence(
    *,
    role_bindings: tuple[object, ...],
    review_state: Mapping[str, object],
    events: Sequence[Mapping[str, object]],
    wake_evidence_type: Any,
) -> tuple[object, ...]:
    if not role_bindings:
        return ()
    packet_inbox = packet_inbox_from_review_state(review_state)
    rows: list[object] = []
    event_rows = [dict(event) for event in events if isinstance(event, Mapping)]
    for binding in role_bindings:
        actor_id = (
            f"{binding.role}-{binding.provider}" if binding.role else binding.provider
        )
        evidence = derive_wake_evidence_for_actor(
            events=event_rows,
            actor_id=actor_id,
            session_id=binding.session_id,
        )
        record = packet_inbox.for_agent(binding.provider) if packet_inbox else None
        pending_packet_ids = wake_pending_packet_ids(evidence, record)
        attention_status = getattr(record, "attention_status", "none") if record else "none"
        wake_reason = getattr(record, "wake_reason", "") if record else ""
        required_command = getattr(record, "required_command", "") if record else ""
        if (
            evidence.arrival_kind == "none"
            and attention_status == "none"
            and not wake_reason
            and not required_command
            and not pending_packet_ids
        ):
            continue
        rows.append(
            wake_evidence_type(
                role=binding.role,
                provider=binding.provider,
                actor_id=actor_id,
                session_id=binding.session_id,
                arrival_kind=evidence.arrival_kind,
                latest_relevant_event_id=evidence.latest_relevant_event_id,
                latest_relevant_event_at_utc=evidence.latest_relevant_event_at_utc,
                latest_relevant_packet_id=evidence.latest_relevant_packet_id,
                attention_status=attention_status,
                wake_reason=wake_reason,
                required_command=required_command,
                pending_packet_ids=pending_packet_ids,
            )
        )
    return tuple(rows)


def wake_pending_packet_ids(
    evidence: WakeEvidence,
    record: AgentAttentionRecord | None,
) -> tuple[str, ...]:
    packet_ids: list[str] = []
    append_packet_id(packet_ids, evidence.latest_relevant_packet_id)
    if record is not None:
        append_packet_id(packet_ids, record.current_instruction_packet_id)
        append_packet_id(packet_ids, record.latest_finding_packet_id)
        for packet_id in record.pending_actionable_packet_ids:
            append_packet_id(packet_ids, packet_id)
        for packet_id in record.expired_unresolved_packet_ids:
            append_packet_id(packet_ids, packet_id)
    return tuple(packet_ids)


def append_packet_id(packet_ids: list[str], value: object) -> None:
    packet_id = str(value or "").strip()
    if packet_id and packet_id not in packet_ids:
        packet_ids.append(packet_id)
