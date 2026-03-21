"""Build a context graph from existing repo artifacts.

Reuses probe_topology_scan for code edges, script_catalog for guard/probe
registries, and INDEX.md for plan nodes.  Every node carries a
canonical_pointer_ref so the graph never becomes a second authority store.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from ..config import get_repo_root
from ..governance.doc_authority_rules import parse_index_registry
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
from .concepts import build_concept_nodes
from .models import (
    EDGE_KIND_DOCUMENTED_BY,
    EDGE_KIND_IMPORTS,
    EDGE_KIND_ROUTES_TO,
    NODE_KIND_COMMAND,
    NODE_KIND_GUARD,
    NODE_KIND_GUIDE,
    NODE_KIND_PLAN,
    NODE_KIND_PROBE,
    NODE_KIND_SOURCE,
    GraphEdge,
    GraphNode,
)

# Keywords in INDEX.md "when agents read" that map to concept directory keys.
# Used to generate typed documented_by edges between plans and concepts.
_PLAN_CONCEPT_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("review.channel", "dev/scripts/devctl/review_channel"),
    ("review channel", "dev/scripts/devctl/review_channel"),
    ("autonomous", "dev/scripts/devctl/autonomy"),
    ("autonomy", "dev/scripts/devctl/autonomy"),
    ("operator console", "app/operator_console"),
    ("theme", "app/operator_console/theme"),
    ("memory", "rust/src/memory"),
    ("probe", "dev/scripts/checks"),
    ("governance", "dev/scripts/devctl/governance"),
    ("mobile", "app/ios"),
)

# Paths containing these segments are worktree artifacts, not canonical source
_WORKTREE_MARKERS = (".claude/worktrees/",)


def _parse_guide_files(repo_root: Path) -> list[Path]:
    """Collect guide markdown files."""
    guides_dir = repo_root / "dev" / "guides"
    if not guides_dir.is_dir():
        return []
    return sorted(guides_dir.glob("*.md"))


def _temperature_for_source(
    fan_in: int,
    fan_out: int,
    hint_count: int,
    changed: bool,
) -> float:
    """Compute a 0.0-1.0 temperature score for a source file node."""
    score = 0.0
    score += min(hint_count * 0.15, 0.45)
    bridge = min(fan_in, fan_out)
    score += min(bridge * 0.05, 0.2)
    score += min((fan_in + fan_out) * 0.01, 0.15)
    if changed:
        score += 0.2
    return min(round(score, 3), 1.0)


def _collect_source_nodes(
    hint_counts: dict[str, int],
    changed_paths: set[str],
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
    for rel_path, language in sorted(all_paths.items()):
        fan_in = len(incoming.get(rel_path, set()))
        fan_out = len(outgoing.get(rel_path, set()))
        nid = f"src:{rel_path}"
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
                ),
                metadata={
                    "language": language,
                    "fan_in": fan_in,
                    "fan_out": fan_out,
                    "hint_count": hint_counts.get(rel_path, 0),
                    "changed": rel_path in changed_paths,
                },
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
    """
    repo_root = get_repo_root()
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    _deferred_doc_edges: list[tuple[str, str]] = []

    src_nodes, src_edges, node_ids = _collect_source_nodes(
        hint_counts or {}, changed_paths or set(),
    )
    nodes.extend(src_nodes)
    edges.extend(src_edges)

    from ..repo_packs import active_path_config
    _ACTIVE_PLAN_ROLES = {"tracker", "spec"}
    path_config = active_path_config()
    index_path = repo_root / path_config.active_index_doc_rel
    registry = parse_index_registry(index_path)
    for path, row in registry.items():
        role = row.get("role", "")
        when = row.get("when", "").lower()
        is_active_plan = role in _ACTIVE_PLAN_ROLES
        if row.get("authority") == "canonical":
            temp = 0.6
        elif is_active_plan:
            temp = 0.3
        else:
            temp = 0.1
        plan_id = f"plan:{path}"
        scope_raw = row.get("scope", "")
        nodes.append(
            GraphNode(
                node_id=plan_id,
                node_kind=NODE_KIND_PLAN,
                label=path,
                canonical_pointer_ref=path,
                provenance_ref=str(index_path.relative_to(repo_root)),
                temperature=temp,
                metadata={
                    "role": role,
                    "authority": row.get("authority", ""),
                    "scope": scope_raw.replace("`", "").strip().strip(",").strip(),
                    "is_active_plan": is_active_plan,
                },
            )
        )
        for keyword, concept_dir in _PLAN_CONCEPT_KEYWORDS:
            if keyword in when:
                _deferred_doc_edges.append((plan_id, f"concept:{concept_dir}"))
                break

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

    for guide_path in _parse_guide_files(repo_root):
        rel = repo_relative(guide_path)
        nodes.append(
            GraphNode(
                node_id=f"guide:{rel}",
                node_kind=NODE_KIND_GUIDE,
                label=guide_path.stem,
                canonical_pointer_ref=rel,
                provenance_ref="dev/guides/",
                temperature=0.05,
            )
        )

    import importlib
    try:
        cli_mod = importlib.import_module("dev.scripts.devctl.cli")
        handlers = getattr(cli_mod, "COMMAND_HANDLERS", {})
    except (ImportError, ModuleNotFoundError):
        handlers = {}
    for cmd_name, handler in sorted(handlers.items()):
        normalized = cmd_name.replace("-", "_")
        handler_module = getattr(handler, "__module__", "") or ""
        # Handle both namespaces: dev.scripts.devctl.* (module) and devctl.* (script)
        if handler_module.startswith("dev.scripts.devctl."):
            suffix = handler_module[len("dev.scripts.devctl."):]
        elif handler_module.startswith("devctl."):
            suffix = handler_module[len("devctl."):]
        else:
            suffix = handler_module
        handler_path = "dev/scripts/devctl/" + suffix.replace(".", "/") + ".py"
        init_path = handler_path.replace(".py", "/__init__.py")
        if f"src:{init_path}" in node_ids and f"src:{handler_path}" not in node_ids:
            handler_path = init_path
        nid = f"cmd:{cmd_name}"
        nodes.append(
            GraphNode(
                node_id=nid,
                node_kind=NODE_KIND_COMMAND,
                label=cmd_name,
                canonical_pointer_ref=f"devctl {cmd_name}",
                provenance_ref="cli.COMMAND_HANDLERS",
                temperature=0.05,
                metadata={
                    "aliases": [normalized, cmd_name],
                    "handler_module": handler_module,
                },
            )
        )
        src_nid = f"src:{handler_path}"
        if src_nid in node_ids:
            edges.append(GraphEdge(
                source_id=nid,
                target_id=src_nid,
                edge_kind=EDGE_KIND_ROUTES_TO,
            ))

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
