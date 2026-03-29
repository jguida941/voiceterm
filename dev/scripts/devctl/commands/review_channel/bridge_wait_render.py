"""Markdown render helpers for bounded review-channel wait actions."""

from __future__ import annotations


def append_wait_state_markdown(lines: list[str], wait_state: object) -> None:
    """Render implementer-wait state when present."""
    if not isinstance(wait_state, dict):
        return

    lines.append("")
    lines.append("## Wait State")
    _append_common_wait_rows(lines, wait_state)
    _append_mode_specific_wait_rows(lines, wait_state)


def _append_common_wait_rows(lines: list[str], wait_state: dict[str, object]) -> None:
    lines.append(f"- mode: {wait_state.get('mode')}")
    lines.append(f"- stop_reason: {wait_state.get('stop_reason')}")
    lines.append(f"- polls_observed: {wait_state.get('polls_observed')}")
    lines.append(
        f"- wait_interval_seconds: {wait_state.get('wait_interval_seconds')}"
    )
    lines.append(f"- wait_timeout_seconds: {wait_state.get('wait_timeout_seconds')}")


def _append_mode_specific_wait_rows(
    lines: list[str],
    wait_state: dict[str, object],
) -> None:
    mode = str(wait_state.get("mode") or "")
    if mode == "reviewer_wait":
        _append_reviewer_wait_rows(lines, wait_state)
        return
    _append_implementer_wait_rows(lines, wait_state)


def _append_implementer_wait_rows(
    lines: list[str],
    wait_state: dict[str, object],
) -> None:
    lines.append(
        f"- baseline_instruction_revision: {wait_state.get('baseline_instruction_revision') or 'n/a'}"
    )
    lines.append(
        f"- current_instruction_revision: {wait_state.get('current_instruction_revision') or 'n/a'}"
    )
    _append_attention_wait_rows(lines, wait_state)
    lines.append(
        f"- reviewer_update_observed: {wait_state.get('reviewer_update_observed')}"
    )


def _append_reviewer_wait_rows(
    lines: list[str],
    wait_state: dict[str, object],
) -> None:
    lines.append(
        f"- baseline_worktree_hash: {wait_state.get('baseline_worktree_hash') or 'n/a'}"
    )
    lines.append(
        f"- current_worktree_hash: {wait_state.get('current_worktree_hash') or 'n/a'}"
    )
    lines.append(
        f"- baseline_reviewed_hash: {wait_state.get('baseline_reviewed_hash') or 'n/a'}"
    )
    lines.append(
        "- baseline_implementer_ack_revision: "
        f"{wait_state.get('baseline_implementer_ack_revision') or 'n/a'}"
    )
    lines.append(
        "- current_implementer_ack_revision: "
        f"{wait_state.get('current_implementer_ack_revision') or 'n/a'}"
    )
    _append_attention_wait_rows(lines, wait_state)
    lines.append(
        f"- implementer_update_observed: {wait_state.get('implementer_update_observed')}"
    )


def _append_attention_wait_rows(
    lines: list[str],
    wait_state: dict[str, object],
) -> None:
    lines.append(
        f"- baseline_attention_status: {wait_state.get('baseline_attention_status') or 'n/a'}"
    )
    lines.append(
        f"- current_attention_status: {wait_state.get('current_attention_status') or 'n/a'}"
    )
    lines.append(
        f"- baseline_attention_summary: {wait_state.get('baseline_attention_summary') or 'n/a'}"
    )
    lines.append(
        f"- current_attention_summary: {wait_state.get('current_attention_summary') or 'n/a'}"
    )
