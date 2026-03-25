"""Query and bootstrap surfaces over the built context graph."""

from __future__ import annotations

import subprocess
from typing import Any

from ..config import get_repo_root
from ..governance.surfaces import load_surface_policy
from ..governance.push_policy import detect_push_enforcement_state, load_push_policy
from .models import (
    EDGE_KIND_GUARDS,
    NODE_KIND_GUARD,
    NODE_KIND_PLAN,
    NODE_KIND_PROBE,
    NODE_KIND_SOURCE,
    BootstrapContext,
    GraphEdge,
    GraphNode,
    GraphSize,
    HotIndexSummary,
    QueryResult,
)
from .startup_signals import load_bootstrap_quality_signals

_USAGE = (
    "Start from this packet for repo-level orientation. "
    "Follow bootstrap_links when the task requires full authority from "
    "the canonical docs. Use `context-graph --query <term>` for targeted "
    "subgraphs on specific files, MPs, guards, or subsystems."
)


def query_context_graph(
    query: str,
    nodes: list[GraphNode],
    edges: list[GraphEdge],
) -> QueryResult:
    """Run a text query against the built graph, returning a targeted subgraph.

    Matches node labels and canonical_pointer_refs against the query string.
    Returns matched nodes sorted by temperature (hottest first) plus their
    immediate edge neighborhood.
    """
    query_lower = query.lower().strip()
    if not query_lower:
        top_nodes = sorted(nodes, key=lambda n: -n.temperature)[:20]
        return QueryResult(
            query=query,
            matched_nodes=top_nodes,
            edges=[],
            hot_index_summary=_hot_index_summary(nodes, edges),
            evidence=["empty query: returning top-20 hottest nodes"],
        )

    # Normalize separators so "context-graph" matches "context_graph" and vice versa
    query_variants = {query_lower, query_lower.replace("-", "_"), query_lower.replace("_", "-")}

    matched_ids: set[str] = set()
    for node in nodes:
        label_lower = node.label.lower()
        ref_lower = node.canonical_pointer_ref.lower()
        if any(v in label_lower or v in ref_lower for v in query_variants):
            matched_ids.add(node.node_id)
        scope = str(node.metadata.get("scope", "")).lower()
        if scope and any(v in scope for v in query_variants):
            matched_ids.add(node.node_id)
        aliases = node.metadata.get("aliases", [])
        if isinstance(aliases, list) and any(query_lower in str(a).lower() for a in aliases):
            matched_ids.add(node.node_id)

    neighbor_ids: set[str] = set()
    matched_edges: list[GraphEdge] = []
    # Guard edges (guard → file) create N_guards × N_files cartesian noise
    # when querying for source files. Keep them when the query matched a guard
    # node directly (the user asked about a guard). Filter otherwise.
    matched_has_guard = any(nid.startswith("guard:") for nid in matched_ids)
    for edge in edges:
        if edge.edge_kind == EDGE_KIND_GUARDS and not matched_has_guard:
            continue
        if edge.source_id in matched_ids or edge.target_id in matched_ids:
            neighbor_ids.add(edge.source_id)
            neighbor_ids.add(edge.target_id)
            matched_edges.append(edge)

    result_ids = matched_ids | neighbor_ids
    result_nodes = sorted(
        [n for n in nodes if n.node_id in result_ids],
        key=lambda n: (-n.temperature, n.node_id),
    )

    if not matched_ids:
        confidence = "no_match"
    elif not matched_edges:
        confidence = "low_confidence"
    else:
        # If all edges are heuristic documented_by, downgrade to low_confidence
        from .models import EDGE_KIND_DOCUMENTED_BY
        non_heuristic = [e for e in matched_edges if e.edge_kind != EDGE_KIND_DOCUMENTED_BY]
        confidence = "high" if non_heuristic else "low_confidence"

    return QueryResult(
        query=query,
        matched_nodes=result_nodes,
        edges=matched_edges,
        hot_index_summary=_hot_index_summary(nodes, edges),
        confidence=confidence,
        evidence=[
            f"matched {len(matched_ids)} direct node(s)",
            f"expanded to {len(neighbor_ids)} neighbor(s)",
            f"{len(matched_edges)} connecting edge(s)",
            f"confidence: {confidence}",
        ],
    )


