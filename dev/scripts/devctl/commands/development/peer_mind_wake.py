"""Wake classification for `/develop` peer-mind context."""

from __future__ import annotations

import re

from .models import DevelopmentPeerMindEvent

_PACKET_PATTERN = re.compile(r"\brev_pkt_\d+\b")
_PACKET_TERMS = (
    "ack",
    "bundle",
    "debt",
    "finding",
    "inbox",
    "packet",
    "posted",
    "unacked",
)


def peer_mind_wake_hint(
    *,
    confidence: str,
    latest_summary: str,
    events: tuple[DevelopmentPeerMindEvent, ...],
) -> str:
    """Return the wake hint for a peer-mind projection."""
    if confidence != "fresh_auxiliary":
        return "refresh_agent_mind"

    text = " ".join(event.summary for event in events)
    if _is_packet_activity(f"{latest_summary} {text}"):
        return "peer_packet_activity"
    return "peer_recent_activity"


def _is_packet_activity(text: str) -> bool:
    normalized = text.lower()
    if _PACKET_PATTERN.search(text):
        return True
    return any(term in normalized for term in _PACKET_TERMS)


__all__ = ["peer_mind_wake_hint"]
