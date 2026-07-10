"""Session-posture rendering helpers for session resume packets."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .session_resume_support import SessionCachePacket


def interaction_mode(packet: "SessionCachePacket") -> str:
    posture = getattr(packet, "session_posture", None)
    if posture is not None and posture.interaction_mode != "unresolved":
        return posture.interaction_mode
    return str(packet.operator_interaction_mode or "unresolved").strip()


def append_remote_control_boundaries(
    lines: list[str],
    packet: "SessionCachePacket",
) -> None:
    if interaction_mode(packet) != "remote_control":
        return
    lines.extend(
        [
            "",
            "### Remote Control Boundaries",
            "- no local GUI/process intervention",
            "- no ad hoc kill commands",
            "- no local commit/push authority",
            "- privileged, commit, and push work routes through typed `action_request` packets or bounded repo commands.",
        ]
    )


def append_packet_intent_anchors(
    lines: list[str],
    packet: "SessionCachePacket",
) -> None:
    anchors = tuple(getattr(packet, "packet_intent_anchors", ()) or ())
    if not anchors:
        return
    lines.append("")
    lines.append("### Packet Intent Anchors")
    for anchor in anchors[:5]:
        target = anchor.target_plan or "plan"
        lines.append(
            f"- `{anchor.packet_id}` {anchor.lifecycle_state}: "
            f"{target} ({anchor.summary})"
        )


def remote_control_routing_summary(packet: "SessionCachePacket") -> str:
    if interaction_mode(packet) == "remote_control":
        return "remote_control_routing=typed_action_request_or_bounded_repo_command"
    return "remote_control_routing=inactive"
