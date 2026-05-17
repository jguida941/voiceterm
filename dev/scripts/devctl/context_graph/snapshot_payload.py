"""Shared contracts and payload helpers for context-graph snapshots."""

from __future__ import annotations

import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .models import GraphNode

CONTEXT_GRAPH_SNAPSHOT_SCHEMA_VERSION = 1
CONTEXT_GRAPH_SNAPSHOT_CONTRACT_ID = "ContextGraphSnapshot"
_SNAPSHOT_DIR = Path("dev/reports/graph_snapshots")
_SNAPSHOT_CACHE_MAX_AGE = timedelta(hours=1)


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

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "ContextGraphSnapshot":
        """Rebuild one typed snapshot from a serialized payload."""
        return cls(
            schema_version=int(
                payload.get("schema_version") or CONTEXT_GRAPH_SNAPSHOT_SCHEMA_VERSION
            ),
            contract_id=str(
                payload.get("contract_id") or CONTEXT_GRAPH_SNAPSHOT_CONTRACT_ID
            ),
            repo=str(payload.get("repo") or ""),
            branch=str(payload.get("branch") or "unknown"),
            commit_hash=str(payload.get("commit_hash") or "unknown"),
            generated_at_utc=str(payload.get("generated_at_utc") or ""),
            source_mode=str(payload.get("source_mode") or "unknown"),
            node_count=int(payload.get("node_count") or 0),
            edge_count=int(payload.get("edge_count") or 0),
            nodes_by_kind=coerce_int_map(payload.get("nodes_by_kind")),
            edges_by_kind=coerce_int_map(payload.get("edges_by_kind")),
            temperature_distribution=load_temperature_distribution(
                payload.get("temperature_distribution")
            ),
            nodes=coerce_object_list(payload.get("nodes")),
            edges=coerce_object_list(payload.get("edges")),
        )


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


# --- Snapshot cache freshness ---


def resolve_head_sha(repo_root: Path) -> str:
    """Return the full HEAD SHA for the repo, or empty string on failure."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def snapshot_cache_is_fresh(snapshot_path: Path, head_sha: str) -> bool:
    """Check whether a cached snapshot file is safe to serve.

    Validates two conditions:
    1. The snapshot was created at the same commit as the current HEAD.
       The filename format is ``<commit_hash>_<timestamp>.json`` so the
       commit hash is extracted without parsing JSON.
    2. The snapshot is not older than ``_SNAPSHOT_CACHE_MAX_AGE``.

    Returns False (force rebuild) when either check fails or when the
    inputs are unusable.
    """
    if not head_sha:
        return False
    stem = snapshot_path.stem
    sep_index = stem.find("_")
    if sep_index < 1:
        return False
    snapshot_head = stem[:sep_index]
    if snapshot_head != head_sha:
        return False
    timestamp_slug = stem[sep_index + 1:]
    try:
        snapshot_time = datetime.strptime(timestamp_slug, "%Y%m%dT%H%M%SZ")
        snapshot_time = snapshot_time.replace(tzinfo=timezone.utc)
    except ValueError:
        return False
    age = datetime.now(timezone.utc) - snapshot_time
    return age <= _SNAPSHOT_CACHE_MAX_AGE
