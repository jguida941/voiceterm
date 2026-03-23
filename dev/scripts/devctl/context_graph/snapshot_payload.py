"""Shared contracts and payload helpers for context-graph snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import GraphNode

CONTEXT_GRAPH_SNAPSHOT_SCHEMA_VERSION = 1
CONTEXT_GRAPH_SNAPSHOT_CONTRACT_ID = "ContextGraphSnapshot"
_SNAPSHOT_DIR = Path("dev/reports/graph_snapshots")


@dataclass(frozen=True, slots=True)
class TemperatureDistributionSummary:
    """Compact temperature-distribution summary for a graph snapshot."""

    minimum: float
    maximum: float
    average: float
    buckets: dict[str, int]


@dataclass(frozen=True, slots=True)
class ContextGraphSnapshot:
    """Full serialized graph snapshot plus lightweight capture metadata."""

    schema_version: int
    contract_id: str
    repo: str
    branch: str
    commit_hash: str
    generated_at_utc: str
    source_mode: str
    node_count: int
    edge_count: int
    nodes_by_kind: dict[str, int]
    edges_by_kind: dict[str, int]
    temperature_distribution: TemperatureDistributionSummary
    nodes: list[dict[str, object]]
    edges: list[dict[str, object]]


@dataclass(frozen=True, slots=True)
class ContextGraphSnapshotReceipt:
    """Small receipt surfaced back through devctl command outputs."""

    path: str
    schema_version: int
    contract_id: str
    branch: str
    commit_hash: str
    generated_at_utc: str
    source_mode: str
    node_count: int
    edge_count: int
    temperature_distribution: dict[str, object]


@dataclass(frozen=True, slots=True)
class ContextGraphSnapshotCapture:
    """Capture controls for deterministic snapshot emission."""

    source_mode: str
    repo_root: Path | None = None
    branch: str | None = None
    commit_hash: str | None = None
    generated_at_utc: str | None = None
    timestamp_slug: str | None = None


class SnapshotResolutionError(ValueError):
    """Raised when a requested snapshot ref cannot be resolved safely."""


def coerce_int_map(value: object) -> dict[str, int]:
    """Normalize a mapping-like payload into a string-to-int dictionary."""
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, raw in value.items():
        if raw is None:
            continue
        result[str(key)] = int(raw)
    return result


def coerce_object_list(value: object) -> list[dict[str, object]]:
    """Normalize a payload list into dictionaries only."""
    if not isinstance(value, list):
        return []
    result: list[dict[str, object]] = []
    for item in value:
        if isinstance(item, dict):
            result.append(dict(item))
    return result


def load_temperature_distribution(value: object) -> TemperatureDistributionSummary:
    """Load one serialized temperature-distribution payload."""
    if not isinstance(value, dict):
        return TemperatureDistributionSummary(
            minimum=0.0,
            maximum=0.0,
            average=0.0,
            buckets=_empty_temperature_buckets(),
        )
    buckets = _empty_temperature_buckets()
    raw_buckets = value.get("buckets")
    if isinstance(raw_buckets, dict):
        for key, raw in raw_buckets.items():
            if key in buckets and raw is not None:
                buckets[key] = int(raw)
    return TemperatureDistributionSummary(
        minimum=float(value.get("minimum") or 0.0),
        maximum=float(value.get("maximum") or 0.0),
        average=float(value.get("average") or 0.0),
        buckets=buckets,
    )


def temperature_distribution(nodes: list[GraphNode]) -> TemperatureDistributionSummary:
    """Compute one compact temperature-distribution summary for a snapshot."""
    temperatures = [node.temperature for node in nodes]
    if not temperatures:
        return TemperatureDistributionSummary(
            minimum=0.0,
            maximum=0.0,
            average=0.0,
            buckets=_empty_temperature_buckets(),
        )
    buckets = _empty_temperature_buckets()
    for temperature in temperatures:
        buckets[_temperature_bucket_label(temperature)] += 1
    return TemperatureDistributionSummary(
        minimum=min(temperatures),
        maximum=max(temperatures),
        average=sum(temperatures) / len(temperatures),
        buckets=buckets,
    )


def _empty_temperature_buckets() -> dict[str, int]:
    return {
        "0.00-0.24": 0,
        "0.25-0.49": 0,
        "0.50-0.74": 0,
        "0.75-1.00": 0,
    }


def _temperature_bucket_label(temperature: float) -> str:
    if temperature < 0.25:
        return "0.00-0.24"
    if temperature < 0.5:
        return "0.25-0.49"
    if temperature < 0.75:
        return "0.50-0.74"
    return "0.75-1.00"
