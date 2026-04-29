"""Deterministic graph-walk navigation over ContextGraphSnapshot inputs."""

from __future__ import annotations

import heapq
from dataclasses import asdict, dataclass

from .models import (
    EDGE_KIND_DOCUMENTED_BY,
    EDGE_KIND_RELATED_TO,
    NODE_KIND_COMMAND,
    NODE_KIND_FINDING,
    NODE_KIND_AGENT,
    NODE_KIND_GUARD,
    NODE_KIND_INTENT,
    NODE_KIND_PACKET,
    NODE_KIND_PLAN,
    NODE_KIND_PLAN_ROW,
    NODE_KIND_PROBE,
    NODE_KIND_RECEIPT,
    NODE_KIND_SOURCE,
    NODE_KIND_TYPED_CONTRACT,
    GraphEdge,
    GraphNode,
)

_HEURISTIC_EDGE_KINDS = frozenset({EDGE_KIND_DOCUMENTED_BY, EDGE_KIND_RELATED_TO})
_NODE_KIND_ALIASES = {
    "command": NODE_KIND_COMMAND,
    "commands": NODE_KIND_COMMAND,
    "file": NODE_KIND_SOURCE,
    "source": NODE_KIND_SOURCE,
    "source_file": NODE_KIND_SOURCE,
    "contract": NODE_KIND_TYPED_CONTRACT,
    "typed_contract": NODE_KIND_TYPED_CONTRACT,
    "guard": NODE_KIND_GUARD,
    "guards": NODE_KIND_GUARD,
    "probe": NODE_KIND_PROBE,
    "probes": NODE_KIND_PROBE,
    "packet": NODE_KIND_PACKET,
    "packets": NODE_KIND_PACKET,
    "finding": NODE_KIND_FINDING,
    "findings": NODE_KIND_FINDING,
    "plan": NODE_KIND_PLAN,
    "plan_row": NODE_KIND_PLAN_ROW,
    "plan-row": NODE_KIND_PLAN_ROW,
    "task": NODE_KIND_PLAN_ROW,
    "intent": NODE_KIND_INTENT,
    "intents": NODE_KIND_INTENT,
    "receipt": NODE_KIND_RECEIPT,
    "receipts": NODE_KIND_RECEIPT,
    "agent": NODE_KIND_AGENT,
    "agents": NODE_KIND_AGENT,
}
_EDGE_COSTS = {
    "contains": 0.7,
    "routes_to": 0.8,
    "scoped_by": 0.9,
    "contract_reads": 0.9,
    "contract_writes": 0.9,
    "packet_handoff": 1.0,
    "command_invokes": 1.0,
    "guard_catches": 1.0,
    "probe_finds": 1.0,
    "finding_blocks": 1.0,
    "receipt_proves": 1.0,
    "test_covers": 1.2,
    "workflow_runs": 1.2,
    "guards": 1.3,
    "calls": 1.5,
    "imports": 1.8,
    "related_to": 2.4,
    "documented_by": 3.0,
}


@dataclass(frozen=True, slots=True)
class GraphWalkStep:
    """One cited node in a graph walk."""

    node_id: str
    node_kind: str
    label: str
    canonical_pointer_ref: str
    provenance_ref: str
    inbound_edge_kind: str = ""
    inbound_direction: str = ""


@dataclass(frozen=True, slots=True)
class GraphWalkResult:
    """A bounded cited path through the generated context graph."""

    from_query: str
    to_query: str
    strategy: str
    confidence: str
    path: tuple[GraphWalkStep, ...]
    evidence: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["path"] = [asdict(step) for step in self.path]
        payload["evidence"] = list(self.evidence)
        payload["warnings"] = list(self.warnings)
        return payload


