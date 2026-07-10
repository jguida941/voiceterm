"""Compatibility aliases for implementer-owned bridge headings."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

_IMPLEMENTER_HEADING_ALIASES: dict[str, tuple[str, ...]] = {
    "Implementer Status": ("Claude Status",),
    "Implementer Questions": ("Claude Questions",),
    "Implementer Ack": ("Claude Ack",),
    "Current Instruction For Implementer": ("Current Instruction For Claude",),
}

_ALIAS_TO_CANONICAL = {
    alias: canonical
    for canonical, aliases in _IMPLEMENTER_HEADING_ALIASES.items()
    for alias in aliases
}


def canonical_bridge_heading(heading: str) -> str:
    """Return the canonical compatibility heading for one bridge section name."""
    normalized = str(heading).strip()
    return _ALIAS_TO_CANONICAL.get(normalized, normalized)


def bridge_heading_aliases(heading: str) -> tuple[str, ...]:
    """Return the canonical heading plus accepted aliases for one section."""
    canonical = canonical_bridge_heading(heading)
    aliases = tuple(
        alias
        for alias, mapped_heading in _ALIAS_TO_CANONICAL.items()
        if mapped_heading == canonical
    )
    return (canonical, *aliases)


def bridge_section_text(
    sections: Mapping[str, str],
    heading: str,
    *,
    default: str = "",
) -> str:
    """Read one canonical bridge section with legacy aliases as fallbacks."""
    for candidate in bridge_heading_aliases(heading):
        if candidate in sections:
            return str(sections.get(candidate) or "")
    return default


def normalize_bridge_headings(headings: Iterable[str]) -> list[str]:
    """Normalize a bridge heading iterable to canonical compatibility names."""
    return [canonical_bridge_heading(heading) for heading in headings]


def normalize_bridge_sections(sections: Mapping[str, str]) -> dict[str, str]:
    """Merge alias headings into canonical compatibility section keys."""
    normalized: dict[str, str] = {}
    for heading, value in sections.items():
        canonical = canonical_bridge_heading(heading)
        text = str(value or "")
        existing = normalized.get(canonical, "")
        if existing and text.strip():
            normalized[canonical] = f"{existing}\n\n{text}"
            continue
        if canonical not in normalized or text:
            normalized[canonical] = text
    return normalized
