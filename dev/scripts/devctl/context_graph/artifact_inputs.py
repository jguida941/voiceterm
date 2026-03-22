"""Artifact-backed input helpers for context-graph construction."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

ARTIFACT_INPUT_MAX_AGE = timedelta(hours=6)


def load_artifact_inputs(
    repo_root: Path,
) -> tuple[dict[str, int], set[str], dict[str, str]]:
    """Load hint counts, changed paths, and per-file severity from fresh
    file_topology.json when available.

    Returns (hint_counts, changed_paths, severity_by_file).
    severity_by_file maps file path → highest severity string found in that
    file's probe hints (e.g., "high", "medium", "low").
    """
    topology_path = repo_root / "dev" / "reports" / "probes" / "latest" / "file_topology.json"
    if not topology_path.exists():
        return {}, set(), {}
    try:
        payload = json.loads(topology_path.read_text(encoding="utf-8"))
        generated_at = _parse_generated_at(payload.get("generated_at"))
        if generated_at is None or _artifact_is_stale(generated_at):
            return {}, set(), {}
        nodes_payload = payload.get("nodes") or {}
        hint_counts: dict[str, int] = {}
        changed_paths: set[str] = set()
        severity_by_file: dict[str, str] = {}
        for file_path, file_data in nodes_payload.items():
            if not isinstance(file_data, dict):
                continue
            hint_count = file_data.get("hint_count", 0)
            if isinstance(hint_count, int) and hint_count > 0:
                hint_counts[file_path] = hint_count
            if file_data.get("changed"):
                changed_paths.add(file_path)
            # Extract highest severity from severity_counts if present
            severity_counts = file_data.get("severity_counts")
            if isinstance(severity_counts, dict) and severity_counts:
                highest = _highest_severity(severity_counts)
                if highest:
                    severity_by_file[file_path] = highest
        return hint_counts, changed_paths, severity_by_file
    except (OSError, ValueError, KeyError):
        return {}, set(), {}


_SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


def _highest_severity(severity_counts: dict[str, object]) -> str:
    """Return the highest severity key present in the counts dict."""
    best = ""
    best_rank = -1
    for key in severity_counts:
        rank = _SEVERITY_ORDER.get(str(key).lower(), -1)
        if rank > best_rank:
            best = str(key).lower()
            best_rank = rank
    return best


def resolve_graph_inputs(
    repo_root: Path,
    *,
    hint_counts: dict[str, int] | None,
    changed_paths: set[str] | None,
) -> tuple[dict[str, int], set[str], dict[str, str]]:
    """Fill missing graph inputs from a fresh topology artifact when available.

    Returns (hint_counts, changed_paths, severity_by_file).

    Explicit empty caller inputs (``{}`` or ``set()``) are preserved — only
    ``None`` triggers artifact fallback for that side.
    """
    if hint_counts is not None and changed_paths is not None:
        # Both explicitly provided — still load severity from artifact
        _, _, severity = load_artifact_inputs(repo_root)
        return hint_counts, changed_paths, severity
    artifact_hints, artifact_changed, artifact_severity = load_artifact_inputs(repo_root)
    resolved_hints = hint_counts if hint_counts is not None else artifact_hints
    resolved_changed = changed_paths if changed_paths is not None else artifact_changed
    return resolved_hints, resolved_changed, artifact_severity


def _parse_generated_at(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        generated_at = datetime.fromisoformat(text)
    except ValueError:
        return None
    if generated_at.tzinfo is None:
        return generated_at.replace(tzinfo=UTC)
    return generated_at.astimezone(UTC)


def _artifact_is_stale(generated_at: datetime) -> bool:
    return datetime.now(UTC) - generated_at > ARTIFACT_INPUT_MAX_AGE
