"""Typed-contract discoverability nodes for context-graph queries."""

from __future__ import annotations

from pathlib import Path

from .contract_relations import (
    capability_contract_edges,
    contract_aliases,
    field_aliases,
)
from .contract_scan import (
    discoverable_contract_names,
    field_names,
    iter_dataclass_defs,
    should_index_contract,
)
from .models import (
    EDGE_KIND_CONTAINS,
    EDGE_KIND_ROUTES_TO,
    NODE_KIND_DATACLASS_FIELD,
    NODE_KIND_TYPED_CONTRACT,
    GraphEdge,
    GraphNode,
)


def collect_contract_nodes(
    repo_root: Path,
    *,
    source_node_ids: set[str],
    capability_nodes: list[GraphNode],
) -> tuple[list[GraphNode], list[GraphEdge]]:
    """Collect typed contract and dataclass-field nodes from repo-owned code."""
    contract_names = discoverable_contract_names()
    contract_nodes: list[GraphNode] = []
    field_nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    contract_node_ids_by_name: dict[str, list[str]] = {}

    for rel_path, class_def in iter_dataclass_defs(repo_root):
        class_name = class_def.name
        if not should_index_contract(class_name, contract_names):
            continue

        node_id = f"contract:{rel_path}:{class_name}"
        runtime_model = f"{rel_path[:-3].replace('/', '.')}:{class_name}"
        contract_fields = field_names(class_def)
        contract_node = GraphNode(
            node_id=node_id,
            node_kind=NODE_KIND_TYPED_CONTRACT,
            label=class_name,
            canonical_pointer_ref=f"{rel_path}:{class_name}",
            provenance_ref="dataclass_ast",
            temperature=0.08,
            metadata={
                "aliases": contract_aliases(class_name),
                "field_names": contract_fields,
                "field_count": len(contract_fields),
                "runtime_model": runtime_model,
                "source_path": rel_path,
            },
        )
        contract_nodes.append(contract_node)
        contract_node_ids_by_name.setdefault(class_name, []).append(node_id)

        source_node_id = f"src:{rel_path}"
        if source_node_id in source_node_ids:
            edges.append(
                GraphEdge(
                    source_id=node_id,
                    target_id=source_node_id,
                    edge_kind=EDGE_KIND_ROUTES_TO,
                )
            )

        for field_name in contract_fields:
            field_node_id = f"field:{rel_path}:{class_name}:{field_name}"
            field_nodes.append(
                GraphNode(
                    node_id=field_node_id,
                    node_kind=NODE_KIND_DATACLASS_FIELD,
                    label=field_name,
                    canonical_pointer_ref=f"{rel_path}:{class_name}.{field_name}",
                    provenance_ref="dataclass_ast",
                    temperature=0.03,
                    metadata={
                        "aliases": field_aliases(class_name, field_name),
                        "contract_id": class_name,
                        "source_path": rel_path,
                    },
                )
            )
            edges.append(
                GraphEdge(
                    source_id=node_id,
                    target_id=field_node_id,
                    edge_kind=EDGE_KIND_CONTAINS,
                )
            )

    edges.extend(
        capability_contract_edges(
            capability_nodes=capability_nodes,
            contract_node_ids_by_name=contract_node_ids_by_name,
        )
    )
    return contract_nodes + field_nodes, edges
