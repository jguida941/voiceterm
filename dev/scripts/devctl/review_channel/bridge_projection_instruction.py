"""Instruction helpers for bridge compatibility projection metadata."""

from __future__ import annotations

from collections.abc import Mapping

from ..runtime.review_state_semantics import is_missing_instruction

PLACEHOLDER_INSTRUCTION_MARKERS = (
    "stop at a safe boundary",
    "relaunch before compaction",
    "await reviewer instruction refresh",
    "cut a checkpoint before continuing to edit",
)


def is_placeholder_instruction(current_instruction: str) -> bool:
    normalized = str(current_instruction or "").strip().lower()
    return any(marker in normalized for marker in PLACEHOLDER_INSTRUCTION_MARKERS)


def typed_instruction_explicitly_cleared(
    current_session: Mapping[str, object],
    *,
    projected_instruction: str = "",
) -> bool:
    if "current_instruction" not in current_session:
        return False
    instruction = str(current_session.get("current_instruction") or "").strip()
    if not is_missing_instruction(instruction):
        return False
    projected = str(projected_instruction or "").strip()
    if (
        projected
        and not is_missing_instruction(projected)
        and not is_placeholder_instruction(projected)
    ):
        return False
    return True
