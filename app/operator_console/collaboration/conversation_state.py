"""Review-channel packets reshaped as a collaboration conversation timeline.

Reads the event store and presents each packet as a chat message
between team members (Codex, Claude, Cursor, Operator). The GUI
renders these as a conversation — but under the hood every message
is a ``devctl review-channel`` packet with full guard backing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dev.scripts.devctl.runtime import ReviewPacketState

from ..state.core.models import utc_timestamp
from ..state.review.review_state import load_review_packets


@dataclass(frozen=True)
class ConversationMessage:
    """One review-channel packet rendered for the conversation panel."""

    packet_id: str
    from_agent: str
    to_agent: str
    kind: str
    summary: str
    body_preview: str
    timestamp: str
    status: str
    policy_hint: str = ""
    guard_passed: bool = True


@dataclass(frozen=True)
class ConversationSnapshot:
    """Full conversation state for the chat timeline."""

    messages: tuple[ConversationMessage, ...] = ()
    last_refresh: str = ""


# Agent display names for the conversation view
AGENT_DISPLAY_NAMES: dict[str, str] = {
    "codex": "Codex",
    "claude": "Claude",
    "cursor": "Cursor",
    "operator": "Operator",
    "system": "System",
}

AGENT_ROLES: dict[str, str] = {
    "codex": "Reviewer",
    "claude": "Implementer",
    "cursor": "Editor",
    "operator": "Lead",
    "system": "System",
}


def _body_preview(body: str, *, limit: int = 200) -> str:
    """Collapse and truncate a packet body for the conversation timeline."""
    normalized = " ".join(body.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "\u2026"


def _packet_field(packet: dict[str, object] | ReviewPacketState, field_name: str) -> str:
    if isinstance(packet, ReviewPacketState):
        return str(getattr(packet, field_name, ""))
    return str(packet.get(field_name, ""))


def _parse_packet_to_message(
    packet: dict[str, object] | ReviewPacketState,
) -> ConversationMessage | None:
    """Convert one event-store packet dict into a ConversationMessage."""
    packet_id = _packet_field(packet, "packet_id")
    if not packet_id:
        return None
    return ConversationMessage(
        packet_id=packet_id,
        from_agent=_packet_field(packet, "from_agent") or "system",
        to_agent=_packet_field(packet, "to_agent") or "operator",
        kind=_packet_field(packet, "kind") or "system_notice",
        summary=_packet_field(packet, "summary"),
        body_preview=_body_preview(_packet_field(packet, "body")),
        timestamp=_packet_field(packet, "posted_at"),
        status=_packet_field(packet, "status") or "posted",
        policy_hint=_packet_field(packet, "policy_hint"),
    )


def build_conversation_snapshot(
    *,
    review_state_path: Path | None = None,
    history_packets: list[dict] | None = None,
) -> ConversationSnapshot:
    """Build a conversation snapshot from the review-channel event store.

    Accepts either a path to ``review_state.json`` or pre-loaded packets
    (for testing). Returns an empty snapshot when no data is available.
    """
    packets: list[dict[str, object] | ReviewPacketState] = []
    if history_packets is not None:
        packets = history_packets
    elif review_state_path is not None and review_state_path.is_file():
        try:
            packets = list(load_review_packets(review_state_path))
        except (OSError, ValueError):
            packets = []

    messages: list[ConversationMessage] = []
    for packet in packets:
        msg = _parse_packet_to_message(packet)
        if msg is not None:
            messages.append(msg)

    # Sort by timestamp (newest last for chat-style display)
    messages.sort(key=lambda m: m.timestamp)

    return ConversationSnapshot(
        messages=tuple(messages),
        last_refresh=utc_timestamp(),
    )
