"""Query-term matching helpers for context-graph discovery."""

from __future__ import annotations

from .models import NODE_KIND_DATACLASS_FIELD, GraphNode


def query_terms(query_lower: str) -> tuple[str, ...]:
    """Return the full query plus individual terms for multi-symbol discovery."""
    tokens = tuple(part for part in query_lower.split() if part)
    if len(tokens) <= 1:
        return (query_lower,)
    return (query_lower, *tokens)


def query_variants(term: str) -> set[str]:
    """Normalize separators so related symbol shapes still match."""
    variants = {
        term,
        term.replace("-", "_"),
        term.replace("_", "-"),
    }
    if " " in term:
        variants.add(term.replace(" ", "_"))
        variants.add(term.replace(" ", "-"))
    return {variant for variant in variants if variant}


def matching_variants(
    haystack: str,
    variants_by_term: dict[str, set[str]],
) -> list[str]:
    if not haystack:
        return []

    matches: list[str] = []
    for variants in variants_by_term.values():
        for variant in variants:
            if variant in haystack and variant not in matches:
                matches.append(variant)
    return matches


def matching_aliases(
    aliases: list[object],
    variants_by_term: dict[str, set[str]],
) -> list[str]:
    matches: list[str] = []
    for alias in aliases:
        alias_text = str(alias).lower()
        if not alias_text:
            continue
        matched = matching_variants(alias_text, variants_by_term)
        if matched and str(alias) not in matches:
            matches.append(str(alias))
    return matches


def ref_matches(
    node: GraphNode,
    ref_lower: str,
    query_lower: str,
    variants_by_term: dict[str, set[str]],
) -> list[str]:
    """Keep field-node canonical refs from swamping parent-contract queries."""
    if node.node_kind == NODE_KIND_DATACLASS_FIELD and "." not in query_lower:
        return []
    return matching_variants(ref_lower, variants_by_term)
