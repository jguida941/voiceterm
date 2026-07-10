"""Bridge section replacement helpers for reviewer checkpoint writes."""

from __future__ import annotations

from dataclasses import dataclass

from .bridge_heading_aliases import bridge_heading_aliases
from .reviewer_state_support import _replace_section


@dataclass(frozen=True, slots=True)
class ReviewerCheckpointSections:
    current_verdict: str
    open_findings: str
    current_instruction: str
    reviewed_scope_body: str


def replace_reviewer_checkpoint_sections(
    text: str,
    sections: ReviewerCheckpointSections,
) -> str:
    text = _replace_section_with_aliases(
        text,
        heading="Current Verdict",
        body=sections.current_verdict.strip(),
    )
    text = _replace_section_with_aliases(
        text,
        heading="Open Findings",
        body=sections.open_findings.strip(),
    )
    text = _replace_section_with_aliases(
        text,
        heading="Current Instruction For Implementer",
        body=sections.current_instruction.strip(),
    )
    return _replace_section_with_aliases(
        text,
        heading="Last Reviewed Scope",
        body=sections.reviewed_scope_body,
    )


def _replace_section_with_aliases(text: str, *, heading: str, body: str) -> str:
    last_error: ValueError | None = None
    for candidate in bridge_heading_aliases(heading):
        try:
            return _replace_section(text, heading=candidate, body=body)
        except ValueError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    raise ValueError(f"Unable to locate `{heading}` in the markdown bridge.")


__all__ = [
    "ReviewerCheckpointSections",
    "replace_reviewer_checkpoint_sections",
]
