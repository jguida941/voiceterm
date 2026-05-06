"""Context-graph query edge matching helpers."""

from __future__ import annotations

from .models import EDGE_KIND_GUARDS, EDGE_KIND_SCOPED_BY, GraphEdge

_MAX_MATCHED_EDGES = 200
_EDGE_KIND_PRIORITIES = (
    (EDGE_KIND_SCOPED_BY, 0),
    ("routes_to", 1),
    ("packet_handoff", 2),
    ("receipt_proves", 3),
    ("probe_finds", 4),
    ("guard_catches", 5),
    ("finding_blocks", 6),
    ("contract_reads", 7),
    ("contract_writes", 8),
    ("contains", 9),
    ("command_invokes", 10),
    ("test_covers", 11),
    ("workflow_runs", 12),
)


def matched_query_edges(
    edges: list[GraphEdge],
    *,
    matched_ids: set[str],
) -> tuple[list[GraphEdge], int]:
    matched_has_guard = any(nid.startswith("guard:") for nid in matched_ids)
    matched_edges = [
        edge
        for edge in edges
        if _edge_visible_for_match(
            edge,
            matched_ids=matched_ids,
            matched_has_guard=matched_has_guard,
        )
    ]
    total_matched_edge_count = len(matched_edges)
    if len(matched_edges) > _MAX_MATCHED_EDGES:
        matched_edges = sorted(matched_edges, key=query_edge_sort_key)[
            :_MAX_MATCHED_EDGES
        ]
    return matched_edges, total_matched_edge_count


def query_neighbor_ids(matched_edges: list[GraphEdge]) -> set[str]:
    neighbor_ids: set[str] = set()
    for edge in matched_edges:
        neighbor_ids.add(edge.source_id)
        neighbor_ids.add(edge.target_id)
    return neighbor_ids


def query_edge_sort_key(edge: GraphEdge) -> tuple[int, str, str, str]:
    return (_edge_priority(edge.edge_kind), edge.edge_kind, edge.source_id, edge.target_id)


def _edge_visible_for_match(
    edge: GraphEdge,
    *,
    matched_ids: set[str],
    matched_has_guard: bool,
) -> bool:
    if edge.edge_kind == EDGE_KIND_GUARDS and not matched_has_guard:
        return False
    return edge.source_id in matched_ids or edge.target_id in matched_ids


def _edge_priority(edge_kind: str) -> int:
    for candidate, priority in _EDGE_KIND_PRIORITIES:
        if edge_kind == candidate:
            return priority
    return 20


__all__ = ["matched_query_edges", "query_edge_sort_key", "query_neighbor_ids"]
