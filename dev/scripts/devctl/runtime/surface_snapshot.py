"""Shared snapshot-id/zref helpers for startup/review projections."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from hashlib import sha256
from typing import Protocol, runtime_checkable


def build_surface_snapshot_id(
    *,
    reviewer_runtime: object = None,
    commit_pipeline: object = None,
    push_decision: object = None,
) -> str:
    """Return one deterministic snapshot id for aligned typed surfaces."""
    payload = {
        "reviewer_runtime": _normalize_payload(reviewer_runtime, drop_keys=()),
        "commit_pipeline": _normalize_payload(
            commit_pipeline,
            drop_keys=("snapshot_id", "zref"),
        ),
        "push_decision": _normalize_push_decision(push_decision),
    }
    digest = sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    return f"snap-{digest}"


def build_surface_zref(
    *,
    snapshot_id: str,
    head_sha: str,
) -> str:
    """Return a compact human-readable handle for one snapshot/head pair."""
    snapshot_prefix = _identity_prefix(snapshot_id)
    head_prefix = _identity_prefix(head_sha)
    if not snapshot_prefix and not head_prefix:
        return ""
    return f"zref_{snapshot_prefix or 'unknown'}_{head_prefix or 'unknown'}"


@runtime_checkable
class SupportsToDict(Protocol):
    """Protocol for typed payloads that expose a mapping projection."""

    def to_dict(self) -> Mapping[str, object]: ...


def _normalize_push_decision(payload: object) -> dict[str, object]:
    mapping = _normalize_payload(payload, drop_keys=("snapshot_id", "zref"))
    backlog = mapping.get("publication_backlog")
    backlog_mapping = backlog if isinstance(backlog, Mapping) else {}
    return {
        "worktree_clean": bool(mapping.get("worktree_clean")),
        "review_gate_allows_push": bool(mapping.get("review_gate_allows_push")),
        "has_remote_work_to_push": bool(mapping.get("has_remote_work_to_push")),
        "push_eligible_now": bool(mapping.get("push_eligible_now")),
        "action": str(mapping.get("action") or ""),
        "reason": str(mapping.get("reason") or ""),
        "next_step_command": str(mapping.get("next_step_command") or ""),
        "publication_guidance": str(mapping.get("publication_guidance") or ""),
        "publication_backlog": {
            "backlog_state": str(backlog_mapping.get("backlog_state") or ""),
            "backlog_recommended": bool(backlog_mapping.get("backlog_recommended")),
            "backlog_urgent": bool(backlog_mapping.get("backlog_urgent")),
        },
    }


def _normalize_payload(
    payload: Mapping[str, object] | SupportsToDict | object | None,
    *,
    drop_keys: tuple[str, ...],
) -> dict[str, object]:
    if payload is None:
        return {}
    if isinstance(payload, Mapping):
        mapping = dict(payload)
    elif isinstance(payload, SupportsToDict):
        mapping = dict(payload.to_dict())
    elif is_dataclass(payload):
        mapping = asdict(payload)
    else:
        return {}
    for key in drop_keys:
        mapping.pop(key, None)
    return mapping


def _identity_prefix(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if "-" in text:
        text = text.split("-", 1)[-1]
    return text[:8]
