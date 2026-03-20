"""Markdown render helpers for bounded review-channel wait actions."""

from __future__ import annotations


def append_wait_state_markdown(lines: list[str], wait_state: object) -> None:
    """Render implementer-wait state when present."""
    if not isinstance(wait_state, dict):
        return
    lines.append("")
    lines.append("## Wait State")
    lines.append(f"- mode: {wait_state.get('mode')}")
    lines.append(f"- stop_reason: {wait_state.get('stop_reason')}")
    lines.append(f"- polls_observed: {wait_state.get('polls_observed')}")
    lines.append(
        f"- wait_interval_seconds: {wait_state.get('wait_interval_seconds')}"
    )
    lines.append(f"- wait_timeout_seconds: {wait_state.get('wait_timeout_seconds')}")
    lines.append(
        f"- baseline_instruction_revision: {wait_state.get('baseline_instruction_revision') or 'n/a'}"
    )
    lines.append(
        f"- current_instruction_revision: {wait_state.get('current_instruction_revision') or 'n/a'}"
    )
    lines.append(
        f"- reviewer_update_observed: {wait_state.get('reviewer_update_observed')}"
    )
