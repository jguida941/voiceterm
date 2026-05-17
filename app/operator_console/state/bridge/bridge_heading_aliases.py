"""Stable bridge-heading compatibility helpers for the Operator Console."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

_IMPLEMENTER_HEADING_ALIASES: tuple[tuple[str, str], ...] = (
    ("Implementer Status", "Claude Status"),
    ("Implementer Questions", "Claude Questions"),
    ("Implementer Ack", "Claude Ack"),
    ("Current Instruction For Implementer", "Current Instruction For Claude"),
)


def canonical_bridge_heading(heading: str) -> str:
    """Return the canonical compatibility heading for one bridge section name."""
    normalized = str(heading).strip()
    for canonical, alias in _IMPLEMENTER_HEADING_ALIASES:
        if normalized == alias:
            return canonical
    return normalized


def bridge_heading_aliases(heading: str) -> tuple[str, ...]:
    """Return the canonical heading plus accepted aliases for one section."""
    canonical = canonical_bridge_heading(heading)
    candidates = [canonical]
    candidates.extend(
        alias
        for known_heading, alias in _IMPLEMENTER_HEADING_ALIASES
        if known_heading == canonical
    )
    return tuple(candidates)


def bridge_section_text(
    sections: Mapping[str, str],
    heading: str,
    *,
    default: str = "",
) -> str:
    """Read one canonical bridge section with legacy aliases as fallbacks."""
    normalized_sections = normalize_bridge_sections(sections)
    return normalized_sections.get(canonical_bridge_heading(heading), default)


def normalize_bridge_headings(headings: Iterable[str]) -> list[str]:
    """Normalize a bridge heading iterable to canonical compatibility names."""
    return [canonical_bridge_heading(heading) for heading in headings]


def normalize_bridge_sections(sections: Mapping[str, str]) -> dict[str, str]:
    """Merge alias headings into canonical compatibility section keys."""
    merged: dict[str, str] = {}
    for heading, value in sections.items():
        _merge_section_text(
            merged,
            heading=canonical_bridge_heading(heading),
            value=str(value or ""),
        )
    return merged


def _merge_section_text(
    sections: dict[str, str],
    *,
    heading: str,
    value: str,
) -> None:
    current = sections.get(heading, "")
    if current and value.strip():
        sections[heading] = "\n\n".join((current, value))
        return
    if heading not in sections or value:
        sections[heading] = value
