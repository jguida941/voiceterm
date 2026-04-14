"""Authority payload helpers for the session-resume surface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...platform.coordination_snapshot_models import CoordinationSnapshot
from ...runtime.review_state_models import PacketInboxState


@dataclass(frozen=True, slots=True)
class SessionResumeAuthorityPayload:
    reviewer_mode: str
    reviewer_freshness: str
    operator_interaction_mode: str
    attention: dict[str, Any]
    recovery_assessment: dict[str, Any]
    current_instruction: str
    instruction_revision: str
    ack_state: str
    coordination: CoordinationSnapshot | None
    packet_inbox: PacketInboxState | None
    next_command: str

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        payload["reviewer_mode"] = self.reviewer_mode
        payload["reviewer_freshness"] = self.reviewer_freshness
        payload["operator_interaction_mode"] = self.operator_interaction_mode
        payload["attention"] = self.attention
        payload["recovery_assessment"] = self.recovery_assessment
        payload["current_session"] = _build_current_session_payload(
            self.current_instruction,
            self.instruction_revision,
            self.ack_state,
        )
        payload["coordination"] = (
            self.coordination.to_dict() if self.coordination is not None else {}
        )
        payload["packet_inbox"] = _build_packet_inbox_payload(self.packet_inbox)
        payload["next_command"] = self.next_command
        return payload


def _build_current_session_payload(
    current_instruction: str,
    instruction_revision: str,
    ack_state: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    payload["current_instruction"] = current_instruction
    payload["current_instruction_revision"] = instruction_revision
    payload["implementer_ack_state"] = ack_state
    return payload


def _build_packet_inbox_payload(packet_inbox: PacketInboxState | None) -> dict[str, Any]:
    if packet_inbox is None:
        return {}
    payload: dict[str, Any] = {}
    payload["attention_revision"] = packet_inbox.attention_revision
    payload["agents"] = [
        _build_packet_inbox_agent_payload(record)
        for record in packet_inbox.agents
    ]
    return payload


def _build_packet_inbox_agent_payload(record: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    payload["agent"] = record.agent
    payload["current_instruction_packet_id"] = record.current_instruction_packet_id
    payload["latest_finding_packet_id"] = record.latest_finding_packet_id
    payload["pending_actionable_total"] = len(record.pending_actionable_packet_ids)
    payload["expired_unresolved_total"] = len(record.expired_unresolved_packet_ids)
    payload["attention_status"] = record.attention_status
    payload["wake_reason"] = record.wake_reason
    payload["required_command"] = record.required_command
    payload["delivery_state"] = record.delivery_state
    return payload
