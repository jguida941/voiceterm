"""Staged-tree arguments for governed commit guard replay."""

from __future__ import annotations


def guard_check_args_for_pipeline(pipeline: object | None) -> tuple[str, ...]:
    """Return `devctl check` args for staged commit snapshots."""
    if not pipeline_has_checkpoint_snapshot(pipeline):
        return ()
    staged_tree_hash = _pipeline_staged_tree_hash(pipeline)
    if not staged_tree_hash:
        return ()
    return ("--commit-snapshot", "--since-ref", "HEAD", "--head-ref", staged_tree_hash)


def pipeline_has_checkpoint_snapshot(pipeline: object | None) -> bool:
    if pipeline is None:
        return False
    intent = getattr(pipeline, "intent", None)
    if intent is None:
        return False
    return bool(
        getattr(intent, "validation_plan", None)
        or getattr(intent, "staged_tree_hash", "")
        or getattr(intent, "staged_path_count", 0)
    )


def _pipeline_staged_tree_hash(pipeline: object | None) -> str:
    if pipeline is None:
        return ""
    intent = getattr(pipeline, "intent", None)
    if intent is None:
        return ""
    plan = getattr(intent, "validation_plan", None)
    if plan is not None:
        staged_tree_hash = str(getattr(plan, "staged_tree_hash", "") or "").strip()
        if staged_tree_hash:
            return staged_tree_hash
    return str(getattr(intent, "staged_tree_hash", "") or "").strip()
