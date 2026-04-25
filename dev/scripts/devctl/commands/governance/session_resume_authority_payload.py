"""Authority payload helpers for the session-resume surface."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass

from ...platform.coordination_snapshot_models import CoordinationSnapshot
from ...review_channel.collaboration_provider import (
    coding_provider_from_review_state,
    reviewer_provider_from_review_state,
)
from ...runtime.review_packet_inbox import (
    packet_inbox_from_review_state,
    summarize_packet_attention_open_findings,
)
from ...runtime.review_state_models import (
    AgentAttentionRecord,
    PacketInboxState,
    packet_inbox_from_mapping,
)


@dataclass(frozen=True, slots=True)
class SessionResumeCurrentSessionPayload:
    current_instruction: str
    current_instruction_revision: str
    implementer_ack_state: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SessionResumePacketInboxAgentPayload:
    agent: str
    current_instruction_packet_id: str
    latest_finding_packet_id: str
    pending_actionable_total: int
    expired_unresolved_total: int
    attention_status: str
    wake_reason: str
    required_command: str
    delivery_state: str

    @classmethod
    def from_record(
        cls,
        record: AgentAttentionRecord,
    ) -> SessionResumePacketInboxAgentPayload:
        return cls(
            agent=record.agent,
            current_instruction_packet_id=record.current_instruction_packet_id,
            latest_finding_packet_id=record.latest_finding_packet_id,
            pending_actionable_total=len(record.pending_actionable_packet_ids),
            expired_unresolved_total=len(record.expired_unresolved_packet_ids),
            attention_status=record.attention_status,
            wake_reason=record.wake_reason,
            required_command=record.required_command,
            delivery_state=record.delivery_state,
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SessionResumePacketInboxPayload:
    attention_revision: str
    agents: tuple[SessionResumePacketInboxAgentPayload, ...] = ()

    @classmethod
    def from_state(
        cls,
        packet_inbox: PacketInboxState | None,
    ) -> SessionResumePacketInboxPayload | None:
        if packet_inbox is None:
            return None
        return cls(
            attention_revision=packet_inbox.attention_revision,
            agents=tuple(
                SessionResumePacketInboxAgentPayload.from_record(record)
                for record in packet_inbox.agents
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "attention_revision": self.attention_revision,
            "agents": [agent.to_dict() for agent in self.agents],
        }


@dataclass(frozen=True, slots=True)
class SessionResumeReviewStateContext:
    packet_inbox: PacketInboxState | None
    open_findings: str


@dataclass(frozen=True, slots=True)
class SessionResumeAuthorityPayload:
    reviewer_mode: str
    reviewer_freshness: str
    operator_interaction_mode: str
    observed_control_topology: str
    implementation_permission: str
    attention: Mapping[str, object]
    recovery_assessment: Mapping[str, object]
    current_session: SessionResumeCurrentSessionPayload
    coordination: CoordinationSnapshot | None
    packet_inbox: SessionResumePacketInboxPayload | None
    next_command: str
    governance: Mapping[str, object] | None = None
    collaboration: Mapping[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        payload["reviewer_mode"] = self.reviewer_mode
        payload["reviewer_freshness"] = self.reviewer_freshness
        payload["operator_interaction_mode"] = self.operator_interaction_mode
        payload["observed_control_topology"] = self.observed_control_topology
        payload["implementation_permission"] = self.implementation_permission
        payload["attention"] = dict(self.attention)
        payload["recovery_assessment"] = dict(self.recovery_assessment)
        payload["current_session"] = self.current_session.to_dict()
        payload["coordination"] = (
            self.coordination.to_dict() if self.coordination is not None else {}
        )
        payload["packet_inbox"] = (
            self.packet_inbox.to_dict() if self.packet_inbox is not None else {}
        )
        payload["next_command"] = self.next_command
        if self.governance:
            payload["governance"] = dict(self.governance)
        if self.collaboration:
            payload["collaboration"] = dict(self.collaboration)
        return payload


_READ_ONLY_SESSION_ROLES = frozenset({"dashboard", "observer"})


def build_session_resume_review_state_context(
    review_state_payload: Mapping[str, object],
    *,
    fallback_open_findings: str,
    role: str,
) -> SessionResumeReviewStateContext:
    payload = dict(review_state_payload)
    attention_agent = _attention_agent_for_role(payload, role=role)
    packet_inbox = None
    if payload:
        packet_inbox = packet_inbox_from_review_state(
            payload
        ) or packet_inbox_from_mapping(payload.get("packet_inbox"))
    open_findings = summarize_packet_attention_open_findings(
        payload,
        fallback=fallback_open_findings,
        agent=attention_agent,
    )
    return SessionResumeReviewStateContext(
        packet_inbox=packet_inbox,
        open_findings=open_findings,
    )


def _attention_agent_for_role(
    review_state_payload: Mapping[str, object],
    *,
    role: str,
) -> str:
    normalized_role = str(role or "").strip().lower()
    if normalized_role == "reviewer":
        return reviewer_provider_from_review_state(review_state_payload)
    if normalized_role in _READ_ONLY_SESSION_ROLES:
        return "operator"
    return coding_provider_from_review_state(review_state_payload)
