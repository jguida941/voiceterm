"""Context-graph query result evidence helpers."""

from __future__ import annotations

from .models import EDGE_KIND_DOCUMENTED_BY, GraphEdge, GraphNode, HotIndexSummary


def query_confidence(matched_ids: set[str], matched_edges: list[GraphEdge]) -> str:
    if not matched_ids:
        return "no_match"
    if not matched_edges:
        return "low_confidence"
    non_heuristic = [
        edge for edge in matched_edges if edge.edge_kind != EDGE_KIND_DOCUMENTED_BY
    ]
    return "high" if non_heuristic else "low_confidence"


def query_node_count_evidence(
    visible_count: int,
    total_count: int,
    neighbor_count: int,
) -> str:
    if visible_count == total_count:
        return f"expanded to {neighbor_count} neighbor(s)"
    return (
        f"expanded to {neighbor_count} neighbor(s); "
        f"{visible_count} of {total_count} node(s) shown"
    )


def query_edge_count_evidence(visible_count: int, total_count: int) -> str:
    if visible_count == total_count:
        return f"{visible_count} connecting edge(s)"
    return f"{visible_count} of {total_count} connecting edge(s) shown"


def hot_index_summary(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
) -> HotIndexSummary:
    """Build the compact hot-index summary for any query result."""
    by_kind: dict[str, int] = {}
    for node in nodes:
        by_kind[node.node_kind] = by_kind.get(node.node_kind, 0) + 1
    edge_kinds: dict[str, int] = {}
    for edge in edges:
        edge_kinds[edge.edge_kind] = edge_kinds.get(edge.edge_kind, 0) + 1
    return HotIndexSummary(
        total_nodes=len(nodes),
        total_edges=len(edges),
        nodes_by_kind=by_kind,
        edges_by_kind=edge_kinds,
    )


__all__ = [
    "hot_index_summary",
    "query_confidence",
    "query_edge_count_evidence",
    "query_node_count_evidence",
]
