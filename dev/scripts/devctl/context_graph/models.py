"""Frozen data models for the context graph query surface."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GraphNode:
    """A single node in the context graph."""

    node_id: str
    node_kind: str
    label: str
    canonical_pointer_ref: str
    provenance_ref: str
    temperature: float
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphEdge:
    """A typed directed edge between two nodes."""

    source_id: str
    target_id: str
    edge_kind: str


@dataclass(frozen=True)
class QueryResult:
    """Result of a context-graph query with stable evidence fields."""

    query: str
    matched_nodes: list[GraphNode]
    edges: list[GraphEdge]
    hot_index_summary: HotIndexSummary
    evidence: list[str]
    confidence: str = "high"


NODE_KIND_SOURCE = "source_file"
NODE_KIND_PLAN = "active_plan"
NODE_KIND_COMMAND = "devctl_command"
NODE_KIND_GUARD = "guard"
NODE_KIND_PROBE = "probe"
NODE_KIND_GUIDE = "guide"
NODE_KIND_CONCEPT = "concept"

@dataclass(frozen=True)
class GraphSize:
    """Graph dimension counts for bootstrap packets."""

    source_files: int
    guards: int
    probes: int
    active_plans: int
    edges: int


@dataclass(frozen=True)
class BootstrapContext:
    """Slim AI startup context packet."""

    repo: str
    branch: str
    bridge_active: bool
    graph_size: GraphSize
    active_plans: list[dict[str, object]]
    hotspots: list[dict[str, object]]
    key_commands: dict[str, str]
    bootstrap_links: dict[str, str | None]
    push_enforcement: dict[str, object]
    usage: str


@dataclass(frozen=True)
class HotIndexSummary:
    """Compact graph dimension summary included in every query result."""

    total_nodes: int
    total_edges: int
    nodes_by_kind: dict[str, int]
    edges_by_kind: dict[str, int]


EDGE_KIND_IMPORTS = "imports"
EDGE_KIND_DOCUMENTED_BY = "documented_by"
EDGE_KIND_GUARDS = "guards"
EDGE_KIND_ROUTES_TO = "routes_to"
EDGE_KIND_SCOPED_BY = "scoped_by"
EDGE_KIND_CONTAINS = "contains"
EDGE_KIND_RELATED_TO = "related_to"
