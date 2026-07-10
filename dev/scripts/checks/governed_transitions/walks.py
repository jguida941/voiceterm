"""Context-graph walk checks for governed transition paths."""

from __future__ import annotations

from collections.abc import Sequence

from dev.scripts.devctl.context_graph.graph_walk import (
    GraphWalkStep,
    walk_context_graph,
)
from dev.scripts.devctl.context_graph.models import (
    EDGE_KIND_PRODUCES_STATE,
    EDGE_KIND_REQUIRES_STATE,
    EDGE_KIND_TRANSITIONS_TO,
    GraphEdge,
    GraphNode,
)
from dev.scripts.devctl.runtime.governed_transitions import TransitionContract

from .ids import graph_path_node_id, state_node_id
from .models import GovernedTransitionPathCheck


def state_path_checks(
    transition: TransitionContract,
    *,
    nodes: list[GraphNode],
    edges: list[GraphEdge],
) -> tuple[GovernedTransitionPathCheck, ...]:
    checks: list[GovernedTransitionPathCheck] = []
    for required in transition.requires:
        for produced in transition.produces:
            checks.append(
                _walk_state_path(
                    transition,
                    required=required,
                    produced=produced,
                    nodes=nodes,
                    edges=edges,
                )
            )
    return tuple(checks)


def declared_graph_path_check(
    transition: TransitionContract,
    *,
    nodes: list[GraphNode],
    edges: list[GraphEdge],
) -> GovernedTransitionPathCheck:
    from_id = graph_path_node_id(transition.transition_id, 0, transition.graph_path[0])
    last_index = len(transition.graph_path) - 1
    to_id = graph_path_node_id(
        transition.transition_id,
        last_index,
        transition.graph_path[last_index],
    )
    result = walk_context_graph(from_id, to_id, nodes, edges, max_depth=last_index + 1)
    edge_kinds = _result_edge_kinds(result.path)
    ok = result.confidence != "no_match" and edge_kinds == (
        EDGE_KIND_TRANSITIONS_TO,
    ) * last_index
    return GovernedTransitionPathCheck(
        transition_id=transition.transition_id,
        check_kind="declared_graph_path",
        from_ref=transition.graph_path[0],
        to_ref=transition.graph_path[last_index],
        ok=ok,
        confidence=result.confidence,
        path_length=max(len(result.path) - 1, 0),
        edge_kinds=edge_kinds,
        reason="" if ok else "; ".join(result.evidence),
    )


def _walk_state_path(
    transition: TransitionContract,
    *,
    required: str,
    produced: str,
    nodes: list[GraphNode],
    edges: list[GraphEdge],
) -> GovernedTransitionPathCheck:
    from_id = state_node_id(transition.transition_id, "requires", required)
    to_id = state_node_id(transition.transition_id, "produces", produced)
    result = walk_context_graph(from_id, to_id, nodes, edges, max_depth=4)
    edge_kinds = _result_edge_kinds(result.path)
    ok = (
        result.confidence != "no_match"
        and EDGE_KIND_REQUIRES_STATE in edge_kinds
        and EDGE_KIND_PRODUCES_STATE in edge_kinds
    )
    return GovernedTransitionPathCheck(
        transition_id=transition.transition_id,
        check_kind="state_path",
        from_ref=required,
        to_ref=produced,
        ok=ok,
        confidence=result.confidence,
        path_length=max(len(result.path) - 1, 0),
        edge_kinds=edge_kinds,
        reason="" if ok else "; ".join(result.evidence),
    )


def _result_edge_kinds(path: Sequence[GraphWalkStep]) -> tuple[str, ...]:
    return tuple(step.inbound_edge_kind for step in path if step.inbound_edge_kind)
