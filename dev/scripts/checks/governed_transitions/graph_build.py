"""Synthetic context-graph construction for governed transition metadata."""

from __future__ import annotations

from collections.abc import Sequence

from dev.scripts.devctl.context_graph.models import (
    EDGE_KIND_PRODUCES_STATE,
    EDGE_KIND_RECEIPT_PROVES,
    EDGE_KIND_REQUIRES_STATE,
    EDGE_KIND_TRANSITIONS_TO,
    NODE_KIND_CONCEPT,
    GraphEdge,
    GraphNode,
)
from dev.scripts.devctl.runtime.governed_transitions import TransitionContract

from .ids import (
    emit_node_id,
    graph_path_node_id,
    state_node_id,
    transition_node_id,
)


def build_transition_graph(
    transitions: Sequence[TransitionContract],
) -> tuple[list[GraphNode], list[GraphEdge]]:
    nodes: dict[str, GraphNode] = {}
    edges: list[GraphEdge] = []
    for transition in transitions:
        if not transition.transition_id:
            continue
        _add_transition_edges(transition, nodes=nodes, edges=edges)
    return list(nodes.values()), edges


def _add_transition_edges(
    transition: TransitionContract,
    *,
    nodes: dict[str, GraphNode],
    edges: list[GraphEdge],
) -> None:
    node_id = transition_node_id(transition.transition_id)
    _add_node(
        nodes,
        node_id,
        label=transition.transition_id,
        metadata={
            "contract_id": transition.contract_id,
            "owner_module": transition.owner_module,
            "function_name": transition.function_name,
        },
    )
    _add_required_state_edges(transition, node_id, nodes=nodes, edges=edges)
    _add_produced_state_edges(transition, node_id, nodes=nodes, edges=edges)
    _add_emitted_evidence_edges(transition, node_id, nodes=nodes, edges=edges)
    _add_declared_graph_path_edges(transition, nodes=nodes, edges=edges)


def _add_required_state_edges(
    transition: TransitionContract,
    transition_id: str,
    *,
    nodes: dict[str, GraphNode],
    edges: list[GraphEdge],
) -> None:
    for required in transition.requires:
        node_id = state_node_id(transition.transition_id, "requires", required)
        _add_node(nodes, node_id, label=required)
        edges.append(
            GraphEdge(
                source_id=node_id,
                target_id=transition_id,
                edge_kind=EDGE_KIND_REQUIRES_STATE,
                metadata={"transition_id": transition.transition_id},
            )
        )


def _add_produced_state_edges(
    transition: TransitionContract,
    transition_id: str,
    *,
    nodes: dict[str, GraphNode],
    edges: list[GraphEdge],
) -> None:
    for produced in transition.produces:
        node_id = state_node_id(transition.transition_id, "produces", produced)
        _add_node(nodes, node_id, label=produced)
        edges.append(
            GraphEdge(
                source_id=transition_id,
                target_id=node_id,
                edge_kind=EDGE_KIND_PRODUCES_STATE,
                metadata={"transition_id": transition.transition_id},
            )
        )


def _add_emitted_evidence_edges(
    transition: TransitionContract,
    transition_id: str,
    *,
    nodes: dict[str, GraphNode],
    edges: list[GraphEdge],
) -> None:
    for emitted in transition.emits:
        node_id = emit_node_id(transition.transition_id, emitted)
        _add_node(nodes, node_id, label=emitted)
        edges.append(
            GraphEdge(
                source_id=transition_id,
                target_id=node_id,
                edge_kind=EDGE_KIND_RECEIPT_PROVES,
                metadata={"transition_id": transition.transition_id},
            )
        )


def _add_declared_graph_path_edges(
    transition: TransitionContract,
    *,
    nodes: dict[str, GraphNode],
    edges: list[GraphEdge],
) -> None:
    for index, label in enumerate(transition.graph_path):
        current_id = graph_path_node_id(transition.transition_id, index, label)
        _add_node(nodes, current_id, label=label)
        if index == 0:
            continue
        previous_id = graph_path_node_id(
            transition.transition_id,
            index - 1,
            transition.graph_path[index - 1],
        )
        edges.append(
            GraphEdge(
                source_id=previous_id,
                target_id=current_id,
                edge_kind=EDGE_KIND_TRANSITIONS_TO,
                metadata={
                    "transition_id": transition.transition_id,
                    "path_index": index,
                },
            )
        )


def _add_node(
    nodes: dict[str, GraphNode],
    node_id: str,
    *,
    label: str,
    metadata: dict[str, object] | None = None,
) -> None:
    nodes.setdefault(
        node_id,
        GraphNode(
            node_id=node_id,
            node_kind=NODE_KIND_CONCEPT,
            label=label,
            canonical_pointer_ref=node_id,
            provenance_ref="governed_transition_metadata",
            temperature=0.65,
            metadata=metadata or {},
        ),
    )
