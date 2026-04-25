"""Typed-contract discoverability nodes for context-graph queries."""

from __future__ import annotations

from pathlib import Path

from .contract_relations import (
    capability_contract_edges,
    contract_aliases,
    field_aliases,
)
from .connectivity_registry_nodes import (
    load_connectivity_registry,
    registry_contract_metadata,
    registry_field_metadata,
    registry_fields_by_name,
    registry_only_contract_nodes,
    registry_reader_nodes_and_edges,
    registry_snapshot_metadata,
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
from ..platform.connectivity_registry_models import ConnectivityRegistrySnapshot


def collect_contract_nodes(
    repo_root: Path,
    *,
    source_node_ids: set[str],
    capability_nodes: list[GraphNode],
    connectivity_registry: ConnectivityRegistrySnapshot | None = None,
) -> tuple[list[GraphNode], list[GraphEdge]]:
    """Collect typed contract and dataclass-field nodes from repo-owned code."""
    contract_names = discoverable_contract_names()
    registry = connectivity_registry or load_connectivity_registry(repo_root)
    registry_rows = {
        row.contract_id: row
        for row in (registry.connected_contracts if registry is not None else ())
    }
    contract_nodes: list[GraphNode] = []
    field_nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    contract_node_ids_by_name: dict[str, list[str]] = {}
    field_node_ids_by_key: dict[tuple[str, str], str] = {}

    for rel_path, class_def in iter_dataclass_defs(repo_root):
        class_name = class_def.name
        if not should_index_contract(class_name, contract_names):
            continue

        node_id = f"contract:{rel_path}:{class_name}"
        runtime_model = f"{rel_path[:-3].replace('/', '.')}:{class_name}"
        contract_fields = field_names(class_def)
        registry_row = registry_rows.get(class_name)
        metadata = {
            "aliases": contract_aliases(class_name),
            "field_names": contract_fields,
            "field_count": len(contract_fields),
            "runtime_model": runtime_model,
            "source_path": rel_path,
        }
        if registry_row is not None and registry is not None:
            metadata.update(registry_contract_metadata(registry, registry_row))
        elif class_name == getattr(registry, "contract_id", ""):
            metadata.update(registry_snapshot_metadata(registry))
        contract_node = GraphNode(
            node_id=node_id,
            node_kind=NODE_KIND_TYPED_CONTRACT,
            label=class_name,
            canonical_pointer_ref=f"{rel_path}:{class_name}",
            provenance_ref="dataclass_ast",
            temperature=0.08,
            metadata=metadata,
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

        registry_fields = registry_fields_by_name(registry_row)
        for field_name in contract_fields:
            field_node_id = f"field:{rel_path}:{class_name}:{field_name}"
            field_metadata = {
                "aliases": field_aliases(class_name, field_name),
                "contract_id": class_name,
                "source_path": rel_path,
            }
            registry_field = registry_fields.get(field_name)
            if registry_field is not None:
                field_metadata.update(registry_field_metadata(registry_field))
            field_nodes.append(
                GraphNode(
                    node_id=field_node_id,
                    node_kind=NODE_KIND_DATACLASS_FIELD,
                    label=field_name,
                    canonical_pointer_ref=f"{rel_path}:{class_name}.{field_name}",
                    provenance_ref="dataclass_ast",
                    temperature=0.03,
                    metadata=field_metadata,
                )
            )
            field_node_ids_by_key[(class_name, field_name)] = field_node_id
            edges.append(
                GraphEdge(
                    source_id=node_id,
                    target_id=field_node_id,
                    edge_kind=EDGE_KIND_CONTAINS,
                )
            )

    if registry is not None:
        registry_nodes, registry_edges = registry_only_contract_nodes(
            registry=registry,
            source_node_ids=source_node_ids,
            contract_node_ids_by_name=contract_node_ids_by_name,
            field_node_ids_by_key=field_node_ids_by_key,
        )
        contract_nodes.extend(registry_nodes)
        edges.extend(registry_edges)

    edges.extend(
        capability_contract_edges(
            capability_nodes=capability_nodes,
            contract_node_ids_by_name=contract_node_ids_by_name,
        )
    )
    if registry is not None:
        reader_nodes, reader_edges = registry_reader_nodes_and_edges(
            registry=registry,
            capability_nodes=capability_nodes,
            contract_node_ids_by_name=contract_node_ids_by_name,
            field_node_ids_by_key=field_node_ids_by_key,
        )
        contract_nodes.extend(reader_nodes)
        edges.extend(reader_edges)
    return contract_nodes + field_nodes, edges
