"""Typed rehydration render helpers for session-resume output."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .session_resume_support import SessionCachePacket


def typed_rehydration_lines(packet: "SessionCachePacket") -> list[str]:
    continuation = getattr(packet, "agent_session_continuation", None)
    if continuation is None:
        return []
    lines = [
        "",
        "### Typed Rehydration",
        f"- **continuation_id**: `{continuation.continuation_id}`",
        f"- **mode**: `{continuation.continuation_mode}`",
        f"- **continuation_hash**: `{continuation.continuation_hash[:16]}`",
        f"- **agent**: `{continuation.agent_id}` / `{continuation.role}`",
        f"- **dirty_paths**: {_dirty_paths_display(continuation)}",
        f"- **authority_result**: `{continuation.authority_result}`",
        f"- **proof_command**: `{continuation.resume_command}`",
    ]
    if continuation.bootstrap_hash:
        lines.append(f"- **bootstrap_hash**: `{continuation.bootstrap_hash[:16]}`")
    if continuation.last_seen_packet_id:
        lines.append(f"- **last_seen_packet**: `{continuation.last_seen_packet_id}`")
    if continuation.last_acknowledged_packet_id:
        lines.append(
            "- **last_acknowledged_packet**: "
            f"`{continuation.last_acknowledged_packet_id}`"
        )
    return lines


def typed_rehydration_summary(packet: "SessionCachePacket") -> str:
    continuation = getattr(packet, "agent_session_continuation", None)
    if continuation is None:
        return "typed_rehydration=none"
    digest = (
        continuation.continuation_hash[:12]
        if continuation.continuation_hash
        else "none"
    )
    return f"typed_rehydration={continuation.continuation_mode}:{digest}"


def _dirty_paths_display(continuation: object) -> str:
    if getattr(continuation, "dirty_paths_status", "") == "unknown":
        return "unknown"
    return str(getattr(continuation, "dirty_paths_count", 0))


__all__ = ["typed_rehydration_lines", "typed_rehydration_summary"]