def walk_context_graph(
    from_query: str,
    to_query: str,
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    *,
    strategy: str = "cost-ranked",
    max_depth: int = 6,
) -> GraphWalkResult:
    """Return a deterministic cited graph path from one query to another."""
    node_by_id = {node.node_id: node for node in nodes}
    start_nodes = _resolve_start_nodes(from_query, nodes)
    if not start_nodes:
        return _no_match_result(
            from_query=from_query,
            to_query=to_query,
            strategy=strategy,
            reason=f"no start node matched `{from_query}`",
        )
    target_matches = [node for node in nodes if _node_matches_target(node, to_query)]
    if not target_matches:
        return _no_match_result(
            from_query=from_query,
            to_query=to_query,
            strategy=strategy,
            reason=f"no target node matched `{to_query}`",
        )
    target_ids = {node.node_id for node in target_matches}
    adjacency = _walk_adjacency(edges)
    best = None
    for start_node in start_nodes[:10]:
        candidate = _walk_from_start(
            start_node.node_id,
            target_ids=target_ids,
            adjacency=adjacency,
            node_by_id=node_by_id,
            strategy=strategy,
            max_depth=max_depth,
        )
        if candidate is None:
            continue
        if best is None or candidate[0] < best[0]:
            best = candidate
    if best is None:
        return _no_match_result(
            from_query=from_query,
            to_query=to_query,
            strategy=strategy,
            reason=(
                f"matched {len(start_nodes)} start node(s) and "
                f"{len(target_matches)} target node(s), but no path within depth {max_depth}"
            ),
        )

    _, path_ids, inbound_edges = best
    steps = _render_steps(path_ids, inbound_edges, node_by_id)
    used_edge_kinds = tuple(step.inbound_edge_kind for step in steps if step.inbound_edge_kind)
    confidence = (
        "low_confidence"
        if any(kind in _HEURISTIC_EDGE_KINDS for kind in used_edge_kinds)
        else "high"
    )
    return GraphWalkResult(
        from_query=from_query,
        to_query=to_query,
        strategy=strategy,
        confidence=confidence,
        path=steps,
        evidence=(
            f"resolved {len(start_nodes)} start candidate(s)",
            f"resolved {len(target_matches)} target candidate(s)",
            f"path length: {max(len(steps) - 1, 0)} edge(s)",
            "edge kinds: " + (", ".join(used_edge_kinds) if used_edge_kinds else "none"),
            "context graph is a generated read model; follow canonical refs for authority",
        ),
    )


def render_graph_walk_markdown(result: GraphWalkResult) -> str:
    """Render one graph walk as concise markdown."""
    lines = [
        "# Context Graph Walk",
        "",
        f"- **from**: `{result.from_query}`",
        f"- **to**: `{result.to_query}`",
        f"- **strategy**: `{result.strategy}`",
        f"- **confidence**: `{result.confidence}`",
        "",
        "## Evidence",
        "",
    ]
    for item in result.evidence:
        lines.append(f"- {item}")
    if result.warnings:
        lines.extend(["", "## Warnings", ""])
        for item in result.warnings:
            lines.append(f"- {item}")
    if result.path:
        lines.extend(["", "## Path", ""])
        lines.append("| Step | Node | Kind | Via | Canonical Ref |")
        lines.append("|---:|---|---|---|---|")
        for index, step in enumerate(result.path, start=1):
            via = step.inbound_edge_kind or "start"
            if step.inbound_direction:
                via = f"{via} ({step.inbound_direction})"
            lines.append(
                f"| {index} | `{step.label}` | {step.node_kind} | {via} | "
                f"`{step.canonical_pointer_ref}` |"
            )
    else:
        lines.extend(["", "## Path", "", "- No path found."])
    return "\n".join(lines)


def _resolve_start_nodes(query: str, nodes: list[GraphNode]) -> list[GraphNode]:
    normalized = _normalize(query)
    exact: list[GraphNode] = []
    partial: list[GraphNode] = []
    for node in nodes:
        values = _node_match_values(node)
        normalized_values = {_normalize(value) for value in values if value}
        if normalized in normalized_values:
            exact.append(node)
            continue
        if any(normalized and normalized in value for value in normalized_values):
            partial.append(node)
    selected = exact or partial
    return sorted(selected, key=lambda node: (-node.temperature, node.node_id))


def _node_matches_target(node: GraphNode, target_query: str) -> bool:
    normalized = _normalize(target_query)
    kind_alias = _NODE_KIND_ALIASES.get(normalized)
    if kind_alias and node.node_kind == kind_alias:
        return True
    if normalized == _normalize(node.node_kind):
        return True
    return normalized in {_normalize(value) for value in _node_match_values(node) if value}


