"""Shared traversal helpers for graph-backed context/governance queries."""

from __future__ import annotations

from collections import deque


def edge_adjacency(
    edges: object,
    *,
    edge_kind: str,
) -> dict[str, tuple[str, ...]]:
    """Group outgoing targets by source for one edge kind."""
    adjacency: dict[str, list[str]] = {}
    for edge in _iter_edges(edges):
        if getattr(edge, "edge_kind", "") != edge_kind:
            continue
        adjacency.setdefault(str(edge.source_id), []).append(str(edge.target_id))
    return {key: tuple(value) for key, value in adjacency.items()}


def contains_parents(
    edges: object,
    *,
    child_prefix: str = "",
) -> dict[str, str]:
    """Map contained child node ids back to their parent node ids."""
    parents: dict[str, str] = {}
    for edge in _iter_edges(edges):
        if getattr(edge, "edge_kind", "") != "contains":
            continue
        target_id = str(edge.target_id)
        if child_prefix and not target_id.startswith(child_prefix):
            continue
        parents[target_id] = str(edge.source_id)
    return parents


def shortest_paths(
    start_id: str,
    adjacency: dict[str, tuple[str, ...]],
) -> dict[str, tuple[str, ...]]:
    """Return one shortest-path tree from a start node over adjacency."""
    paths = {start_id: (start_id,)}
    queue: deque[str] = deque([start_id])
    while queue:
        current = queue.popleft()
        current_path = paths[current]
        for neighbor in adjacency.get(current, ()):
            if neighbor in paths:
                continue
            paths[neighbor] = current_path + (neighbor,)
            queue.append(neighbor)
    return paths


def _iter_edges(edges: object):
    if isinstance(edges, list | tuple):
        return edges
    return tuple(edges or ())
