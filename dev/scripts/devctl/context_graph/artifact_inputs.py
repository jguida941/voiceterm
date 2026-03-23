"""Artifact-backed input helpers for context-graph construction."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ARTIFACT_INPUT_MAX_AGE = timedelta(hours=6)


def load_artifact_inputs(
    repo_root: Path,
) -> tuple[dict[str, int], set[str], dict[str, str]]:
    """Load hint counts, changed paths, and per-file severity from fresh
    probe artifacts when available.

    Returns (hint_counts, changed_paths, severity_by_file).

    hint_counts and changed_paths come from ``file_topology.json`` (node rows).
    severity_by_file comes from ``review_packet.json`` (hotspot rows), which
    is the only artifact that carries ``severity_counts`` per file.
    """
    probe_ts = _load_probe_run_timestamp(repo_root)
    hints, changed = _load_topology_inputs(repo_root, probe_timestamp=probe_ts)
    severity = _load_severity_from_review_packet(repo_root, probe_timestamp=probe_ts)
    return hints, changed, severity


def _load_probe_run_timestamp(repo_root: Path) -> datetime | None:
    """Load the probe-run timestamp from summary.json (the sibling artifact
    that carries ``generated_at``). Both ``file_topology.json`` and
    ``review_packet.json`` are emitted in the same run but do not carry
    their own ``generated_at`` in the current contract.
    """
    summary_path = repo_root / "dev" / "reports" / "probes" / "latest" / "summary.json"
    if not summary_path.exists():
        return None
    try:
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        return _parse_generated_at(payload.get("generated_at"))
    except (OSError, ValueError):
        return None


def _load_topology_inputs(
    repo_root: Path,
    probe_timestamp: datetime | None = None,
) -> tuple[dict[str, int], set[str]]:
    """Load hint counts and changed paths from file_topology.json."""
    topology_path = repo_root / "dev" / "reports" / "probes" / "latest" / "file_topology.json"
    if not topology_path.exists():
        return {}, set()
    try:
        payload = json.loads(topology_path.read_text(encoding="utf-8"))
        # Use probe-run timestamp from summary.json for freshness,
        # falling back to in-payload generated_at if present
        generated_at = probe_timestamp or _parse_generated_at(payload.get("generated_at"))
        if generated_at is None or _artifact_is_stale(generated_at):
            return {}, set()
        nodes_payload = payload.get("nodes") or {}
        hint_counts: dict[str, int] = {}
        changed_paths: set[str] = set()
        for file_path, file_data in nodes_payload.items():
            if not isinstance(file_data, dict):
                continue
            hint_count = file_data.get("hint_count", 0)
            if isinstance(hint_count, int) and hint_count > 0:
                hint_counts[file_path] = hint_count
            if file_data.get("changed"):
                changed_paths.add(file_path)
        return hint_counts, changed_paths
    except (OSError, ValueError, KeyError):
        return {}, set()


def _load_severity_from_review_packet(
    repo_root: Path,
    probe_timestamp: datetime | None = None,
) -> dict[str, str]:
    """Load per-file severity from review_packet.json hotspots.

    The review_packet.json hotspot rows carry ``severity_counts`` (e.g.,
    ``{"high": 5, "medium": 6}``). File_topology.json node rows do NOT
    carry this field.

    Freshness is gated from the sibling ``summary.json`` timestamp (passed
    as ``probe_timestamp``), not from an in-payload ``generated_at`` field
    that the current ``ReviewPacket`` contract does not emit.
    """
    packet_path = repo_root / "dev" / "reports" / "probes" / "latest" / "review_packet.json"
    if not packet_path.exists():
        return {}
    try:
        payload = json.loads(packet_path.read_text(encoding="utf-8"))
        # Use probe-run timestamp from summary.json for freshness
        generated_at = probe_timestamp or _parse_generated_at(payload.get("generated_at"))
        if generated_at is None or _artifact_is_stale(generated_at):
            return {}
        hotspots = payload.get("hotspots") or []
        severity_by_file: dict[str, str] = {}
        for hotspot in hotspots:
            if not isinstance(hotspot, dict):
                continue
            file_path = hotspot.get("file")
            if not file_path:
                continue
            severity_counts = hotspot.get("severity_counts")
            if isinstance(severity_counts, dict) and severity_counts:
                highest = _highest_severity(severity_counts)
                if highest:
                    severity_by_file[str(file_path)] = highest
        return severity_by_file
    except (OSError, ValueError, KeyError):
        return {}


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
        return generated_at.replace(tzinfo=timezone.utc)
    return generated_at.astimezone(timezone.utc)


def _artifact_is_stale(generated_at: datetime) -> bool:
    return datetime.now(timezone.utc) - generated_at > ARTIFACT_INPUT_MAX_AGE