def _node_match_values(node: GraphNode) -> tuple[str, ...]:
    values = [node.node_id, node.label, node.canonical_pointer_ref]
    aliases = node.metadata.get("aliases") if isinstance(node.metadata, dict) else None
    if isinstance(aliases, list):
        values.extend(str(alias) for alias in aliases)
    return tuple(values)


def _walk_adjacency(
    edges: list[GraphEdge],
) -> dict[str, list[tuple[str, GraphEdge, str]]]:
    adjacency: dict[str, list[tuple[str, GraphEdge, str]]] = {}
    for edge in edges:
        adjacency.setdefault(edge.source_id, []).append((edge.target_id, edge, "forward"))
        adjacency.setdefault(edge.target_id, []).append((edge.source_id, edge, "reverse"))
    for neighbors in adjacency.values():
        neighbors.sort(key=lambda item: (_edge_cost(item[1], "cost-ranked"), item[0]))
    return adjacency


def _walk_from_start(
    start_id: str,
    *,
    target_ids: set[str],
    adjacency: dict[str, list[tuple[str, GraphEdge, str]]],
    node_by_id: dict[str, GraphNode],
    strategy: str,
    max_depth: int,
) -> tuple[tuple[float, int, str], tuple[str, ...], dict[str, tuple[GraphEdge, str]]] | None:
    queue: list[tuple[float, int, str, tuple[str, ...]]] = [(0.0, 0, start_id, (start_id,))]
    best_cost_by_node = {start_id: 0.0}
    inbound_by_path_key: dict[tuple[str, ...], dict[str, tuple[GraphEdge, str]]] = {
        (start_id,): {}
    }
    while queue:
        cost, depth, node_id, path = heapq.heappop(queue)
        if node_id in target_ids and depth > 0:
            return (
                (cost, depth, node_id),
                path,
                inbound_by_path_key[path],
            )
        if depth >= max_depth:
            continue
        for neighbor_id, edge, direction in adjacency.get(node_id, ()):
            if neighbor_id in path or neighbor_id not in node_by_id:
                continue
            next_cost = cost + _edge_cost(edge, strategy)
            previous = best_cost_by_node.get(neighbor_id)
            if previous is not None and previous <= next_cost:
                continue
            next_path = path + (neighbor_id,)
            inbound = dict(inbound_by_path_key[path])
            inbound[neighbor_id] = (edge, direction)
            inbound_by_path_key[next_path] = inbound
            best_cost_by_node[neighbor_id] = next_cost
            heapq.heappush(queue, (next_cost, depth + 1, neighbor_id, next_path))
    return None


def _render_steps(
    path_ids: tuple[str, ...],
    inbound_edges: dict[str, tuple[GraphEdge, str]],
    node_by_id: dict[str, GraphNode],
) -> tuple[GraphWalkStep, ...]:
    steps: list[GraphWalkStep] = []
    for node_id in path_ids:
        node = node_by_id[node_id]
        inbound = inbound_edges.get(node_id)
        edge_kind = inbound[0].edge_kind if inbound is not None else ""
        direction = inbound[1] if inbound is not None else ""
        steps.append(
            GraphWalkStep(
                node_id=node.node_id,
                node_kind=node.node_kind,
                label=node.label,
                canonical_pointer_ref=node.canonical_pointer_ref,
                provenance_ref=node.provenance_ref,
                inbound_edge_kind=edge_kind,
                inbound_direction=direction,
            )
        )
    return tuple(steps)


def _edge_cost(edge: GraphEdge, strategy: str) -> float:
    if strategy == "bfs":
        return 1.0
    # A* is currently deterministic cost-ranked traversal with explainable
    # edge weights; later heuristics must remain evidence-backed.
    return _EDGE_COSTS.get(edge.edge_kind, 2.0)


def _normalize(value: object) -> str:
    return str(value or "").strip().lower().replace("-", "_")


def _no_match_result(
    *,
    from_query: str,
    to_query: str,
    strategy: str,
    reason: str,
) -> GraphWalkResult:
    return GraphWalkResult(
        from_query=from_query,
        to_query=to_query,
        strategy=strategy,
        confidence="no_match",
        path=(),
        evidence=(reason,),
    )


__all__ = [
    "GraphWalkResult",
    "GraphWalkStep",
    "render_graph_walk_markdown",
    "walk_context_graph",
]
