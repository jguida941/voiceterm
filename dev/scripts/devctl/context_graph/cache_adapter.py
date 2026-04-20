"""Adapter helpers for loading cached context-graph snapshots."""

from __future__ import annotations

from collections.abc import Mapping

from .models import GraphEdge, GraphNode
from .snapshot_payload import _SNAPSHOT_DIR, resolve_head_sha, snapshot_cache_is_fresh
from .snapshot_store import load_context_graph_snapshot
from ..config import get_repo_root


def load_cached_context_graph() -> tuple[list[GraphNode], list[GraphEdge]] | None:
    """Load the latest cached context graph when it still matches HEAD."""
    try:
        repo_root = get_repo_root()
        snapshot_dir = repo_root / _SNAPSHOT_DIR
        if not snapshot_dir.is_dir():
            return None
        snapshot_files = list(snapshot_dir.glob("*.json"))
        if not snapshot_files:
            return None
        snapshot_files.sort(
            key=lambda path: path.stem.split("_", 1)[-1]
            if "_" in path.stem
            else path.stem
        )
        latest_path = snapshot_files[-1]
        head_sha = resolve_head_sha(repo_root)
        if not snapshot_cache_is_fresh(latest_path, head_sha):
            return None
        latest = load_context_graph_snapshot(latest_path)
        if latest.nodes and latest.edges:
            return (
                _coerce_cached_nodes(latest.nodes),
                _coerce_cached_edges(latest.edges),
            )
    except Exception:  # broad-except: allow reason=context-graph cache hydration must fail soft when cached snapshots are absent, stale, or partially unreadable fallback=return None
        pass
    return None


def _coerce_cached_nodes(rows: list[object]) -> list[GraphNode]:
    nodes: list[GraphNode] = []
    for row in rows:
        if isinstance(row, GraphNode):
            nodes.append(row)
            continue
        if not isinstance(row, Mapping):
            continue
        metadata = row.get("metadata")
        nodes.append(
            GraphNode(
                node_id=str(row.get("node_id") or ""),
                node_kind=str(row.get("node_kind") or ""),
                label=str(row.get("label") or ""),
                canonical_pointer_ref=str(row.get("canonical_pointer_ref") or ""),
                provenance_ref=str(row.get("provenance_ref") or ""),
                temperature=float(row.get("temperature") or 0.0),
                metadata=dict(metadata) if isinstance(metadata, Mapping) else {},
            )
        )
    return nodes


def _coerce_cached_edges(rows: list[object]) -> list[GraphEdge]:
    edges: list[GraphEdge] = []
    for row in rows:
        if isinstance(row, GraphEdge):
            edges.append(row)
            continue
        if not isinstance(row, Mapping):
            continue
        edges.append(
            GraphEdge(
                source_id=str(row.get("source_id") or ""),
                target_id=str(row.get("target_id") or ""),
                edge_kind=str(row.get("edge_kind") or ""),
            )
        )
    return edges
