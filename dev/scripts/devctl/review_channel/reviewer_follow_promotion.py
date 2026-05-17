"""Promotion helpers shared by reviewer-follow runtime loops."""

from __future__ import annotations

from pathlib import Path

from .current_session_projection import bridge_implementer_state_hash
from .handoff import extract_bridge_snapshot, summarize_bridge_liveness
from .heartbeat import bridge_excluded_rel_paths, compute_non_audit_worktree_hash
from .plan_resolution import resolve_promotion_plan_path
from .promotion import (
    derive_promotion_candidate,
    promote_bridge_instruction,
    validate_promotion_ready,
)


def maybe_auto_promote(
    *,
    args,
    repo_root: Path,
    paths: dict[str, object],
    bridge_path: Path,
) -> dict[str, object] | None:
    if not bool(getattr(args, "auto_promote", False)):
        return None
    if not bridge_path.exists():
        return {"attempted": False, "promoted": False, "reason": "bridge_missing"}
    explicit_plan_path = paths.get("promotion_plan_path")
    if not isinstance(explicit_plan_path, Path):
        explicit_plan_path = None
    resolution = resolve_promotion_plan_path(
        repo_root=repo_root,
        bridge_path=bridge_path,
        explicit_plan_path=explicit_plan_path,
    )
    promotion_plan_path = resolution.path
    if promotion_plan_path is None:
        return {
            "attempted": True,
            "promoted": False,
            "reason": "scope_missing",
            "detail": resolution.detail or "Unable to resolve scoped plan path.",
        }

    bridge_text = bridge_path.read_text(encoding="utf-8")
    snapshot = extract_bridge_snapshot(bridge_text)
    readiness_errors = validate_promotion_ready(snapshot)
    try:
        current_hash = compute_non_audit_worktree_hash(
            repo_root=repo_root,
            excluded_rel_paths=bridge_excluded_rel_paths(
                repo_root=repo_root,
                bridge_path=bridge_path,
            ),
        )
    except (OSError, ValueError):
        current_hash = None
    liveness = summarize_bridge_liveness(
        snapshot,
        current_worktree_hash=current_hash,
    )
    if liveness.reviewed_hash_current is False:
        readiness_errors.append("reviewed_hash_stale")
    candidate = derive_promotion_candidate(
        repo_root=repo_root,
        promotion_plan_path=promotion_plan_path,
        require_exists=False,
    )
    if candidate is None:
        return {
            "attempted": True,
            "promoted": False,
            "reason": "no_unchecked_items",
        }
    if readiness_errors:
        return {
            "attempted": True,
            "promoted": False,
            "reason": "not_ready",
            "errors": readiness_errors,
        }

    promoted = promote_bridge_instruction(
        repo_root=repo_root,
        bridge_path=bridge_path,
        promotion_plan_path=promotion_plan_path,
        expected_instruction_revision=str(
            snapshot.metadata.get("current_instruction_revision") or ""
        ),
        expected_implementer_state_hash=bridge_implementer_state_hash(snapshot),
    )
    return {
        "attempted": True,
        "promoted": True,
        "source_path": promoted.source_path,
        "checklist_item": promoted.checklist_item,
        "instruction": promoted.instruction,
    }
