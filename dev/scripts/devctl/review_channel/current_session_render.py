"""Render-focused current-session helpers for review-channel projections."""

from __future__ import annotations

from .pending_packets import live_pending_packets


def append_current_session_markdown(
    lines: list[str],
    current_session: object,
) -> None:
    """Render the typed current-session summary into latest.md output."""
    if not isinstance(current_session, dict):
        return
    lines.append("")
    lines.append("## Current Session")
    lines.append(
        "- instruction_revision: "
        f"{current_session.get('current_instruction_revision') or 'n/a'}"
    )
    lines.append(
        "- implementer_status: "
        f"{current_session.get('implementer_status') or 'n/a'}"
    )
    lines.append(
        "- implementer_ack_state: "
        f"{current_session.get('implementer_ack_state') or 'n/a'}"
    )
    if current_session.get("implementer_session_state"):
        lines.append(
            "- implementer_session_state: "
            f"{current_session.get('implementer_session_state') or 'n/a'}"
        )
    lines.append(
        "- last_reviewed_scope: "
        f"{current_session.get('last_reviewed_scope') or 'n/a'}"
    )


def current_focus_line(review_state: dict[str, object]) -> str:
    """Return the best current instruction from typed state or fallbacks."""
    current_session = review_state.get("current_session", {})
    if isinstance(current_session, dict):
        current_instruction = str(
            current_session.get("current_instruction") or ""
        ).strip()
        if current_instruction:
            return current_instruction
    bridge = review_state.get("bridge", {})
    if isinstance(bridge, dict):
        current_instruction = str(bridge.get("current_instruction") or "").strip()
        if current_instruction:
            return current_instruction
    queue = review_state.get("queue", {})
    if isinstance(queue, dict):
        derived_next_instruction = str(
            queue.get("derived_next_instruction") or ""
        ).strip()
        if derived_next_instruction:
            return derived_next_instruction
    packets = review_state.get("packets")
    if not isinstance(packets, list):
        return "(missing)"
    pending_packet = next(iter(live_pending_packets(packets)), None)
    if isinstance(pending_packet, dict):
        summary = str(pending_packet.get("summary") or "").strip()
        if summary:
            return summary
    return "(missing)"
