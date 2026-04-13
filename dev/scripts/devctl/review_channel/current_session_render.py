"""Render-focused current-session helpers for review-channel projections."""

from __future__ import annotations

from .current_session_support import event_current_instruction


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
    """Return the best current instruction from the typed control line."""
    current_session = review_state.get("current_session", {})
    if isinstance(current_session, dict):
        current_instruction = str(
            current_session.get("current_instruction") or ""
        ).strip()
        if current_instruction:
            return current_instruction
    current_instruction = event_current_instruction(review_state)
    if current_instruction:
        return current_instruction
    return "(missing)"
