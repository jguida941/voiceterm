"""Context-graph query result node selection."""

from __future__ import annotations

from ..probe_topology.packet import (
    enrich_query_node,
    query_match_evidence,
    query_match_summary,
    query_ranking_summary,
)
from .models import NODE_KIND_CONCEPT, GraphEdge, GraphNode

_MAX_RESULT_NODES = 120


def query_result_nodes(
    nodes: list[GraphNode],
    *,
    matched_ids: set[str],
    neighbor_ids: set[str],
    matched_edges: list[GraphEdge],
    match_reasons: dict[str, list[str]],
) -> tuple[list[GraphNode], int]:
    result_ids = matched_ids | neighbor_ids
    edge_count_by_node = _edge_count_by_node(matched_edges)
    all_result_nodes = [
        enrich_query_node(
            node,
            match_summary=query_match_summary(
                node,
                direct_match=node.node_id in matched_ids,
                reasons=match_reasons.get(node.node_id, []),
            ),
            match_evidence=query_match_evidence(
                node,
                direct_match=node.node_id in matched_ids,
                reasons=match_reasons.get(node.node_id, []),
            ),
            ranking_summary=query_ranking_summary(
                node,
                direct_match=node.node_id in matched_ids,
                connected_edge_count=edge_count_by_node.get(node.node_id, 0),
            ),
        )
        for node in sorted(
            [item for item in nodes if item.node_id in result_ids],
            key=lambda item: (-item.temperature, item.node_id),
        )
    ]
    result_nodes = _bounded_result_nodes(
        all_result_nodes,
        pinned_ids={
            node.node_id
            for node in all_result_nodes
            if node.node_kind == NODE_KIND_CONCEPT and node.node_id in matched_ids
        },
    )
    return result_nodes, len(all_result_nodes)


def _edge_count_by_node(edges: list[GraphEdge]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for edge in edges:
        counts[edge.source_id] = counts.get(edge.source_id, 0) + 1
        counts[edge.target_id] = counts.get(edge.target_id, 0) + 1
    return counts


def _bounded_result_nodes(
    nodes: list[GraphNode],
    *,
    pinned_ids: set[str],
) -> list[GraphNode]:
    """Return bounded query nodes while preserving direct concept matches."""
    if len(nodes) <= _MAX_RESULT_NODES:
        return nodes
    pinned = [node for node in nodes if node.node_id in pinned_ids]
    if len(pinned) >= _MAX_RESULT_NODES:
        return sorted(
            pinned[:_MAX_RESULT_NODES],
            key=lambda n: (-n.temperature, n.node_id),
        )

    selected = list(nodes[:_MAX_RESULT_NODES])
    selected_ids = {node.node_id for node in selected}
    for pinned_node in pinned:
        if pinned_node.node_id in selected_ids:
            continue
        _replace_last_unpinned(selected, selected_ids, pinned_node, pinned_ids)
    return sorted(selected, key=lambda n: (-n.temperature, n.node_id))


def _replace_last_unpinned(
    selected: list[GraphNode],
    selected_ids: set[str],
    pinned_node: GraphNode,
    pinned_ids: set[str],
) -> None:
    for index in range(len(selected) - 1, -1, -1):
        evicted = selected[index]
        if evicted.node_id in pinned_ids:
            continue
        selected_ids.remove(evicted.node_id)
        selected[index] = pinned_node
        selected_ids.add(pinned_node.node_id)
        return


__all__ = ["query_result_nodes"]
