"""Renderers for context-graph query results, bootstrap packets, and concept views.

Concept-view renderers (mermaid, dot) follow the same pattern as
``probe_topology_render.py`` and produce output compatible with the
existing ``dev/reports/probes/latest/`` artifact path.
"""

from __future__ import annotations

from typing import Any

from .models import (
    EDGE_KIND_DOCUMENTED_BY,
    EDGE_KIND_RELATED_TO,
    NODE_KIND_CONCEPT,
    GraphEdge,
    GraphNode,
    QueryResult,
)


def render_query_result_markdown(result: QueryResult) -> str:
    """Render a QueryResult as human-readable markdown."""
    lines: list[str] = []
    lines.append("# Context Graph — Discovery View")
    lines.append("")
    lines.append(f"**Query:** `{result.query or '(empty — hot index)'}`")
    lines.append("")
    lines.append(
        "> This is a discovery graph built from directory structure and import "
        "edges. Plan-to-concept edges are heuristic (keyword-matched from "
        "INDEX.md prose). Verify connections against canonical docs before "
        "treating them as authority."
    )
    lines.append("")

    summary = result.hot_index_summary
    lines.append("## Hot Index Summary")
    lines.append("")
    lines.append(f"- Total nodes: {summary.total_nodes}")
    lines.append(f"- Total edges: {summary.total_edges}")
    if summary.nodes_by_kind:
        for kind, count in sorted(summary.nodes_by_kind.items()):
            lines.append(f"  - {kind}: {count}")
    lines.append("")

    lines.append("## Evidence")
    lines.append("")
    for item in result.evidence:
        lines.append(f"- {item}")
    lines.append("")

    if result.matched_nodes:
        lines.append("## Matched Nodes")
        lines.append("")
        lines.append(
            "| Node | Kind | Temperature | Canonical Ref | Provenance |"
        )
        lines.append("|---|---|---|---|---|")
        for node in result.matched_nodes[:50]:
            lines.append(
                f"| `{node.label}` "
                f"| {node.node_kind} "
                f"| {node.temperature:.3f} "
                f"| `{node.canonical_pointer_ref}` "
                f"| {node.provenance_ref} |"
            )
        lines.append("")

    if result.edges:
        lines.append("## Edges")
        lines.append("")
        lines.append("| Source | Target | Kind |")
        lines.append("|---|---|---|")
        for edge in result.edges[:100]:
            lines.append(
                f"| `{edge.source_id}` | `{edge.target_id}` | {edge.edge_kind} |"
            )
        lines.append("")

    return "\n".join(lines)


def render_bootstrap_markdown(ctx: dict[str, Any]) -> str:
    """Render a bootstrap context packet as concise AI-ready markdown."""
    lines: list[str] = []
    lines.append("# Bootstrap Context")
    lines.append("")
    lines.append(f"**Repo:** {ctx.get('repo', '?')} | "
                 f"**Branch:** `{ctx.get('branch', '?')}` | "
                 f"**Bridge:** {'active' if ctx.get('bridge_active') else 'inactive'}")
    lines.append("")

    gs = ctx.get("graph_size", {})
    lines.append(f"**Graph:** {gs.get('source_files', 0)} source files, "
                 f"{gs.get('guards', 0)} guards, {gs.get('probes', 0)} probes, "
                 f"{gs.get('active_plans', 0)} plans, {gs.get('edges', 0)} edges")
    lines.append("")

    plans = ctx.get("active_plans", [])
    if plans:
        lines.append("## Active Plans")
        lines.append("")
        lines.append("| Path | Role | Scope |")
        lines.append("|---|---|---|")
        for p in plans:
            lines.append(f"| `{p['path']}` | {p.get('role', '')} | {p.get('scope', '')} |")
        lines.append("")

    hotspots = ctx.get("hotspots", [])
    if hotspots:
        lines.append("## Hotspots (highest temperature)")
        lines.append("")
        lines.append("| File | Temp | Fan-in | Fan-out |")
        lines.append("|---|---|---|---|")
        for h in hotspots:
            lines.append(f"| `{h['file']}` | {h['temperature']:.3f} | {h.get('fan_in', 0)} | {h.get('fan_out', 0)} |")
        lines.append("")

    cmds = ctx.get("key_commands", {})
    if cmds:
        lines.append("## Key Commands")
        lines.append("")
        for label, cmd in cmds.items():
            lines.append(f"- **{label}**: `{cmd}`")
        lines.append("")

    links = ctx.get("bootstrap_links", {})
    if links:
        lines.append("## Deep Links (load on demand)")
        lines.append("")
        for label, path in links.items():
            if path:
                lines.append(f"- **{label}**: `{path}`")
        lines.append("")

    usage = ctx.get("usage", "")
    if usage:
        lines.append(f"> {usage}")
        lines.append("")

    return "\n".join(lines)


