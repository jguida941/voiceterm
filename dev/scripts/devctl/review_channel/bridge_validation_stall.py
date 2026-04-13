"""Implementer-stall helpers for live bridge validation."""

from __future__ import annotations

from .peer_liveness import (
    IMPLEMENTER_STALL_MARKERS,
    REVIEWER_WAIT_STATE_MARKERS,
    ReviewerMode,
    reviewer_mode_is_active,
)


def _contains_any_marker(text: str, markers: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(marker in lower for marker in markers)


def _leading_section_excerpt(text: str, *, max_lines: int = 12) -> str:
    lines: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        lines.append(stripped)
        if len(lines) >= max_lines:
            break
    return "\n".join(lines)


def _implementer_completion_stall_error(
    *,
    snapshot,
    reviewer_mode: ReviewerMode,
) -> str | None:
    if not reviewer_mode_is_active(reviewer_mode):
        return None
    instruction = snapshot.sections.get("Current Instruction For Claude", "")
    poll_status = snapshot.sections.get("Poll Status", "")
    if _contains_any_marker(
        instruction,
        REVIEWER_WAIT_STATE_MARKERS,
    ) or _contains_any_marker(
        poll_status,
        REVIEWER_WAIT_STATE_MARKERS,
    ):
        return None
    claude_status = _leading_section_excerpt(snapshot.sections.get("Claude Status", ""))
    claude_ack = _leading_section_excerpt(snapshot.sections.get("Claude Ack", ""))
    combined = f"{claude_status}\n{claude_ack}".strip()
    if not _contains_any_marker(combined, IMPLEMENTER_STALL_MARKERS):
        return None
    return (
        "Implementer status/ack compatibility sections (`Claude Status` / "
        "`Claude Ack`) show completion-stall language while "
        "`Current Instruction For Claude` still assigns active work. Resume the "
        "active slice or record one concrete blocker/question instead of "
        "parking on reviewer polling."
    )
