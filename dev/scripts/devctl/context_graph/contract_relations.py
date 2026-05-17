"""Typed-contract alias and relation helpers for context-graph."""

from __future__ import annotations

import re

from .models import EDGE_KIND_RELATED_TO, NODE_KIND_CAPABILITY, GraphEdge, GraphNode


def contract_aliases(class_name: str) -> list[str]:
    """Return discoverable aliases for one contract label."""
    snake = snake_case(class_name)
    aliases = [snake]
    trimmed = snake
    for suffix in (
        "_authority",
        "_candidate",
        "_catalog",
        "_contract",
        "_decision",
        "_packet",
        "_record",
        "_ref",
        "_snapshot",
        "_state",
    ):
        if trimmed.endswith(suffix):
            trimmed = trimmed[: -len(suffix)]
            break
    if trimmed and trimmed != snake:
        aliases.append(trimmed)
    return aliases


def field_aliases(class_name: str, field_name: str) -> list[str]:
    """Return plain and contract-qualified aliases for one dataclass field."""
    aliases = [field_name]
    for alias in contract_aliases(class_name):
        aliases.append(f"{alias}.{field_name}")
    return aliases


def snake_case(value: str) -> str:
    """Convert a contract label into a query-friendly snake_case alias."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()


def capability_contract_edges(
    *,
    capability_nodes: list[GraphNode],
    contract_node_ids_by_name: dict[str, list[str]],
) -> list[GraphEdge]:
    """Relate capability nodes to the contract nodes they advertise or consume."""
    edge_keys: set[tuple[str, str]] = set()
    for node in capability_nodes:
        if node.node_kind != NODE_KIND_CAPABILITY:
            continue
        for contract_name in capability_contract_names(node):
            for contract_node_id in contract_node_ids_by_name.get(contract_name, ()):
                edge_keys.add((node.node_id, contract_node_id))
    return [
        GraphEdge(
            source_id=source_id,
            target_id=target_id,
            edge_kind=EDGE_KIND_RELATED_TO,
        )
        for source_id, target_id in sorted(edge_keys)
    ]


def capability_contract_names(node: GraphNode) -> tuple[str, ...]:
    """Return the contract IDs mentioned by one capability node."""
    metadata = node.metadata
    collected: list[str] = []
    for raw in (
        metadata.get("consumes_contracts"),
        metadata.get("contract_ids"),
    ):
        if not isinstance(raw, list):
            continue
        for item in raw:
            name = str(item).strip()
            if name and name not in collected:
                collected.append(name)
    return tuple(collected)
