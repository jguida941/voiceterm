"""Query and bootstrap surfaces over the built context graph."""

from __future__ import annotations

import subprocess
from typing import Any

from ..config import get_repo_root
from ..governance.surfaces import load_surface_policy
from ..governance.push_policy import detect_push_enforcement_state, load_push_policy
from ..probe_topology_packet import (
    enrich_query_node,
    query_hot_index_ranking_summary,
    query_match_evidence,
    query_match_summary,
    query_ranking_summary,
    record_query_match_reason,
)
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
            hot_index_summary=_hot_index_summary(nodes, edges),
            evidence=["empty query: returning top-20 hottest nodes"],
        )

    # Normalize separators so "context-graph" matches "context_graph" and vice versa
    query_variants = {query_lower, query_lower.replace("-", "_"), query_lower.replace("_", "-")}

    matched_ids: set[str] = set()
    match_reasons: dict[str, list[str]] = {}
    for node in nodes:
        label_lower = node.label.lower()
        ref_lower = node.canonical_pointer_ref.lower()
        label_matches = [v for v in query_variants if v in label_lower]
        ref_matches = [v for v in query_variants if v in ref_lower]
        if label_matches or ref_matches:
            matched_ids.add(node.node_id)
        if label_matches:
            record_query_match_reason(
                match_reasons,
                node.node_id,
                f"label matched `{node.label}`",
            )
        if ref_matches:
            record_query_match_reason(
                match_reasons,
                node.node_id,
                f"canonical ref matched `{node.canonical_pointer_ref}`",
            )
        scope = str(node.metadata.get("scope", "")).lower()
        scope_matches = [v for v in query_variants if scope and v in scope]
        if scope_matches:
            matched_ids.add(node.node_id)
            record_query_match_reason(
                match_reasons,
                node.node_id,
                f"scope matched `{scope}`",
            )
        aliases = node.metadata.get("aliases", [])
        alias_matches: list[str] = []
        if isinstance(aliases, list):
            alias_matches = [
                str(alias) for alias in aliases if query_lower in str(alias).lower()
            ]
        if alias_matches:
            matched_ids.add(node.node_id)
            record_query_match_reason(
                match_reasons,
                node.node_id,
                "alias matched `"
                + ", ".join(alias_matches[:2])
                + "`",
            )

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
    edge_count_by_node: dict[str, int] = {}
    for edge in matched_edges:
        edge_count_by_node[edge.source_id] = edge_count_by_node.get(edge.source_id, 0) + 1
        edge_count_by_node[edge.target_id] = edge_count_by_node.get(edge.target_id, 0) + 1
    result_nodes = [
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
            [n for n in nodes if n.node_id in result_ids],
            key=lambda n: (-n.temperature, n.node_id),
        )
    ]

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
            "ranking_summary": query_ranking_summary(
                n,
                direct_match=False,
                connected_edge_count=0,
            ),
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
