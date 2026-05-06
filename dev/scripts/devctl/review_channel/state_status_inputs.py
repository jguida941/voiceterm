"""Input-loading helpers for review-channel status projection."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from ..runtime.review_state_locator import load_current_review_state_payload
from .core import LaneAssignment, ensure_launcher_prereqs
from .handoff import bridge_liveness_to_dict, summarize_bridge_liveness
from .heartbeat import bridge_excluded_rel_paths, compute_non_audit_worktree_hash
from .lifecycle_state import read_publisher_state, read_reviewer_supervisor_state
from .reviewer_worker import check_review_needed, reviewer_worker_tick_to_dict


def load_status_lanes(
    *,
    review_channel_path: Path,
    bridge_path: Path,
    execution_mode: str,
) -> list[LaneAssignment]:
    _, lanes = ensure_launcher_prereqs(
        review_channel_path=review_channel_path,
        bridge_path=bridge_path,
        execution_mode=execution_mode,
    )
    return lanes


def build_status_bridge_liveness(
    *,
    bridge_snapshot,
    repo_root: Path,
    bridge_path: Path,
) -> dict[str, object]:
    return bridge_liveness_to_dict(
        summarize_bridge_liveness(
            bridge_snapshot,
            current_worktree_hash=current_worktree_hash(
                repo_root=repo_root,
                bridge_path=bridge_path,
            ),
        )
    )


def current_worktree_hash(*, repo_root: Path, bridge_path: Path) -> str | None:
    try:
        return compute_non_audit_worktree_hash(
            repo_root=repo_root,
            excluded_rel_paths=bridge_excluded_rel_paths(
                repo_root=repo_root,
                bridge_path=bridge_path,
            ),
        )
    except (ValueError, OSError):
        return None


def load_lifecycle_states(output_root: Path) -> tuple[dict[str, object], dict[str, object]]:
    return (
        read_publisher_state(output_root),
        read_reviewer_supervisor_state(output_root),
    )


def load_prior_review_state(
    *,
    repo_root: Path,
    output_root: Path,
) -> dict[str, object] | None:
    canonical_payload = load_current_review_state_payload(
        repo_root,
        review_status_dir=output_root,
        prefer_cached_projection=False,
        allow_live_refresh=False,
    )
    local_payload = _read_json_mapping(output_root / "review_state.json")
    state_payload = _read_json_mapping(output_root.parent / "state" / "latest.json")
    if isinstance(canonical_payload, dict) and isinstance(state_payload, dict):
        canonical_payload = _merge_prior_review_state(canonical_payload, state_payload)
    if isinstance(local_payload, dict) and isinstance(state_payload, dict):
        local_payload = _merge_prior_review_state(local_payload, state_payload)
    if isinstance(canonical_payload, dict) and isinstance(local_payload, dict):
        return _merge_prior_review_state(canonical_payload, local_payload)
    if isinstance(canonical_payload, dict):
        return canonical_payload
    if isinstance(local_payload, dict):
        return local_payload
    return None


def _read_json_mapping(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def build_reviewer_worker_snapshot(
    *,
    repo_root: Path,
    bridge_path: Path,
    bridge_text: str,
) -> dict[str, object]:
    return reviewer_worker_tick_to_dict(
        check_review_needed(
            repo_root=repo_root,
            bridge_path=bridge_path,
            bridge_text=bridge_text,
            current_hash=current_worktree_hash(
                repo_root=repo_root,
                bridge_path=bridge_path,
            ),
        )
    )


def _merge_prior_review_state(
    canonical_payload: dict[str, object],
    local_payload: dict[str, object],
) -> dict[str, object]:
    local_hash = _reviewer_accepted_implementer_state_hash(local_payload)
    merged: dict[str, object] = dict(canonical_payload)
    target = merged
    nested_review_state = merged.get("review_state")
    if isinstance(nested_review_state, Mapping):
        target = dict(nested_review_state)
        merged["review_state"] = target

    if local_hash and not _reviewer_accepted_implementer_state_hash(canonical_payload):
        reviewer_runtime = target.get("reviewer_runtime")
        target["reviewer_runtime"] = (
            dict(reviewer_runtime) if isinstance(reviewer_runtime, Mapping) else {}
        )
        review_acceptance = target["reviewer_runtime"].get("review_acceptance")
        target["reviewer_runtime"]["review_acceptance"] = (
            dict(review_acceptance) if isinstance(review_acceptance, Mapping) else {}
        )
        target["reviewer_runtime"]["review_acceptance"][
            "reviewer_accepted_implementer_state_hash"
        ] = local_hash
    local_target: Mapping[str, object] = local_payload
    local_nested_review_state = local_payload.get("review_state")
    if isinstance(local_nested_review_state, Mapping):
        local_target = local_nested_review_state
    for field in ("latest_reviewer_checkpoint", "packet_continuity_index"):
        if field not in target and isinstance(local_target.get(field), Mapping):
            target[field] = dict(local_target[field])
    local_packets = local_target.get("packets")
    target_packets = target.get("packets")
    if isinstance(local_packets, list) and (
        not isinstance(target_packets, list)
        or len(local_packets) > len(target_packets)
    ):
        target["packets"] = list(local_packets)
    return merged


def _reviewer_accepted_implementer_state_hash(payload: Mapping[str, object]) -> str:
    review_state = payload.get("review_state")
    if isinstance(review_state, Mapping):
        payload = review_state
    reviewer_runtime = payload.get("reviewer_runtime")
    if not isinstance(reviewer_runtime, Mapping):
        return ""
    review_acceptance = reviewer_runtime.get("review_acceptance")
    if not isinstance(review_acceptance, Mapping):
        return ""
    return str(
        review_acceptance.get("reviewer_accepted_implementer_state_hash") or ""
    ).strip()