def render_concept_mermaid(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
) -> str:
    """Render concept nodes and related_to/documented_by edges as mermaid."""
    concepts = [n for n in nodes if n.node_kind == NODE_KIND_CONCEPT]
    if not concepts:
        return "graph LR\n  empty[No concept nodes]\n"

    node_ids: dict[str, str] = {}
    lines = ["graph LR"]

    for i, c in enumerate(sorted(concepts, key=lambda n: -n.temperature)):
        nid = f"c{i}"
        node_ids[c.node_id] = nid
        members = c.metadata.get("member_count", 0)
        label = f"{c.label}\\n{members} files, temp {c.temperature:.2f}"
        lines.append(f'  {nid}["{label}"]')

    for plan in [n for n in nodes if n.node_kind != NODE_KIND_CONCEPT]:
        if any(e.source_id == plan.node_id and e.edge_kind == EDGE_KIND_DOCUMENTED_BY for e in edges):
            pid = f"p{len(node_ids)}"
            node_ids[plan.node_id] = pid
            lines.append(f'  {pid}["{plan.label}"]')

    for edge in edges:
        src = node_ids.get(edge.source_id)
        dst = node_ids.get(edge.target_id)
        if not src or not dst:
            continue
        if edge.edge_kind == EDGE_KIND_RELATED_TO:
            lines.append(f"  {src} --- {dst}")
        elif edge.edge_kind == EDGE_KIND_DOCUMENTED_BY:
            lines.append(f"  {src} -.-> {dst}")

    lines.append('  classDef hot fill:#f8d7da,stroke:#842029;')
    lines.append('  classDef warm fill:#fff3cd,stroke:#664d03;')
    lines.append('  classDef plan fill:#d1e7dd,stroke:#0f5132;')
    for c in concepts:
        nid = node_ids.get(c.node_id)
        if nid and c.temperature >= 0.2:
            lines.append(f"  class {nid} hot;")
        elif nid and c.temperature >= 0.1:
            lines.append(f"  class {nid} warm;")
    for n in nodes:
        pid = node_ids.get(n.node_id)
        if pid and n.node_kind != NODE_KIND_CONCEPT:
            lines.append(f"  class {pid} plan;")

    return "\n".join(lines) + "\n"


def render_concept_dot(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
) -> str:
    """Render concept nodes and edges as graphviz DOT."""
    concepts = [n for n in nodes if n.node_kind == NODE_KIND_CONCEPT]
    lines = ["digraph ConceptGraph {", '  graph [rankdir="LR"];']

    for c in sorted(concepts, key=lambda n: -n.temperature):
        members = c.metadata.get("member_count", 0)
        label = f"{c.label}\\n{members} files"
        attrs = ['shape="box"']
        if c.temperature >= 0.2:
            attrs.extend(['style="filled"', 'fillcolor="#f8d7da"'])
        elif c.temperature >= 0.1:
            attrs.extend(['style="filled"', 'fillcolor="#fff3cd"'])
        lines.append(f'  "{c.node_id}" [label="{label}", {", ".join(attrs)}];')

    for n in nodes:
        if n.node_kind == NODE_KIND_CONCEPT:
            continue
        if any(e.source_id == n.node_id and e.edge_kind == EDGE_KIND_DOCUMENTED_BY for e in edges):
            lines.append(f'  "{n.node_id}" [label="{n.label}", shape="ellipse", '
                         f'style="filled", fillcolor="#d1e7dd"];')

    for edge in edges:
        if edge.edge_kind == EDGE_KIND_RELATED_TO:
            lines.append(f'  "{edge.source_id}" -> "{edge.target_id}" [dir="none", style="dashed"];')
        elif edge.edge_kind == EDGE_KIND_DOCUMENTED_BY:
            lines.append(f'  "{edge.source_id}" -> "{edge.target_id}" [style="dotted"];')

    lines.append("}")
    return "\n".join(lines) + "\n"
