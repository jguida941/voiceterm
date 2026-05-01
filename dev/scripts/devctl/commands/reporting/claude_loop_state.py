"""Review-state helpers for the Claude loop surface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from ...review_channel.event_store import resolve_artifact_paths
from ...runtime.governance_scan import scan_repo_governance_safely
from ...runtime.master_plan_store import read_plan_rows_jsonl


def load_review_state(repo_root: Path) -> dict[str, Any]:
    try:
        artifact_paths = resolve_artifact_paths(repo_root=repo_root)
        path = Path(artifact_paths.projections_root) / "review_state.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def load_master_plan_authority(repo_root: Path) -> dict[str, Any]:
    governance = scan_repo_governance_safely(repo_root)
    master_plan = getattr(governance, "master_plan", None)
    payload = (
        dict(master_plan.to_dict())
        if hasattr(master_plan, "to_dict")
        else {}
    )
    typed_store = str(payload.get("typed_store_path") or "").strip()
    rows = _plan_rows_from_store(repo_root, typed_store)
    if not rows:
        rows = tuple(payload.get("rows") or ())
    payload["rows"] = [
        row.to_dict() if hasattr(row, "to_dict") else dict(row)
        for row in rows
        if hasattr(row, "to_dict") or isinstance(row, Mapping)
    ]
    payload["typed_store_path"] = typed_store
    if not typed_store:
        payload["authority_state"] = "missing_master_plan_store"
    else:
        payload["authority_state"] = "available" if payload["rows"] else "missing_rows"
    return payload


def _plan_rows_from_store(repo_root: Path, typed_store: str) -> tuple[object, ...]:
    if not typed_store:
        return ()
    path = Path(typed_store)
    if not path.is_absolute():
        path = repo_root / path
    try:
        return tuple(read_plan_rows_jsonl(path))
    except (OSError, ValueError):
        return ()


def extract_inbox_observation(review_state: Mapping[str, Any]) -> dict[str, Any]:
    reviewer_runtime = _mapping(review_state.get("reviewer_runtime"))
    observation = _mapping(reviewer_runtime.get("inbox_observation"))
    return dict(observation)


def extract_packet_attention(review_state: Mapping[str, Any]) -> dict[str, Any]:
    reviewer_runtime = _mapping(review_state.get("reviewer_runtime"))
    attention = _mapping(reviewer_runtime.get("packet_attention"))
    return dict(attention)


def extract_agent_runtime_clock(review_state: Mapping[str, Any]) -> dict[str, Any]:
    reviewer_runtime = _mapping(review_state.get("reviewer_runtime"))
    clock = _mapping(reviewer_runtime.get("agent_runtime_clock"))
    return dict(clock)


def typed_freshness_evidence(review_state: dict[str, Any]) -> dict[str, Any]:
    work_board = _mapping(review_state.get("agent_work_board"))
    coord_state = _mapping(review_state.get("coordination_state"))
    agent_sync = _mapping(review_state.get("agent_sync"))
    work_event = str(work_board.get("event_index") or "").strip()
    sync_event = str(agent_sync.get("event_index") or "").strip()
    coord_id = str(coord_state.get("contract_id") or "").strip()
    refreshed = str(review_state.get("timestamp") or "").strip()
    typed_present = bool(work_event or sync_event or coord_id)
    return {
        "source_latest_event_id": work_event or sync_event,
        "refreshed_at_utc": refreshed,
        "agent_work_board_event_index": work_event,
        "agent_sync_event_index": sync_event,
        "coordination_state_present": bool(coord_id),
        "typed_snapshot_state": "available" if typed_present else "unavailable",
    }


def extract_coordination_state(review_state: dict[str, Any]) -> dict[str, Any]:
    coord = review_state.get("coordination_state")
    return dict(coord) if isinstance(coord, dict) else {}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = [
    "extract_agent_runtime_clock",
    "extract_coordination_state",
    "extract_inbox_observation",
    "extract_packet_attention",
    "load_master_plan_authority",
    "load_review_state",
    "typed_freshness_evidence",
]
