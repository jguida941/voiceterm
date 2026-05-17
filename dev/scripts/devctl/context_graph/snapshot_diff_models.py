"""Typed delta/trend models for saved context-graph snapshots."""

from __future__ import annotations

from dataclasses import dataclass

CONTEXT_GRAPH_DELTA_SCHEMA_VERSION = 1
CONTEXT_GRAPH_DELTA_CONTRACT_ID = "ContextGraphDelta"


@dataclass(frozen=True, slots=True)
class SnapshotAnchor:
    """Stable identity/summary for one saved graph snapshot."""

    path: str
    commit_hash: str
    branch: str
    generated_at_utc: str
    node_count: int
    edge_count: int
    average_temperature: float
    import_cycle_count: int
    largest_import_cycle_size: int


@dataclass(frozen=True, slots=True)
class NodeChangeSummary:
    """Compact changed-node sample for markdown and JSON payloads."""

    node_id: str
    label: str
    canonical_pointer_ref: str
    changed_fields: list[str]


@dataclass(frozen=True, slots=True)
class EdgeSummary:
    """Compact edge sample."""

    source_id: str
    target_id: str
    edge_kind: str


@dataclass(frozen=True, slots=True)
class NodeSummary:
    """Compact node sample."""

    node_id: str
    node_kind: str
    label: str
    canonical_pointer_ref: str
    temperature: float


@dataclass(frozen=True, slots=True)
class TemperatureShiftSummary:
    """Largest node-temperature shifts between two snapshots."""

    node_id: str
    label: str
    canonical_pointer_ref: str
    before: float
    after: float
    delta: float


@dataclass(frozen=True, slots=True)
class SnapshotTrendPoint:
    """Trend point for one saved snapshot in the rolling window."""

    path: str
    commit_hash: str
    generated_at_utc: str
    average_temperature: float
    node_count: int
    edge_count: int
    import_cycle_count: int


@dataclass(frozen=True, slots=True)
class SnapshotTrendSummary:
    """Rolling trend summary over recent graph snapshots."""

    window_size: int
    temperature_direction: str
    average_temperature_delta: float
    node_count_delta: int
    edge_count_delta: int
    import_cycle_delta: int
    hot_bucket_delta: int
    points: list[SnapshotTrendPoint]


@dataclass(frozen=True, slots=True)
class ContextGraphDelta:
    """Typed delta payload between two saved graph snapshots."""

    schema_version: int
    contract_id: str
    from_snapshot: SnapshotAnchor
    to_snapshot: SnapshotAnchor
    added_nodes_count: int
    removed_nodes_count: int
    changed_nodes_count: int
    added_edges_count: int
    removed_edges_count: int
    new_edge_kinds: list[str]
    dropped_edge_kinds: list[str]
    added_nodes_sample: list[NodeSummary]
    removed_nodes_sample: list[NodeSummary]
    changed_nodes_sample: list[NodeChangeSummary]
    added_edges_sample: list[EdgeSummary]
    removed_edges_sample: list[EdgeSummary]
    hottest_increases: list[TemperatureShiftSummary]
    hottest_decreases: list[TemperatureShiftSummary]
    trend: SnapshotTrendSummary | None
