"""Rendering helpers for SessionCachePacket output formats.

Extracted from session_resume_support.py to keep both modules under the
Python soft file-size limit (350 lines).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .session_resume_support import SessionCachePacket


def render_markdown(packet: "SessionCachePacket") -> str:
    """Render a human-readable markdown summary of the session packet."""
    lines = [
        "## Session Resume",
        "",
        f"- **role**: {packet.role}",
        f"- **branch**: {packet.branch}",
        f"- **head**: `{packet.head_sha[:12]}`" if packet.head_sha else "- **head**: (unknown)",
        f"- **last_reviewed**: `{packet.last_reviewed_sha[:12]}`" if packet.last_reviewed_sha else "- **last_reviewed**: (none)",
        f"- **head_at_push**: `{packet.head_at_push_time[:12]}`" if packet.head_at_push_time else "- **head_at_push**: (none)",
        f"- **advisory**: {packet.advisory_action} / {packet.advisory_reason}",
        f"- **blockers**: {packet.blockers}",
        f"- **mode**: {packet.operator_interaction_mode}",
        f"- **phase**: {packet.resolved_phase}",
        f"- **ack**: {packet.ack_state}",
        f"- **guard_ok**: {packet.last_guard_ok}",
    ]
    if packet.next_guard_bundle:
        lines.append(f"- **guard_bundle**: {packet.next_guard_bundle}")
    lines.append("")
    if packet.current_instruction:
        lines.append("### Current instruction")
        lines.append(packet.current_instruction)
        lines.append("")
    if packet.open_findings:
        lines.append("### Open findings")
        lines.append(packet.open_findings)
        lines.append("")
    if packet.next_recommended_command:
        lines.append(f"**Next**: `{packet.next_recommended_command}`")
        lines.append("")
    elif packet.next_action:
        lines.append(f"**Next**: `{packet.next_action}`")
        lines.append("")
    if packet.key_rules:
        lines.append("### Key rules")
        for rule in packet.key_rules:
            lines.append(f"- {rule}")
        lines.append("")
    return "\n".join(lines)


def render_summary(packet: "SessionCachePacket") -> str:
    """Render a compact key=value summary for terminal output."""
    lines = [
        f"role={packet.role}",
        f"branch={packet.branch}",
        f"head={packet.head_sha[:12]}" if packet.head_sha else "head=unknown",
        f"last_reviewed={packet.last_reviewed_sha[:12]}" if packet.last_reviewed_sha else "last_reviewed=none",
        f"head_at_push={packet.head_at_push_time[:12]}" if packet.head_at_push_time else "head_at_push=none",
        f"action={packet.advisory_action}",
        f"reason={packet.advisory_reason}",
        f"blockers={packet.blockers}",
        f"mode={packet.operator_interaction_mode}",
        f"phase={packet.resolved_phase}",
        f"ack={packet.ack_state}",
        f"guard_ok={packet.last_guard_ok}",
        f"guard_bundle={packet.next_guard_bundle}" if packet.next_guard_bundle else "guard_bundle=none",
        f"next={packet.next_recommended_command or packet.next_action}",
    ]
    return "\n".join(lines)
