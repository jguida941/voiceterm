"""Promotion helpers extracted from bridge action support."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from .handoff import BridgeSnapshot, extract_bridge_snapshot, summarize_bridge_liveness
from .promotion import derive_promotion_candidate, validate_promotion_ready


def maybe_auto_promote_next_task(
    *,
    args,
    repo_root: Path,
    bridge_path: Path,
    promotion_plan_path: Path | None,
    promote_bridge_instruction_fn: Callable[..., object],
) -> tuple[object | None, list[str]]:
    """Auto-promote the next task when the bridge is ready."""
    if not getattr(args, "auto_promote", False):
        return None, []
    if promotion_plan_path is None:
        return None, ["Auto-promote skipped: scoped plan unresolved (`scope_missing`)."]

    if bridge_path.exists():
        snapshot = extract_bridge_snapshot(
            bridge_path.read_text(encoding="utf-8")
        )
    else:
        snapshot = BridgeSnapshot(metadata={}, sections={})

    readiness_errors = validate_promotion_ready(snapshot)
    try:
        from . import heartbeat as heartbeat_module

        current_hash = heartbeat_module.compute_non_audit_worktree_hash(
            repo_root=repo_root,
            excluded_rel_paths=("code_audit.md",),
        )
    except (ValueError, OSError):
        current_hash = None
    liveness = summarize_bridge_liveness(
        snapshot,
        current_worktree_hash=current_hash,
    )
    if liveness.reviewed_hash_current is False:
        readiness_errors.append(
            "Review content is stale: the worktree has changed since the last reviewed hash. Re-review before auto-promoting."
        )

    candidate = derive_promotion_candidate(
        repo_root=repo_root,
        promotion_plan_path=promotion_plan_path,
        require_exists=False,
    )
    if readiness_errors or candidate is None:
        return None, []

    promoted = promote_bridge_instruction_fn(
        repo_root=repo_root,
        bridge_path=bridge_path,
        promotion_plan_path=promotion_plan_path,
    )
    return promoted, [f"Auto-promoted next task: {candidate.checklist_item}"]


def promotion_plan_rel_for_session(
    *,
    promotion_plan_path: Path | None,
    repo_root: Path,
    display_path_fn: Callable[..., str],
) -> str:
    """Return a stable session-surface string for the promotion plan."""
    if isinstance(promotion_plan_path, Path):
        return display_path_fn(
            promotion_plan_path,
            repo_root=repo_root,
        )
    return "scope-unresolved"
