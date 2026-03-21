"""ZGraph-compatible concept layer over canonical pointer refs.

Derives subsystem concept nodes from directory structure and import edges.
Every concept resolves back to its member files via ``contains`` edges —
this is generated navigation, never an independent authority store.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import PurePosixPath

from .models import (
    EDGE_KIND_CONTAINS,
    EDGE_KIND_RELATED_TO,
    NODE_KIND_CONCEPT,
    NODE_KIND_SOURCE,
    GraphEdge,
    GraphNode,
)

# Directories that are too broad to be a useful concept on their own
_SKIP_CONCEPTS = frozenset((
    "dev", "dev/scripts", "dev/scripts/devctl",
    "dev/scripts/devctl/commands", "dev/scripts/checks",
    "rust", "rust/src", "rust/src/bin",
    "rust/src/bin/voiceterm", "app",
))

# Paths containing these segments are worktree artifacts, not real concepts
_WORKTREE_MARKERS = (".claude/worktrees/",)

# Minimum files required to form a concept (avoids noise)
_MIN_MEMBERS = 3

# How many directory levels deep to derive concepts
_MAX_DEPTH = 5


def _concept_key(rel_path: str) -> str | None:
    """Derive the concept directory key from a source file path."""
    parts = PurePosixPath(rel_path).parent.parts
    if not parts:
        return None
    for depth in range(min(len(parts), _MAX_DEPTH), 0, -1):
        candidate = "/".join(parts[:depth])
        if candidate not in _SKIP_CONCEPTS:
            return candidate
    return None


def _concept_label(key: str) -> str:
    """Generate a human-readable label from a concept directory key."""
    parts = key.split("/")
    meaningful = [p for p in parts if p not in ("src", "bin", "scripts")]
    return "/".join(meaningful[-2:]) if len(meaningful) > 1 else meaningful[-1]


def build_concept_nodes(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
) -> tuple[list[GraphNode], list[GraphEdge]]:
    """Derive concept nodes from source file directory structure.

    Returns (concept_nodes, concept_edges) to be appended to the main graph.
    """
    members: dict[str, list[GraphNode]] = defaultdict(list)
    for node in nodes:
        if node.node_kind != NODE_KIND_SOURCE:
            continue
        ref = node.canonical_pointer_ref
        if any(marker in ref for marker in _WORKTREE_MARKERS):
            continue
        key = _concept_key(ref)
        if key:
            members[key].append(node)

    cross_concept_imports: dict[tuple[str, str], int] = defaultdict(int)
    source_to_concept: dict[str, str] = {}
    for key, file_nodes in members.items():
        if len(file_nodes) < _MIN_MEMBERS:
            continue
        for n in file_nodes:
            source_to_concept[n.node_id] = key

    for edge in edges:
        src_concept = source_to_concept.get(edge.source_id)
        dst_concept = source_to_concept.get(edge.target_id)
        if src_concept and dst_concept and src_concept != dst_concept:
            pair = (min(src_concept, dst_concept), max(src_concept, dst_concept))
            cross_concept_imports[pair] += 1

    concept_nodes: list[GraphNode] = []
    concept_edges: list[GraphEdge] = []

    for key, file_nodes in sorted(members.items()):
        if len(file_nodes) < _MIN_MEMBERS:
            continue

        avg_temp = sum(n.temperature for n in file_nodes) / len(file_nodes)
        max_temp = max(n.temperature for n in file_nodes)
        agg_temp = round(min(avg_temp * 0.6 + max_temp * 0.4, 1.0), 3)

        total_hints = sum(int(n.metadata.get("hint_count", 0)) for n in file_nodes)
        changed_count = sum(1 for n in file_nodes if n.metadata.get("changed"))

        cid = f"concept:{key}"
        concept_nodes.append(
            GraphNode(
                node_id=cid,
                node_kind=NODE_KIND_CONCEPT,
                label=_concept_label(key),
                canonical_pointer_ref=key,
                provenance_ref="directory_structure",
                temperature=agg_temp,
                metadata={
                    "member_count": len(file_nodes),
                    "total_hints": total_hints,
                    "changed_files": changed_count,
                    "directory": key,
                },
            )
        )

        for file_node in file_nodes:
            concept_edges.append(
                GraphEdge(
                    source_id=cid,
                    target_id=file_node.node_id,
                    edge_kind=EDGE_KIND_CONTAINS,
                )
            )

    for (concept_a, concept_b), weight in sorted(
        cross_concept_imports.items(), key=lambda x: -x[1],
    ):
        if weight >= 2:
            concept_edges.append(
                GraphEdge(
                    source_id=f"concept:{concept_a}",
                    target_id=f"concept:{concept_b}",
                    edge_kind=EDGE_KIND_RELATED_TO,
                )
            )

    return concept_nodes, concept_edges
