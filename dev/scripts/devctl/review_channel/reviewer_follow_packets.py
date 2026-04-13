"""Packet-inbox projection helpers for reviewer-follow reports."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

from ..runtime.review_state_locator import load_current_review_state
from ..runtime.review_state_models import packet_inbox_from_mapping


@dataclass(frozen=True, slots=True)
class ReviewerFollowPacketProjection:
    pending_total: int
    attention_source: str
    attention_status: str = ""
    wake_reason: str = ""
    required_command: str = ""
    attention_revision: str = ""
    delivery_state: str = ""
    latest_finding_packet_id: str = ""
    current_instruction_packet_id: str = ""
    expired_unresolved_packet_ids: tuple[str, ...] = ()
    state: str = ""
    latest_packet_id: str = ""
    latest_kind: str = ""
    latest_from_agent: str = ""
    latest_summary: str = ""
    latest_posted_at_utc: str = ""
    actionable_packet_id: str = ""
    actionable_kind: str = ""
    actionable_summary: str = ""

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        for key, value in asdict(self).items():
            if isinstance(value, list):
                if not value:
                    continue
                payload[key] = value
                continue
            if isinstance(value, tuple):
                if not value:
                    continue
                payload[key] = list(value)
                continue
            if value == "":
                continue
            payload[key] = value
        return payload


def attach_reviewer_packets(*, report: dict[str, object], repo_root: Path) -> None:
    review_state = load_current_review_state(
        repo_root,
        prefer_cached_projection=False,
    )
    packet_inbox = packet_inbox_from_mapping(report.get("packet_inbox"))
    if packet_inbox is None and review_state is not None:
        packet_inbox = review_state.packet_inbox
    agent_attention = packet_inbox.for_agent("codex") if packet_inbox is not None else None
    if agent_attention is None:
        report["reviewer_packets"] = ReviewerFollowPacketProjection(
            pending_total=0,
            attention_source="typed_packet_inbox",
            state="unavailable",
        ).to_dict()
        return

    packet_rows = [
        packet
        for packet in report.get("packets", ())
        if isinstance(packet, Mapping)
    ]
    if not packet_rows and review_state is not None:
        packet_rows = [
            {
                "packet_id": packet.packet_id,
                "kind": packet.kind,
                "from_agent": packet.from_agent,
                "summary": packet.summary,
                "posted_at": packet.posted_at,
            }
            for packet in review_state.packets
        ]
    packet_index = {
        str(packet.get("packet_id") or "").strip(): packet
        for packet in packet_rows
        if str(packet.get("packet_id") or "").strip()
    }
    latest_finding = packet_index.get(agent_attention.latest_finding_packet_id)
    current_instruction = packet_index.get(
        agent_attention.current_instruction_packet_id
    )
    report["reviewer_packets"] = ReviewerFollowPacketProjection(
        pending_total=len(agent_attention.pending_actionable_packet_ids),
        attention_source="typed_packet_inbox",
        attention_status=agent_attention.attention_status,
        wake_reason=agent_attention.wake_reason,
        required_command=agent_attention.required_command,
        attention_revision=agent_attention.attention_revision,
        delivery_state=agent_attention.delivery_state,
        latest_finding_packet_id=agent_attention.latest_finding_packet_id,
        current_instruction_packet_id=agent_attention.current_instruction_packet_id,
        expired_unresolved_packet_ids=tuple(
            agent_attention.expired_unresolved_packet_ids
        ),
        latest_packet_id=str(latest_finding.get("packet_id") or "").strip()
        if latest_finding is not None
        else "",
        latest_kind=str(latest_finding.get("kind") or "").strip()
        if latest_finding is not None
        else "",
        latest_from_agent=str(latest_finding.get("from_agent") or "").strip()
        if latest_finding is not None
        else "",
        latest_summary=str(latest_finding.get("summary") or "").strip()
        if latest_finding is not None
        else "",
        latest_posted_at_utc=str(latest_finding.get("posted_at") or "").strip()
        if latest_finding is not None
        else "",
        actionable_packet_id=str(current_instruction.get("packet_id") or "").strip()
        if current_instruction is not None
        else "",
        actionable_kind=str(current_instruction.get("kind") or "").strip()
        if current_instruction is not None
        else "",
        actionable_summary=str(current_instruction.get("summary") or "").strip()
        if current_instruction is not None
        else "",
    ).to_dict()
