"""Text-search query orchestration for context graph snapshots."""

from __future__ import annotations

from ..probe_topology.packet import (
    enrich_query_node,
    query_hot_index_ranking_summary,
)
from .models import GraphEdge, GraphNode, QueryResult
from .query_edge_matching import matched_query_edges, query_neighbor_ids
from .query_node_matching import matched_query_nodes
from .query_result_nodes import query_result_nodes
from .query_result_summary import (
    hot_index_summary,
    query_confidence,
    query_edge_count_evidence,
    query_node_count_evidence,
)


def query_context_graph(
    query: str,
    nodes: list[GraphNode],
    edges: list[GraphEdge],
) -> QueryResult:
    """Run a text query against the built graph, returning a targeted subgraph."""
    query_lower = query.lower().strip()
    if not query_lower:
        return _empty_query_result(query=query, nodes=nodes, edges=edges)

    matched_ids, match_reasons = matched_query_nodes(query_lower, nodes)
    matched_edges, total_matched_edge_count = matched_query_edges(
        edges,
        matched_ids=matched_ids,
    )
    neighbor_ids = query_neighbor_ids(matched_edges)
    result_nodes, total_result_node_count = query_result_nodes(
        nodes,
        matched_ids=matched_ids,
        neighbor_ids=neighbor_ids,
        matched_edges=matched_edges,
        match_reasons=match_reasons,
    )
    confidence = query_confidence(matched_ids, matched_edges)
    return QueryResult(
        query=query,
        matched_nodes=result_nodes,
        edges=matched_edges,
        hot_index_summary=hot_index_summary(nodes, edges),
        confidence=confidence,
        evidence=[
            f"matched {len(matched_ids)} direct node(s)",
            query_node_count_evidence(
                len(result_nodes),
                total_result_node_count,
                len(neighbor_ids),
            ),
            query_edge_count_evidence(len(matched_edges), total_matched_edge_count),
            f"confidence: {confidence}",
        ],
    )


def _empty_query_result(
    *,
    query: str,
    nodes: list[GraphNode],
    edges: list[GraphEdge],
) -> QueryResult:
    top_nodes = [
        enrich_query_node(
            node,
            match_summary="Returned from the hot index because the query was empty.",
            match_evidence=("empty query requested the hottest nodes",),
            ranking_summary=query_hot_index_ranking_summary(node),
        )
        for node in sorted(nodes, key=lambda n: -n.temperature)[:20]
    ]
    return QueryResult(
        query=query,
        matched_nodes=top_nodes,
        edges=[],
        hot_index_summary=hot_index_summary(nodes, edges),
        evidence=["empty query: returning top-20 hottest nodes"],
    )


__all__ = ["query_context_graph"]
