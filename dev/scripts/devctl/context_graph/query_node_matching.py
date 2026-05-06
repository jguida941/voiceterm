"""Context-graph query node matching helpers."""

from __future__ import annotations

from ..probe_topology.packet import record_query_match_reason
from .models import GraphNode
from .query_matching import (
    matching_aliases,
    matching_variants,
    query_terms,
    query_variants,
    ref_matches,
)


def matched_query_nodes(
    query_lower: str,
    nodes: list[GraphNode],
) -> tuple[set[str], dict[str, list[str]]]:
    terms = query_terms(query_lower)
    variants_by_term = {term: query_variants(term) for term in terms}
    matched_ids: set[str] = set()
    match_reasons: dict[str, list[str]] = {}
    for node in nodes:
        _record_node_match(
            node,
            query_lower=query_lower,
            variants_by_term=variants_by_term,
            matched_ids=matched_ids,
            match_reasons=match_reasons,
        )
    return matched_ids, match_reasons


def _record_node_match(
    node: GraphNode,
    *,
    query_lower: str,
    variants_by_term: dict[str, tuple[str, ...]],
    matched_ids: set[str],
    match_reasons: dict[str, list[str]],
) -> None:
    label_matches = matching_variants(node.label.lower(), variants_by_term)
    ref_match_values = ref_matches(
        node,
        node.canonical_pointer_ref.lower(),
        query_lower,
        variants_by_term,
    )
    scope_matches = matching_variants(
        str(node.metadata.get("scope", "")).lower(),
        variants_by_term,
    )
    alias_matches = _alias_matches(node, variants_by_term)
    if label_matches or ref_match_values or scope_matches or alias_matches:
        matched_ids.add(node.node_id)
    _record_match_reasons(
        node,
        label_matches=label_matches,
        ref_match_values=ref_match_values,
        scope_matches=scope_matches,
        alias_matches=alias_matches,
        match_reasons=match_reasons,
    )


def _alias_matches(
    node: GraphNode,
    variants_by_term: dict[str, tuple[str, ...]],
) -> list[str]:
    aliases = node.metadata.get("aliases", [])
    if not isinstance(aliases, list):
        return []
    return matching_aliases(aliases, variants_by_term)


def _record_match_reasons(
    node: GraphNode,
    *,
    label_matches: tuple[str, ...],
    ref_match_values: tuple[str, ...],
    scope_matches: tuple[str, ...],
    alias_matches: list[str],
    match_reasons: dict[str, list[str]],
) -> None:
    if label_matches:
        record_query_match_reason(
            match_reasons,
            node.node_id,
            f"label matched `{node.label}`",
        )
    if ref_match_values:
        record_query_match_reason(
            match_reasons,
            node.node_id,
            f"canonical ref matched `{node.canonical_pointer_ref}`",
        )
    if scope_matches:
        record_query_match_reason(
            match_reasons,
            node.node_id,
            f"scope matched `{node.metadata.get('scope', '')}`",
        )
    if alias_matches:
        record_query_match_reason(
            match_reasons,
            node.node_id,
            "alias matched `" + ", ".join(alias_matches[:2]) + "`",
        )


__all__ = ["matched_query_nodes"]
