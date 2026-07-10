"""Frozen data models for the context graph query surface."""

from __future__ import annotations

from dataclasses import dataclass, field


def _object_metadata() -> dict[str, object]:
    return {}


def _object_list() -> list[dict[str, object]]:
    return []


@dataclass(frozen=True)
class GraphNode:
    """A single node in the context graph."""

    node_id: str
    node_kind: str
    label: str
    canonical_pointer_ref: str
    provenance_ref: str
    temperature: float
    metadata: dict[str, object] = field(default_factory=_object_metadata)


@dataclass(frozen=True)
class GraphEdge:
    """A typed directed edge between two nodes."""

    source_id: str
    target_id: str
    edge_kind: str
    metadata: dict[str, object] = field(default_factory=_object_metadata)


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
NODE_KIND_INTENT = "intent"
NODE_KIND_CAPABILITY = "capability"
NODE_KIND_FUNCTION = "python_function"
NODE_KIND_MUTATION_CALLSITE = "mutation_callsite"
NODE_KIND_TYPED_CONTRACT = "typed_contract"
NODE_KIND_DATACLASS_FIELD = "dataclass_field"
NODE_KIND_PACKET = "packet"
NODE_KIND_HANDOFF = "handoff"
NODE_KIND_FINDING = "finding"
NODE_KIND_PLAN_ROW = "plan_row"
NODE_KIND_RECEIPT = "receipt"
NODE_KIND_TEST = "test"
NODE_KIND_WORKFLOW = "workflow"
NODE_KIND_CONFIG = "config"
NODE_KIND_AGENT = "agent"

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
    bootstrap_commands: list[dict[str, object]] = field(default_factory=_object_list)
    quality_signals: dict[str, object] = field(default_factory=_object_metadata)
    key_surfaces: tuple[str, ...] = ()
    runtime_spine_closure: dict[str, object] = field(default_factory=_object_metadata)
    packet_continuity_index: dict[str, object] = field(default_factory=_object_metadata)
    packet_carry_forward_debt: tuple[dict[str, object], ...] = ()
    continuity_attention: dict[str, object] = field(default_factory=_object_metadata)


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
EDGE_KIND_CALLS = "calls"
EDGE_KIND_PACKET_HANDOFF = "packet_handoff"
EDGE_KIND_COMMAND_INVOKES = "command_invokes"
EDGE_KIND_GUARD_CATCHES = "guard_catches"
EDGE_KIND_PROBE_FINDS = "probe_finds"
EDGE_KIND_FINDING_BLOCKS = "finding_blocks"
EDGE_KIND_TEST_COVERS = "test_covers"
EDGE_KIND_WORKFLOW_RUNS = "workflow_runs"
EDGE_KIND_CONTRACT_READS = "contract_reads"
EDGE_KIND_CONTRACT_WRITES = "contract_writes"
EDGE_KIND_POLICY_SCOPES = "policy_scopes"
EDGE_KIND_RECEIPT_PROVES = "receipt_proves"
EDGE_KIND_TRANSITIONS_TO = "transitions_to"
EDGE_KIND_REQUIRES_STATE = "requires_state"
EDGE_KIND_PRODUCES_STATE = "produces_state"
