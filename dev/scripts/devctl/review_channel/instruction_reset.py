"""Helpers for clearing implementer-owned live state on instruction changes."""

from __future__ import annotations

from .reviewer_state_support import _replace_section

_PENDING_IMPLEMENTER_UPDATE = "- pending"
_IMPLEMENTER_RESET_HEADINGS = (
    "Claude Status",
    "Claude Ack",
)


def reset_implementer_sections_on_instruction_change(
    bridge_text: str,
    *,
    previous_instruction_revision: str,
    next_instruction_revision: str,
) -> str:
    """Clear implementer-owned live state when reviewer instruction changes."""
    if (
        not next_instruction_revision
        or next_instruction_revision == previous_instruction_revision
    ):
        return bridge_text
    updated_text = bridge_text
    for heading in _IMPLEMENTER_RESET_HEADINGS:
        updated_text = _replace_section(
            updated_text,
            heading=heading,
            body=_PENDING_IMPLEMENTER_UPDATE,
        )
    return updated_text
