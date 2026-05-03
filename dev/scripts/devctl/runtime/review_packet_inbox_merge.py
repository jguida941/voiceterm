"""Merge helpers for persisted and rebuilt packet-inbox state."""

from __future__ import annotations

from collections.abc import Mapping

from .review_state_packet_models import (
    AgentAttentionRecord,
    PacketInboxState,
)


def merge_packet_inbox_states(
    *,
    rebuilt: PacketInboxState,
    persisted: PacketInboxState,
    live_packet_ids: frozenset[str] | None,
    live_packet_ids_by_agent: Mapping[str, frozenset[str]] | None = None,
) -> PacketInboxState:
    """Merge rebuilt packet-inbox truth with any still-relevant persisted state."""
    merged_agents: list[AgentAttentionRecord] = []
    for agent in sorted(_agent_ids(rebuilt=rebuilt, persisted=persisted)):
        agent_live_packet_ids = _live_packet_ids_for_agent(
            agent,
            live_packet_ids=live_packet_ids,
            live_packet_ids_by_agent=live_packet_ids_by_agent,
        )
        rebuilt_record = rebuilt.for_agent(agent)
        persisted_record = sanitize_persisted_record(
            persisted.for_agent(agent),
            live_packet_ids=agent_live_packet_ids,
        )
        if rebuilt_record is None and persisted_record is None:
            continue
        if rebuilt_record is None:
            assert persisted_record is not None
            merged_agents.append(persisted_record)
            continue
        if persisted_record is None:
            merged_agents.append(rebuilt_record)
            continue
        merged_agents.append(
            _merge_agent_attention_records(
                rebuilt_record=rebuilt_record,
                persisted_record=persisted_record,
                rebuilt_packet_refs_authoritative=agent_live_packet_ids is not None,
            )
        )
    return PacketInboxState(
        attention_revision=rebuilt.attention_revision or persisted.attention_revision,
        agents=tuple(merged_agents),
    )


def _live_packet_ids_for_agent(
    agent: str,
    *,
    live_packet_ids: frozenset[str] | None,
    live_packet_ids_by_agent: Mapping[str, frozenset[str]] | None,
) -> frozenset[str] | None:
    if live_packet_ids is None:
        return None
    if not live_packet_ids:
        return live_packet_ids
    if live_packet_ids_by_agent is None:
        return live_packet_ids
    return live_packet_ids_by_agent.get(agent)


def sanitize_persisted_record(
    record: AgentAttentionRecord | None,
    *,
    live_packet_ids: frozenset[str] | None,
) -> AgentAttentionRecord | None:
    """Drop persisted packet references that no longer exist in the live reducer."""
    if record is None:
        return None
    packets_missing = live_packet_ids is None
    sanitized = AgentAttentionRecord(
        agent=record.agent,
        current_instruction_packet_id=(
            record.current_instruction_packet_id
            if packets_missing or record.current_instruction_packet_id in live_packet_ids
            else ""
        ),
        latest_finding_packet_id=(
            record.latest_finding_packet_id
            if packets_missing or record.latest_finding_packet_id in live_packet_ids
            else ""
        ),
        pending_actionable_packet_ids=tuple(
            packet_id
            for packet_id in record.pending_actionable_packet_ids
            if packets_missing or packet_id in live_packet_ids
        ),
        expired_unresolved_packet_ids=(
            record.expired_unresolved_packet_ids
            if packets_missing
            else tuple(
                packet_id
                for packet_id in record.expired_unresolved_packet_ids
                if packet_id in live_packet_ids
            )
        ),
        attention_status=record.attention_status,
        wake_reason=record.wake_reason,
        required_command=record.required_command,
        attention_revision=record.attention_revision,
        delivery_state=record.delivery_state,
    )
    if _record_has_live_attention(sanitized):
        return sanitized
    return AgentAttentionRecord(
        agent=sanitized.agent,
        current_instruction_packet_id=sanitized.current_instruction_packet_id,
        latest_finding_packet_id=sanitized.latest_finding_packet_id,
        pending_actionable_packet_ids=sanitized.pending_actionable_packet_ids,
        expired_unresolved_packet_ids=sanitized.expired_unresolved_packet_ids,
        attention_status="none",
        wake_reason="",
        required_command="",
        attention_revision=sanitized.attention_revision,
        delivery_state="idle",
    )


def _merge_agent_attention_records(
    *,
    rebuilt_record: AgentAttentionRecord,
    persisted_record: AgentAttentionRecord,
    rebuilt_packet_refs_authoritative: bool,
) -> AgentAttentionRecord:
    driver = (
        rebuilt_record
        if rebuilt_packet_refs_authoritative
        else _attention_driver(rebuilt_record, persisted_record)
    )
    return AgentAttentionRecord(
        agent=rebuilt_record.agent,
        current_instruction_packet_id=(
            rebuilt_record.current_instruction_packet_id
            if rebuilt_packet_refs_authoritative
            else (
                rebuilt_record.current_instruction_packet_id
                or persisted_record.current_instruction_packet_id
            )
        ),
        latest_finding_packet_id=(
            rebuilt_record.latest_finding_packet_id
            if rebuilt_packet_refs_authoritative
            else (
                rebuilt_record.latest_finding_packet_id
                or persisted_record.latest_finding_packet_id
            )
        ),
        pending_actionable_packet_ids=(
            rebuilt_record.pending_actionable_packet_ids
            if rebuilt_packet_refs_authoritative
            else (
                rebuilt_record.pending_actionable_packet_ids
                or persisted_record.pending_actionable_packet_ids
            )
        ),
        expired_unresolved_packet_ids=(
            rebuilt_record.expired_unresolved_packet_ids
            if rebuilt_packet_refs_authoritative
            else (
                rebuilt_record.expired_unresolved_packet_ids
                or persisted_record.expired_unresolved_packet_ids
            )
        ),
        attention_status=driver.attention_status,
        wake_reason=driver.wake_reason,
        required_command=driver.required_command
        or rebuilt_record.required_command
        or persisted_record.required_command,
        attention_revision=driver.attention_revision
        or rebuilt_record.attention_revision
        or persisted_record.attention_revision,
        delivery_state=driver.delivery_state,
    )


def _attention_driver(
    rebuilt_record: AgentAttentionRecord,
    persisted_record: AgentAttentionRecord,
) -> AgentAttentionRecord:
    rebuilt_score = _attention_score(rebuilt_record)
    persisted_score = _attention_score(persisted_record)
    if persisted_score > rebuilt_score:
        return persisted_record
    return rebuilt_record


def _attention_score(record: AgentAttentionRecord) -> tuple[int, ...]:
    return (
        1 if record.current_instruction_packet_id else 0,
        len(record.pending_actionable_packet_ids),
        len(record.expired_unresolved_packet_ids),
        1 if record.latest_finding_packet_id else 0,
        1 if record.attention_status not in {"", "none"} else 0,
        1 if record.required_command else 0,
        1 if record.delivery_state != "idle" else 0,
    )


def _record_has_live_attention(record: AgentAttentionRecord) -> bool:
    return bool(
        record.current_instruction_packet_id
        or record.pending_actionable_packet_ids
        or record.expired_unresolved_packet_ids
    )


def _agent_ids(
    *,
    rebuilt: PacketInboxState,
    persisted: PacketInboxState,
) -> frozenset[str]:
    return frozenset(
        {
            *(record.agent for record in persisted.agents),
            *(record.agent for record in rebuilt.agents),
        }
    )
