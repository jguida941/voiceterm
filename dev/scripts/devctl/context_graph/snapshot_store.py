"""Read/list/resolve helpers for saved context-graph snapshots."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ..config import get_repo_root
from .snapshot_payload import (
    CONTEXT_GRAPH_SNAPSHOT_CONTRACT_ID,
    CONTEXT_GRAPH_SNAPSHOT_SCHEMA_VERSION,
    ContextGraphSnapshot,
    SnapshotResolutionError,
    _SNAPSHOT_DIR,
)
from .snapshot_payload import (
    coerce_int_map,
    coerce_object_list,
    load_temperature_distribution,
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
        nodes_by_kind=coerce_int_map(payload.get("nodes_by_kind")),
        edges_by_kind=coerce_int_map(payload.get("edges_by_kind")),
        temperature_distribution=load_temperature_distribution(
            payload.get("temperature_distribution")
        ),
        nodes=coerce_object_list(payload.get("nodes")),
        edges=coerce_object_list(payload.get("edges")),
    )


def list_context_graph_snapshots(
    *,
    repo_root: Path | None = None,
    snapshot_dir: Path | None = None,
) -> list[Path]:
    """Return valid snapshot paths ordered by capture time, not filesystem mtime."""
    effective_snapshot_dir = _resolve_snapshot_dir(
        repo_root=repo_root,
        snapshot_dir=snapshot_dir,
    )
    if not effective_snapshot_dir.exists():
        return []
    ordered_paths: list[tuple[tuple[str, str, str], Path]] = []
    for path in effective_snapshot_dir.glob("*.json"):
        resolved = path.resolve()
        try:
            snapshot = load_context_graph_snapshot(resolved)
        except (OSError, json.JSONDecodeError, SnapshotResolutionError):
            continue
        ordered_paths.append((_snapshot_sort_key(resolved, snapshot), resolved))
    ordered_paths.sort(key=lambda item: item[0])
    return [path for _sort_key, path in ordered_paths]


def resolve_context_graph_snapshot_ref(
    ref: str | None,
    *,
    repo_root: Path | None = None,
    exclude: Path | None = None,
) -> Path:
    """Resolve a snapshot ref/path against the canonical graph-snapshot store."""
    effective_repo_root = (repo_root or get_repo_root()).resolve()
    excluded = exclude.resolve() if exclude is not None else None
    token = (ref or "").strip()
    if token:
        direct = Path(token).expanduser()
        if direct.exists():
            return _resolve_direct_snapshot_path(direct, excluded=excluded, ref_label=token)
        candidate = effective_repo_root / token
        if candidate.exists():
            return _resolve_direct_snapshot_path(candidate, excluded=excluded, ref_label=token)
    available = list_context_graph_snapshots(repo_root=effective_repo_root)
    if excluded is not None:
        available = [path for path in available if path.resolve() != excluded]
    if not available:
        raise SnapshotResolutionError("no ContextGraphSnapshot artifacts available")
    if not token or token == "latest":
        return available[-1]
    if token == "previous":
        if len(available) < 2:
            raise SnapshotResolutionError("previous snapshot requested but only one snapshot exists")
        return available[-2]
    for path in available:
        if token in {path.name, path.stem}:
            return path
    matches = [path for path in available if path.name.startswith(token)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise SnapshotResolutionError(f"snapshot ref {token!r} is ambiguous")
    raise SnapshotResolutionError(f"snapshot ref {token!r} not found")


def format_context_graph_snapshot_path(path: str | Path) -> str:
    """Return a portable snapshot path for machine output and markdown."""
    resolved = Path(path).resolve()
    snapshot_parts = _SNAPSHOT_DIR.parts
    resolved_parts = resolved.parts
    max_index = len(resolved_parts) - len(snapshot_parts) + 1
    for index in range(max(0, max_index)):
        if resolved_parts[index : index + len(snapshot_parts)] == snapshot_parts:
            return Path(*resolved_parts[index:]).as_posix()
    return resolved.name


def _resolve_direct_snapshot_path(
    path: Path,
    *,
    excluded: Path | None,
    ref_label: str,
) -> Path:
    resolved = path.resolve()
    _validate_snapshot_resolution_exclusion(resolved, excluded)
    try:
        load_context_graph_snapshot(resolved)
    except (OSError, json.JSONDecodeError, SnapshotResolutionError) as exc:
        raise SnapshotResolutionError(
            f"snapshot ref {ref_label!r} is not a valid {CONTEXT_GRAPH_SNAPSHOT_CONTRACT_ID}: {exc}"
        ) from exc
    return resolved


def _resolve_snapshot_dir(
    *,
    repo_root: Path | None,
    snapshot_dir: Path | None,
) -> Path:
    if snapshot_dir is not None:
        return snapshot_dir.resolve()
    effective_repo_root = (repo_root or get_repo_root()).resolve()
    return effective_repo_root / _SNAPSHOT_DIR


def _snapshot_sort_key(
    path: Path,
    snapshot: ContextGraphSnapshot,
) -> tuple[str, str, str]:
    generated_at = snapshot.generated_at_utc.strip()
    filename_timestamp = _snapshot_filename_timestamp(path)
    primary_timestamp = generated_at or filename_timestamp
    return (
        primary_timestamp,
        filename_timestamp or generated_at,
        path.name,
    )


def _snapshot_filename_timestamp(path: Path) -> str:
    parts = path.stem.rsplit("_", 1)
    if len(parts) != 2:
        return ""
    try:
        parsed = datetime.strptime(parts[1], "%Y%m%dT%H%M%SZ")
    except ValueError:
        return ""
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_snapshot_resolution_exclusion(path: Path, excluded: Path | None) -> None:
    if excluded is not None and path == excluded:
        raise SnapshotResolutionError("snapshot diff requires distinct --from and --to refs")
