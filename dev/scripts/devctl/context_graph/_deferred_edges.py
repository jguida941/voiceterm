"""Deferred edge materialization helpers for the context graph."""

from __future__ import annotations

from .models import EDGE_KIND_DOCUMENTED_BY, GraphEdge, GraphNode


def materialize_documented_by_edges(
    nodes: list[GraphNode],
    deferred_edges: list[tuple[str, str]],
) -> list[GraphEdge]:
    """Resolve deferred documented_by edges once all nodes are present."""
    materialized_ids = {node.node_id for node in nodes}
    return [
        GraphEdge(
            source_id=source_id,
            target_id=target_id,
            edge_kind=EDGE_KIND_DOCUMENTED_BY,
        )
        for source_id, target_id in deferred_edges
        if target_id in materialized_ids
    ]
