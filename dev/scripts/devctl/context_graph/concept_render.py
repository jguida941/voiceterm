"""Diagram renderers for concept-oriented context-graph views."""

from __future__ import annotations

from .models import (
    EDGE_KIND_DOCUMENTED_BY,
    EDGE_KIND_RELATED_TO,
    NODE_KIND_CONCEPT,
    GraphEdge,
    GraphNode,
)


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

    for index, concept in enumerate(sorted(concepts, key=lambda n: -n.temperature)):
        node_id = f"c{index}"
        node_ids[concept.node_id] = node_id
        members = concept.metadata.get("member_count", 0)
        label = f"{concept.label}\\n{members} files, temp {concept.temperature:.2f}"
        lines.append(f'  {node_id}["{label}"]')

    documented_nodes = [
        node
        for node in nodes
        if node.node_kind != NODE_KIND_CONCEPT
        and any(
            edge.source_id == node.node_id
            and edge.edge_kind == EDGE_KIND_DOCUMENTED_BY
            for edge in edges
        )
    ]
    for node in documented_nodes:
        plan_id = f"p{len(node_ids)}"
        node_ids[node.node_id] = plan_id
        lines.append(f'  {plan_id}["{node.label}"]')

    for edge in edges:
        source_id = node_ids.get(edge.source_id)
        target_id = node_ids.get(edge.target_id)
        if not source_id or not target_id:
            continue
        if edge.edge_kind == EDGE_KIND_RELATED_TO:
            lines.append(f"  {source_id} --- {target_id}")
        elif edge.edge_kind == EDGE_KIND_DOCUMENTED_BY:
            lines.append(f"  {source_id} -.-> {target_id}")

    lines.append('  classDef hot fill:#f8d7da,stroke:#842029;')
    lines.append('  classDef warm fill:#fff3cd,stroke:#664d03;')
    lines.append('  classDef plan fill:#d1e7dd,stroke:#0f5132;')
    for concept in concepts:
        node_id = node_ids.get(concept.node_id)
        if node_id and concept.temperature >= 0.2:
            lines.append(f"  class {node_id} hot;")
        elif node_id and concept.temperature >= 0.1:
            lines.append(f"  class {node_id} warm;")
    for node in nodes:
        plan_id = node_ids.get(node.node_id)
        if plan_id and node.node_kind != NODE_KIND_CONCEPT:
            lines.append(f"  class {plan_id} plan;")

    return "\n".join(lines) + "\n"


def render_concept_dot(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
) -> str:
    """Render concept nodes and edges as graphviz DOT."""
    concepts = [n for n in nodes if n.node_kind == NODE_KIND_CONCEPT]
    lines = ["digraph ConceptGraph {", '  graph [rankdir="LR"];']

    for concept in sorted(concepts, key=lambda n: -n.temperature):
        members = concept.metadata.get("member_count", 0)
        label = f"{concept.label}\\n{members} files"
        attrs = ['shape="box"']
        if concept.temperature >= 0.2:
            attrs.extend(['style="filled"', 'fillcolor="#f8d7da"'])
        elif concept.temperature >= 0.1:
            attrs.extend(['style="filled"', 'fillcolor="#fff3cd"'])
        lines.append(
            f'  "{concept.node_id}" [label="{label}", {", ".join(attrs)}];'
        )

    for node in nodes:
        if node.node_kind == NODE_KIND_CONCEPT:
            continue
        if any(
            edge.source_id == node.node_id
            and edge.edge_kind == EDGE_KIND_DOCUMENTED_BY
            for edge in edges
        ):
            lines.append(
                f'  "{node.node_id}" [label="{node.label}", shape="ellipse", '
                f'style="filled", fillcolor="#d1e7dd"];'
            )

    for edge in edges:
        if edge.edge_kind == EDGE_KIND_RELATED_TO:
            lines.append(
                f'  "{edge.source_id}" -> "{edge.target_id}" [dir="none", style="dashed"];'
            )
        elif edge.edge_kind == EDGE_KIND_DOCUMENTED_BY:
            lines.append(
                f'  "{edge.source_id}" -> "{edge.target_id}" [style="dotted"];'
            )

    lines.append("}")
    return "\n".join(lines) + "\n"
