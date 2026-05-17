"""Connectivity-registry node helpers for the context graph."""

from __future__ import annotations

from pathlib import Path

from ..platform.connectivity_registry import (
    build_connectivity_registry_snapshot,
    summarize_connectivity_registry,
)
from ..platform.connectivity_registry_models import (
    ConnectivityContractRow,
    ConnectivityFieldRow,
    ConnectivityRegistrySnapshot,
)
from .contract_relations import contract_aliases, field_aliases
from .connectivity_registry_metadata import (
    registry_contract_metadata,
    registry_field_metadata,
    registry_snapshot_metadata,
)
from .models import (
    EDGE_KIND_CONTAINS,
    EDGE_KIND_RELATED_TO,
    EDGE_KIND_ROUTES_TO,
    NODE_KIND_CAPABILITY,
    NODE_KIND_DATACLASS_FIELD,
    NODE_KIND_TYPED_CONTRACT,
    GraphEdge,
    GraphNode,
)


def load_connectivity_registry(
    repo_root: Path,
) -> ConnectivityRegistrySnapshot | None:
    try:
        return build_connectivity_registry_snapshot(repo_root=repo_root)
    # broad-except: allow reason=context graph must still build on partial/adopted repos when platform registry inputs are absent fallback=AST-only contract nodes.
    except Exception:
        return None


def registry_fields_by_name(
    row: ConnectivityContractRow | None,
) -> dict[str, ConnectivityFieldRow]:
    if row is None:
        return {}
    return {field.field_name: field for field in row.fields}


def registry_only_contract_nodes(
    *,
    registry: ConnectivityRegistrySnapshot,
    source_node_ids: set[str],
    contract_node_ids_by_name: dict[str, list[str]],
    field_node_ids_by_key: dict[tuple[str, str], str],
) -> tuple[list[GraphNode], list[GraphEdge]]:
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    for row in registry.connected_contracts:
        if row.contract_id in contract_node_ids_by_name:
            continue
        node_id = registry_contract_node_id(row)
        nodes.append(
            GraphNode(
                node_id=node_id,
                node_kind=NODE_KIND_TYPED_CONTRACT,
                label=row.contract_id,
                canonical_pointer_ref=registry_contract_ref(row),
                provenance_ref=registry.contract_id,
                temperature=0.08,
                metadata={
                    "aliases": contract_aliases(row.contract_id),
                    "field_names": [field.field_name for field in row.fields],
                    "field_count": len(row.fields),
                    "runtime_model": row.runtime_model,
                    **registry_contract_metadata(registry, row),
                },
            )
        )
        contract_node_ids_by_name.setdefault(row.contract_id, []).append(node_id)
        source_id = f"src:{row.writer.path}"
        if source_id in source_node_ids:
            edges.append(
                GraphEdge(
                    source_id=node_id,
                    target_id=source_id,
                    edge_kind=EDGE_KIND_ROUTES_TO,
                )
            )
        _append_registry_field_nodes(
            row=row,
            registry=registry,
            field_node_ids_by_key=field_node_ids_by_key,
            nodes=nodes,
            edges=edges,
            contract_node_id=node_id,
        )
    return nodes, edges


def _append_registry_field_nodes(
    *,
    row: ConnectivityContractRow,
    registry: ConnectivityRegistrySnapshot,
    field_node_ids_by_key: dict[tuple[str, str], str],
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    contract_node_id: str,
) -> None:
    for field in row.fields:
        field_node_id = f"field:{row.writer.path}:{row.contract_id}:{field.field_name}"
        field_node_ids_by_key[(row.contract_id, field.field_name)] = field_node_id
        nodes.append(
            GraphNode(
                node_id=field_node_id,
                node_kind=NODE_KIND_DATACLASS_FIELD,
                label=field.field_name,
                canonical_pointer_ref=(
                    f"{row.writer.path}:{row.contract_id}.{field.field_name}"
                ),
                provenance_ref=registry.contract_id,
                temperature=0.03,
                metadata={
                    "aliases": field_aliases(row.contract_id, field.field_name),
                    "contract_id": row.contract_id,
                    "source_path": row.writer.path,
                    **registry_field_metadata(field),
                },
            )
        )
        edges.append(
            GraphEdge(
                source_id=contract_node_id,
                target_id=field_node_id,
                edge_kind=EDGE_KIND_CONTAINS,
            )
        )


def registry_contract_node_id(row: ConnectivityContractRow) -> str:
    path = row.writer.path or f"contract_declaration/{row.contract_id}"
    return f"contract:{path}:{row.contract_id}"


def registry_contract_ref(row: ConnectivityContractRow) -> str:
    if row.writer.path:
        return f"{row.writer.path}:{row.contract_id}"
    return row.contract_id


def registry_reader_nodes_and_edges(
    *,
    registry: ConnectivityRegistrySnapshot,
    capability_nodes: list[GraphNode],
    contract_node_ids_by_name: dict[str, list[str]],
    field_node_ids_by_key: dict[tuple[str, str], str],
) -> tuple[list[GraphNode], list[GraphEdge]]:
    known_capability_ids = {node.node_id for node in capability_nodes}
    reader_ids = registry_reader_ids(registry)
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    for reader_id in reader_ids:
        node_id = f"capability:{reader_id}"
        if node_id in known_capability_ids:
            continue
        nodes.append(
            GraphNode(
                node_id=node_id,
                node_kind=NODE_KIND_CAPABILITY,
                label=reader_id,
                canonical_pointer_ref=f"connectivity_reader:{reader_id}",
                provenance_ref="system_catalog.connectivity_registry",
                temperature=0.04,
                metadata={
                    "capability_kind": "connectivity_registry_reader",
                    "consumes_contracts": [registry.contract_id],
                },
            )
        )
        known_capability_ids.add(node_id)
    edge_keys = registry_reader_edge_keys(
        registry=registry,
        reader_ids=reader_ids,
        contract_node_ids_by_name=contract_node_ids_by_name,
        field_node_ids_by_key=field_node_ids_by_key,
    )
    edges.extend(
        GraphEdge(
            source_id=source_id,
            target_id=target_id,
            edge_kind=EDGE_KIND_RELATED_TO,
        )
        for source_id, target_id in sorted(edge_keys)
    )
    return nodes, edges


def registry_reader_edge_keys(
    *,
    registry: ConnectivityRegistrySnapshot,
    reader_ids: tuple[str, ...],
    contract_node_ids_by_name: dict[str, list[str]],
    field_node_ids_by_key: dict[tuple[str, str], str],
) -> set[tuple[str, str]]:
    edge_keys: set[tuple[str, str]] = set()
    registry_contract_nodes = contract_node_ids_by_name.get(registry.contract_id, ())
    for registry_node_id in registry_contract_nodes:
        for reader_id in reader_ids:
            edge_keys.add((registry_node_id, f"capability:{reader_id}"))
    for row in registry.connected_contracts:
        for contract_node_id in contract_node_ids_by_name.get(row.contract_id, ()):
            for reader_id in row.reader_ids:
                edge_keys.add((contract_node_id, f"capability:{reader_id}"))
        for field in row.fields:
            field_node_id = field_node_ids_by_key.get((row.contract_id, field.field_name))
            if field_node_id is None:
                continue
            for reader_id in field.reader_ids:
                edge_keys.add((field_node_id, f"capability:{reader_id}"))
    return edge_keys


def registry_reader_ids(registry: ConnectivityRegistrySnapshot) -> tuple[str, ...]:
    summary = summarize_connectivity_registry(registry)
    return summary.reader_ids
