"""Helpers for clearing implementer-owned live state on instruction changes."""

from __future__ import annotations

from .bridge_heading_aliases import bridge_heading_aliases
from .reviewer_state_support import _replace_section

_IMPLEMENTER_RESET_BODIES = (
    ("Implementer Status", "- pending"),
    ("Implementer Questions", "- None recorded."),
    ("Implementer Ack", "- pending"),
)


def reset_implementer_sections(
    bridge_text: str,
) -> str:
    """Rewrite implementer-owned live sections to the canonical pending state."""
    updated_text = bridge_text
    for heading, body in _IMPLEMENTER_RESET_BODIES:
        updated_text = _replace_bridge_section_alias(
            updated_text,
            heading=heading,
            body=body,
        )
    return updated_text


def _replace_bridge_section_alias(
    bridge_text: str,
    *,
    heading: str,
    body: str,
) -> str:
    for candidate in bridge_heading_aliases(heading):
        if f"## {candidate}" in bridge_text:
            return _replace_section(bridge_text, heading=candidate, body=body)
    return _replace_section(bridge_text, heading=heading, body=body)


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
    return reset_implementer_sections(bridge_text)
