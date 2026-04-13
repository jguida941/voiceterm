"""Validation helpers for bridge-compatibility projections."""

from __future__ import annotations

from collections.abc import Mapping
import re

from .bridge_projection_contract import FLAT_BRIDGE_SECTION_ORDER
from .bridge_heading_aliases import canonical_bridge_heading
from .bridge_projection_sections import projection_sections
from .bridge_section_validation import find_embedded_markdown_headings
from .bridge_sanitize import (
    BRIDGE_ALLOWED_H2,
    BRIDGE_SECTION_LINE_LIMITS,
    sanitize_bridge_sections,
)

_H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def bridge_projection_parts(
    *,
    raw_sections: Mapping[str, str],
    current_session: Mapping[str, object],
    reviewer_runtime: Mapping[str, object],
    packets: list[dict[str, object]] | None = None,
) -> tuple[dict[str, str], tuple[str, ...]]:
    sections, sanitized_sections = sanitize_bridge_sections(
        projection_sections(
            raw_sections,
            current_session=current_session,
            reviewer_runtime=reviewer_runtime,
            packets=packets,
        ),
        section_line_limits=BRIDGE_SECTION_LINE_LIMITS,
    )
    validate_flat_bridge_sections(sections)
    return sections, tuple(sanitized_sections)


def bridge_projection_drop_headings(bridge_text: str) -> tuple[str, ...]:
    return tuple(
        heading
        for heading in dict.fromkeys(
            match.group(1).strip() for match in _H2_RE.finditer(bridge_text)
        )
        if canonical_bridge_heading(heading) not in BRIDGE_ALLOWED_H2
    )


def validate_flat_bridge_sections(sections: Mapping[str, str]) -> None:
    errors: list[str] = []
    for heading in FLAT_BRIDGE_SECTION_ORDER:
        heading_hits = find_embedded_markdown_headings(str(sections.get(heading, "")))
        if not heading_hits:
            continue
        quoted = "; ".join(f"`{line}`" for line in heading_hits)
        errors.append(f"`{heading}`: {quoted}")
    if errors:
        raise ValueError(
            "Typed bridge projection rejected embedded markdown headings in fixed "
            "sections: " + "; ".join(errors)
        )