def _current_branch(repo_root) -> str:
    """Detect the current git branch."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, cwd=repo_root, timeout=5,
            check=False,
        )
        return result.stdout.strip() or "unknown"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return "unknown"


def _detect_bridge_liveness(repo_root) -> bool:
    """Check real bridge liveness via reviewer mode, not just file existence."""
    bridge_path = repo_root / "bridge.md"
    if not bridge_path.exists():
        return False
    try:
        from ..review_channel.peer_liveness import reviewer_mode_is_active
        from ..review_channel.handoff import extract_bridge_snapshot, summarize_bridge_liveness

        text = bridge_path.read_text(encoding="utf-8")
        snapshot = extract_bridge_snapshot(text)
        liveness = summarize_bridge_liveness(snapshot)
        return reviewer_mode_is_active(liveness.reviewer_mode)
    except (OSError, ImportError, ValueError):
        return False


def _load_policy_context(repo_root) -> tuple[dict[str, str], dict[str, str | None]]:
    """Load key commands and bootstrap links from governance repo policy."""
    try:
        surface_ctx = load_surface_policy(repo_root=repo_root).context
    except (OSError, ValueError):
        surface_ctx = {}

    key_block = str(surface_ctx.get("key_commands_block", ""))
    commands: dict[str, str] = {}
    label = ""
    for line in key_block.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            label = stripped.lstrip("# ").strip().lower().replace(" ", "_")
        elif stripped and label:
            commands[label] = stripped
            label = ""

    process_doc = str(surface_ctx.get("process_doc", "AGENTS.md"))
    execution_tracker = str(
        surface_ctx.get("execution_tracker_doc", "dev/active/MASTER_PLAN.md")
    )
    active_registry = str(
        surface_ctx.get("active_registry_doc", "dev/active/INDEX.md")
    )
    links: dict[str, str | None] = {
        "sdlc_policy": process_doc,
        "execution_state": execution_tracker,
        "plan_registry": active_registry,
    }
    return commands, links


def build_bootstrap_context(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
) -> BootstrapContext:
    """Build a slim startup context packet for AI agent bootstrap.

    Provides repo identity, active plans with MP scopes, hotspot files,
    key commands (from governance policy), and deep links. Uses real bridge
    liveness detection instead of file existence.
    """
    repo_root = get_repo_root()
    bridge_active = _detect_bridge_liveness(repo_root)

    plan_nodes = [
        n for n in nodes
        if n.node_kind == NODE_KIND_PLAN and n.metadata.get("is_active_plan")
    ]
    top_hotspots = sorted(
        [n for n in nodes if n.node_kind == NODE_KIND_SOURCE and n.temperature >= 0.3],
        key=lambda n: -n.temperature,
    )[:10]

    policy_commands, policy_links = _load_policy_context(repo_root)
    policy_links["bridge"] = "bridge.md" if bridge_active else None
    push_enforcement = detect_push_enforcement_state(
        load_push_policy(repo_root=repo_root),
        repo_root=repo_root,
    )
    quality_signals = load_bootstrap_quality_signals(repo_root)

    return BootstrapContext(
        repo=repo_root.name,
        branch=_current_branch(repo_root),
        bridge_active=bridge_active,
        graph_size=GraphSize(
            source_files=sum(1 for n in nodes if n.node_kind == NODE_KIND_SOURCE),
            guards=sum(1 for n in nodes if n.node_kind == NODE_KIND_GUARD),
            probes=sum(1 for n in nodes if n.node_kind == NODE_KIND_PROBE),
            active_plans=len(plan_nodes),
            edges=len(edges),
        ),
        active_plans=_plan_summaries(plan_nodes),
        hotspots=_hotspot_summaries(top_hotspots),
        key_commands=policy_commands,
        bootstrap_links=policy_links,
        push_enforcement=push_enforcement,
        usage=_USAGE,
        quality_signals=quality_signals,
    )


def _plan_summaries(plan_nodes: list[GraphNode]) -> list[dict[str, object]]:
    return [
        {
            "path": p.canonical_pointer_ref,
            "role": p.metadata.get("role", ""),
            "authority": p.metadata.get("authority", ""),
            "scope": p.metadata.get("scope", ""),
        }
        for p in plan_nodes
    ]


def _hotspot_summaries(hotspots: list[GraphNode]) -> list[dict[str, object]]:
    return [
        {
            "file": n.canonical_pointer_ref,
            "temperature": n.temperature,
            "fan_in": n.metadata.get("fan_in", 0),
            "fan_out": n.metadata.get("fan_out", 0),
        }
        for n in hotspots
    ]


def _hot_index_summary(
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
