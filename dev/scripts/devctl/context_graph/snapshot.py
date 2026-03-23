"""Deterministic snapshot persistence for the context-graph surface."""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from ..config import get_repo_root
from .models import GraphEdge, GraphNode

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


def write_context_graph_snapshot(
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    *,
    capture: ContextGraphSnapshotCapture,
) -> ContextGraphSnapshotReceipt:
    """Write one deterministic graph snapshot and return a compact receipt."""
    effective_repo_root = (capture.repo_root or get_repo_root()).resolve()
    effective_branch = capture.branch or _git_value(
        effective_repo_root,
        ["git", "branch", "--show-current"],
    )
    effective_commit_hash = capture.commit_hash or _git_value(
        effective_repo_root,
        ["git", "rev-parse", "HEAD"],
    )
    now = datetime.now(timezone.utc)
    generated_at = capture.generated_at_utc or now.strftime("%Y-%m-%dT%H:%M:%SZ")
    file_timestamp = capture.timestamp_slug or now.strftime("%Y%m%dT%H%M%SZ")
    snapshot_path = effective_repo_root / _SNAPSHOT_DIR / f"{effective_commit_hash}_{file_timestamp}.json"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)

    temperature_distribution = _temperature_distribution(nodes)
    payload = ContextGraphSnapshot(
        schema_version=CONTEXT_GRAPH_SNAPSHOT_SCHEMA_VERSION,
        contract_id=CONTEXT_GRAPH_SNAPSHOT_CONTRACT_ID,
        repo=effective_repo_root.name,
        branch=effective_branch,
        commit_hash=effective_commit_hash,
        generated_at_utc=generated_at,
        source_mode=capture.source_mode,
        node_count=len(nodes),
        edge_count=len(edges),
        nodes_by_kind=dict(sorted(Counter(node.node_kind for node in nodes).items())),
        edges_by_kind=dict(sorted(Counter(edge.edge_kind for edge in edges).items())),
        temperature_distribution=temperature_distribution,
        nodes=[asdict(node) for node in nodes],
        edges=[asdict(edge) for edge in edges],
    )

    snapshot_path.write_text(
        json.dumps(asdict(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return ContextGraphSnapshotReceipt(
        path=_snapshot_artifact_path(snapshot_path, effective_repo_root),
        schema_version=payload.schema_version,
        contract_id=payload.contract_id,
        branch=payload.branch,
        commit_hash=payload.commit_hash,
        generated_at_utc=payload.generated_at_utc,
        source_mode=payload.source_mode,
        node_count=payload.node_count,
        edge_count=payload.edge_count,
        temperature_distribution=asdict(payload.temperature_distribution),
    )


def load_context_graph_snapshot(path: str | Path) -> ContextGraphSnapshot:
    """Load a saved snapshot back into the typed snapshot contract."""
    snapshot_path = Path(path)
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if payload.get("contract_id") != CONTEXT_GRAPH_SNAPSHOT_CONTRACT_ID:
        raise SnapshotResolutionError(
            f"expected {CONTEXT_GRAPH_SNAPSHOT_CONTRACT_ID}, found {payload.get('contract_id')!r}"
        )
    if payload.get("schema_version") != CONTEXT_GRAPH_SNAPSHOT_SCHEMA_VERSION:
        raise SnapshotResolutionError(
            "unexpected ContextGraphSnapshot schema_version "
            f"{payload.get('schema_version')!r}"
        )
    return ContextGraphSnapshot(
        schema_version=CONTEXT_GRAPH_SNAPSHOT_SCHEMA_VERSION,
        contract_id=CONTEXT_GRAPH_SNAPSHOT_CONTRACT_ID,
        repo=str(payload.get("repo") or ""),
        branch=str(payload.get("branch") or "unknown"),
        commit_hash=str(payload.get("commit_hash") or "unknown"),
        generated_at_utc=str(payload.get("generated_at_utc") or ""),
        source_mode=str(payload.get("source_mode") or "unknown"),
        node_count=int(payload.get("node_count") or 0),
        edge_count=int(payload.get("edge_count") or 0),
        nodes_by_kind=_coerce_int_map(payload.get("nodes_by_kind")),
        edges_by_kind=_coerce_int_map(payload.get("edges_by_kind")),
        temperature_distribution=_load_temperature_distribution(
            payload.get("temperature_distribution")
        ),
        nodes=_coerce_object_list(payload.get("nodes")),
        edges=_coerce_object_list(payload.get("edges")),
    )


def resolve_context_graph_snapshot_ref(
    ref: str | None,
    *,
    repo_root: Path | None = None,
    exclude: Path | None = None,
) -> Path:
    """Resolve a snapshot ref/path against the canonical graph-snapshot store."""
    effective_repo_root = (repo_root or get_repo_root()).resolve()
    excluded = exclude.resolve() if exclude is not None else None
    available = list_context_graph_snapshots(repo_root=effective_repo_root)
    if excluded is not None:
        available = [path for path in available if path.resolve() != excluded]
    if not available:
        raise SnapshotResolutionError("no ContextGraphSnapshot artifacts available")
    token = (ref or "").strip()
    if not token:
        return available[-1]
    if token == "latest":
        return available[-1]
    if token == "previous":
        if len(available) < 2:
            raise SnapshotResolutionError("previous snapshot requested but only one snapshot exists")
        return available[-2]
    direct = Path(token).expanduser()
    if direct.exists():
        resolved = direct.resolve()
        _validate_snapshot_resolution_exclusion(resolved, excluded)
        return resolved
    candidate = effective_repo_root / token
    if candidate.exists():
        resolved = candidate.resolve()
        _validate_snapshot_resolution_exclusion(resolved, excluded)
        return resolved
    for path in available:
        if token in {path.name, path.stem}:
            return path
    matches = [path for path in available if path.name.startswith(token)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise SnapshotResolutionError(f"snapshot ref {token!r} is ambiguous")
    raise SnapshotResolutionError(f"snapshot ref {token!r} not found")


def _validate_snapshot_resolution_exclusion(path: Path, excluded: Path | None) -> None:
    if excluded is not None and path == excluded:
        raise SnapshotResolutionError("snapshot diff requires distinct --from and --to refs")


def list_context_graph_snapshots(*, repo_root: Path | None = None) -> list[Path]:
    """Return saved snapshot paths sorted by capture time."""
    effective_repo_root = (repo_root or get_repo_root()).resolve()
    snapshot_dir = effective_repo_root / _SNAPSHOT_DIR
    if not snapshot_dir.exists():
        return []
    return sorted(
        snapshot_dir.glob("*.json"),
        key=lambda path: (path.stat().st_mtime_ns, path.name),
    )


def _temperature_distribution(nodes: list[GraphNode]) -> TemperatureDistributionSummary:
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


def _coerce_int_map(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, raw in value.items():
        if raw is None:
            continue
        result[str(key)] = int(raw)
    return result


def _coerce_object_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, object]] = []
    for item in value:
        if isinstance(item, dict):
            result.append(dict(item))
    return result


def _load_temperature_distribution(value: object) -> TemperatureDistributionSummary:
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


def _snapshot_artifact_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


def _git_value(repo_root: Path, argv: list[str]) -> str:
    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            cwd=repo_root,
            timeout=5,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return "unknown"
    value = result.stdout.strip()
    return value or "unknown"
