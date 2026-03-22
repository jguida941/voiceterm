"""Build a context graph from existing repo artifacts.

Reuses probe_topology_scan for code edges, script_catalog for guard/probe
registries, and INDEX.md for plan nodes.  Every node carries a
canonical_pointer_ref so the graph never becomes a second authority store.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from ..config import get_repo_root
from ..probe_topology_scan import (
    build_python_module_index,
    build_rust_suffix_index,
    collect_python_edges,
    collect_rust_edges,
    iter_source_files,
    repo_relative,
)
from ..script_catalog import (
    CHECK_SCRIPT_RELATIVE_PATHS,
    PROBE_SCRIPT_RELATIVE_PATHS,
)
from .artifact_inputs import resolve_graph_inputs
from .catalog_nodes import (
    collect_command_nodes,
    collect_guide_nodes,
    collect_plan_nodes,
)
from .concepts import build_concept_nodes
from .models import (
    EDGE_KIND_DOCUMENTED_BY,
    EDGE_KIND_IMPORTS,
    EDGE_KIND_ROUTES_TO,
    NODE_KIND_GUARD,
    NODE_KIND_PROBE,
    NODE_KIND_SOURCE,
    GraphEdge,
    GraphNode,
)

# Paths containing these segments are worktree artifacts, not canonical source
_WORKTREE_MARKERS = (".claude/worktrees/", "dev/repo_example_temp/")


_SEVERITY_BOOST = {"critical": 0.25, "high": 0.15, "medium": 0.08, "low": 0.03, "info": 0.0}


def _temperature_for_source(
    fan_in: int,
    fan_out: int,
    hint_count: int,
    changed: bool,
    severity: str = "",
) -> float:
    """Compute a 0.0-1.0 temperature score for a source file node."""
    score = 0.0
    score += min(hint_count * 0.15, 0.45)
    bridge = min(fan_in, fan_out)
    score += min(bridge * 0.05, 0.2)
    score += min((fan_in + fan_out) * 0.01, 0.15)
    if changed:
        score += 0.2
    score += _SEVERITY_BOOST.get(severity.lower(), 0.0)
    return min(round(score, 3), 1.0)


def _collect_source_nodes(
    hint_counts: dict[str, int],
    changed_paths: set[str],
    severity_by_file: dict[str, str] | None = None,
) -> tuple[list[GraphNode], list[GraphEdge], set[str]]:
    """Scan source files and import edges from probe_topology_scan."""
    source_files = iter_source_files()
    python_index = build_python_module_index(source_files["python"])
    rust_index = build_rust_suffix_index(source_files["rust"])
    py_edges, _ = collect_python_edges(source_files["python"], python_index)
    rs_edges, _ = collect_rust_edges(source_files["rust"], rust_index)

    all_paths: dict[str, str] = {}
    for p in source_files["python"]:
        rel = repo_relative(p)
        if not any(marker in rel for marker in _WORKTREE_MARKERS):
            all_paths[rel] = "python"
    for p in source_files["rust"]:
        rel = repo_relative(p)
        if not any(marker in rel for marker in _WORKTREE_MARKERS):
            all_paths[rel] = "rust"

    incoming: dict[str, set[str]] = defaultdict(set)
    outgoing: dict[str, set[str]] = defaultdict(set)
    for src, dst, _kind in py_edges | rs_edges:
        outgoing[src].add(dst)
        incoming[dst].add(src)

    nodes: list[GraphNode] = []
    node_ids: set[str] = set()
    sev_map = severity_by_file or {}
    for rel_path, language in sorted(all_paths.items()):
        fan_in = len(incoming.get(rel_path, set()))
        fan_out = len(outgoing.get(rel_path, set()))
        file_severity = sev_map.get(rel_path, "")
        nid = f"src:{rel_path}"
        meta: dict[str, object] = {
            "language": language,
            "fan_in": fan_in,
            "fan_out": fan_out,
            "hint_count": hint_counts.get(rel_path, 0),
            "changed": rel_path in changed_paths,
        }
        if file_severity:
            meta["severity"] = file_severity
        nodes.append(
            GraphNode(
                node_id=nid,
                node_kind=NODE_KIND_SOURCE,
                label=rel_path,
                canonical_pointer_ref=rel_path,
                provenance_ref="probe_topology_scan",
                temperature=_temperature_for_source(
                    fan_in, fan_out,
                    hint_counts.get(rel_path, 0),
                    rel_path in changed_paths,
                    severity=file_severity,
                ),
                metadata=meta,
            )
        )
        node_ids.add(nid)

    edges: list[GraphEdge] = [
        GraphEdge(source_id=f"src:{src}", target_id=f"src:{dst}", edge_kind=EDGE_KIND_IMPORTS)
        for src, dst, _kind in sorted(py_edges | rs_edges)
        if f"src:{src}" in node_ids and f"src:{dst}" in node_ids
    ]
    return nodes, edges, node_ids


def _collect_registry_nodes(
    registry: dict[str, str],
    node_kind: str,
    provenance: str,
    node_ids: set[str],
) -> tuple[list[GraphNode], list[GraphEdge]]:
    """Build nodes and routes_to edges for a script catalog registry."""
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    for name, rel_path in sorted(registry.items()):
        nid = f"{node_kind}:{name}"
        nodes.append(
            GraphNode(
                node_id=nid,
                node_kind=node_kind,
                label=name,
                canonical_pointer_ref=rel_path,
                provenance_ref=provenance,
                temperature=0.1,
            )
        )
        src_nid = f"src:{rel_path}"
        if src_nid in node_ids:
            edges.append(GraphEdge(source_id=nid, target_id=src_nid, edge_kind=EDGE_KIND_ROUTES_TO))
    return nodes, edges

def build_context_graph(
    *,
    hint_counts: dict[str, int] | None = None,
    changed_paths: set[str] | None = None,
) -> tuple[list[GraphNode], list[GraphEdge]]:
    """Build the full context graph from canonical repo artifacts.

    Returns (nodes, edges).  Every node carries canonical_pointer_ref and
    provenance_ref so callers can always trace back to the real artifact.

    When ``hint_counts`` and ``changed_paths`` are not provided, the builder
    prefers fresh ``file_topology.json`` artifact inputs over empty defaults.
    Falls back to empty inputs when the artifact is missing or stale.
    """
    repo_root = get_repo_root()
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    _deferred_doc_edges: list[tuple[str, str]] = []
    hint_counts, changed_paths, severity_by_file = resolve_graph_inputs(
        repo_root,
        hint_counts=hint_counts,
        changed_paths=changed_paths,
    )

    src_nodes, src_edges, node_ids = _collect_source_nodes(
        hint_counts,
        changed_paths,
        severity_by_file=severity_by_file,
    )
    nodes.extend(src_nodes)
    edges.extend(src_edges)

    plan_nodes, _deferred_doc_edges = collect_plan_nodes(repo_root)
    nodes.extend(plan_nodes)

    guard_nodes, guard_edges = _collect_registry_nodes(
        CHECK_SCRIPT_RELATIVE_PATHS, NODE_KIND_GUARD,
        "script_catalog.CHECK_SCRIPT_FILES", node_ids,
    )
    nodes.extend(guard_nodes)
    edges.extend(guard_edges)

    probe_nodes, probe_edges = _collect_registry_nodes(
        PROBE_SCRIPT_RELATIVE_PATHS, NODE_KIND_PROBE,
        "script_catalog.PROBE_SCRIPT_FILES", node_ids,
    )
    nodes.extend(probe_nodes)
    edges.extend(probe_edges)

    nodes.extend(collect_guide_nodes(repo_root))

    command_nodes, command_edges = collect_command_nodes(node_ids)
    nodes.extend(command_nodes)
    edges.extend(command_edges)

    concept_nodes, concept_edges = build_concept_nodes(nodes, edges)
    nodes.extend(concept_nodes)
    edges.extend(concept_edges)

    # Validate deferred documented_by edges — suppress orphans
    materialized_ids = {n.node_id for n in nodes}
    for source_id, target_id in _deferred_doc_edges:
        if target_id in materialized_ids:
            edges.append(GraphEdge(
                source_id=source_id,
                target_id=target_id,
                edge_kind=EDGE_KIND_DOCUMENTED_BY,
            ))

    return nodes, edges
