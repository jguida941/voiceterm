"""Deterministic snapshot persistence for the context-graph surface."""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from ..config import get_repo_root
from .models import GraphEdge, GraphNode
from .snapshot_payload import (
    CONTEXT_GRAPH_SNAPSHOT_CONTRACT_ID,
    CONTEXT_GRAPH_SNAPSHOT_SCHEMA_VERSION,
    ContextGraphSnapshot,
    ContextGraphSnapshotCapture,
    ContextGraphSnapshotReceipt,
    SnapshotResolutionError,
    TemperatureDistributionSummary,
    _SNAPSHOT_DIR,
    temperature_distribution,
)


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

    temperature_summary = temperature_distribution(nodes)
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
        temperature_distribution=temperature_summary,
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
