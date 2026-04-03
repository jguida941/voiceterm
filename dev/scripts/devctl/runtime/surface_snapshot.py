"""Shared surface-generation snapshot helpers for startup/review projections."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from hashlib import sha256


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
            drop_keys=("snapshot_id",),
        ),
        "push_decision": _normalize_push_decision(push_decision),
    }
    digest = sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    return f"snap-{digest}"


def attach_snapshot_id(
    payload: object,
    snapshot_id: str,
) -> dict[str, object]:
    """Copy one mapping-like payload and attach the shared snapshot id."""
    mapping = _normalize_payload(payload, drop_keys=("snapshot_id",))
    if snapshot_id:
        mapping["snapshot_id"] = snapshot_id
    return mapping


def _normalize_push_decision(payload: object) -> dict[str, object]:
    mapping = _normalize_payload(payload, drop_keys=("snapshot_id",))
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
    payload: object,
    *,
    drop_keys: tuple[str, ...],
) -> dict[str, object]:
    if payload is None:
        return {}
    if hasattr(payload, "to_dict") and callable(getattr(payload, "to_dict")):
        mapping = payload.to_dict()
    elif is_dataclass(payload):
        mapping = asdict(payload)
    elif isinstance(payload, Mapping):
        mapping = dict(payload)
    else:
        return {}
    for key in drop_keys:
        mapping.pop(key, None)
    return mapping
