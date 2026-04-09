"""Graph materialization helpers for bounded codeshape ingestion."""

from __future__ import annotations

from ._codeshape_models import (
    CodeShapeGraph,
    FunctionInfo,
    ModuleIndex,
    MutationCandidate,
)
from .models import (
    EDGE_KIND_CALLS,
    EDGE_KIND_CONTAINS,
    NODE_KIND_FUNCTION,
    NODE_KIND_MUTATION_CALLSITE,
    GraphEdge,
    GraphNode,
)


def assemble_codeshape_graph(
    module_indexes: list[ModuleIndex],
    *,
    parse_errors: list[dict[str, str]],
) -> CodeShapeGraph:
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    seen_edge_keys: set[tuple[str, str, str]] = set()
    function_by_pointer = {
        function.canonical_pointer_ref: function
        for module in module_indexes
        for function in module.functions
    }

    for module in module_indexes:
        materialize_function_nodes(module, nodes, edges, seen_edge_keys)
        materialize_call_edges(module, function_by_pointer, edges, seen_edge_keys)
        materialize_mutation_nodes(module, nodes, edges, seen_edge_keys)

    return CodeShapeGraph(
        nodes=tuple(nodes),
        edges=tuple(edges),
        parse_errors=tuple(parse_errors),
    )


def materialize_function_nodes(
    module: ModuleIndex,
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    seen_edge_keys: set[tuple[str, str, str]],
) -> None:
    for function in module.functions:
        nodes.append(
            GraphNode(
                node_id=function.node_id,
                node_kind=NODE_KIND_FUNCTION,
                label=function.qualname,
                canonical_pointer_ref=function.canonical_pointer_ref,
                provenance_ref="context_graph.codeshape",
                temperature=0.2,
                metadata={
                    "path": function.rel_path,
                    "qualname": function.qualname,
                    "line": function.line,
                    "class_name": function.class_name or "",
                    "name": function.local_name,
                },
            )
        )
        edge_key = (f"src:{function.rel_path}", function.node_id, EDGE_KIND_CONTAINS)
        if edge_key not in seen_edge_keys:
            seen_edge_keys.add(edge_key)
            edges.append(GraphEdge(source_id=edge_key[0], target_id=edge_key[1], edge_kind=edge_key[2]))


def materialize_call_edges(
    module: ModuleIndex,
    function_by_pointer: dict[str, FunctionInfo],
    edges: list[GraphEdge],
    seen_edge_keys: set[tuple[str, str, str]],
) -> None:
    for record in module.call_records:
        target_function = function_by_pointer.get(record.target_pointer_ref)
        if target_function is None:
            continue
        edge_key = (record.caller_id, target_function.node_id, EDGE_KIND_CALLS)
        if edge_key not in seen_edge_keys:
            seen_edge_keys.add(edge_key)
            edges.append(
                GraphEdge(
                    source_id=record.caller_id,
                    target_id=target_function.node_id,
                    edge_kind=EDGE_KIND_CALLS,
                )
            )


def materialize_mutation_nodes(
    module: ModuleIndex,
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    seen_edge_keys: set[tuple[str, str, str]],
) -> None:
    for candidate in module.mutation_candidates:
        nodes.append(
            GraphNode(
                node_id=candidate.node_id,
                node_kind=NODE_KIND_MUTATION_CALLSITE,
                label=f"{candidate.git_verb} @ {candidate.qualname}:{candidate.line}",
                canonical_pointer_ref=candidate.canonical_pointer_ref,
                provenance_ref="context_graph.codeshape",
                temperature=0.25,
                metadata=_mutation_metadata(candidate),
            )
        )
        edge_key = (candidate.caller_id, candidate.node_id, EDGE_KIND_CONTAINS)
        if edge_key not in seen_edge_keys:
            seen_edge_keys.add(edge_key)
            edges.append(
                GraphEdge(
                    source_id=candidate.caller_id,
                    target_id=candidate.node_id,
                    edge_kind=EDGE_KIND_CONTAINS,
                )
            )


def _mutation_metadata(candidate: MutationCandidate) -> dict[str, object]:
    metadata: dict[str, object] = {
        "path": candidate.rel_path,
        "qualname": candidate.qualname,
        "line": candidate.line,
        "column": candidate.column,
    }
    metadata["git_verb"] = candidate.git_verb
    metadata["command_source"] = candidate.command_source
    metadata["command_literal"] = candidate.command_literal
    return metadata
