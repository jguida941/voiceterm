"""Pipeline binding checks for commit action-request authority."""

from __future__ import annotations

from pathlib import Path

from .governed_executor_git import pipeline_is_stale_for_current_repo


def pipeline_binding_block(
    *,
    repo_root: Path,
    grant: object,
    pipeline: object | None,
) -> str:
    """Return a denial reason when packet evidence does not match the pipeline."""
    if not pipeline_binding_required(repo_root=repo_root, pipeline=pipeline):
        return ""
    pipeline_generation_value = pipeline_generation(pipeline)
    pipeline_hash_value = pipeline_hash(pipeline)
    grant_generation = _text(getattr(grant, "pipeline_generation", ""))
    grant_snapshot_hash = _text(getattr(grant, "staged_snapshot_hash", ""))
    if pipeline_generation_value or pipeline_hash_value:
        if not grant_generation:
            return "action_request_pipeline_generation_missing"
        if not grant_snapshot_hash:
            return "action_request_staged_snapshot_missing"
    if grant_generation and grant_generation != pipeline_generation_value:
        return "action_request_pipeline_generation_mismatch"
    if grant_snapshot_hash and grant_snapshot_hash != pipeline_hash_value:
        return "action_request_staged_snapshot_mismatch"
    return ""


def pipeline_binding_required(*, repo_root: Path, pipeline: object | None) -> bool:
    """Return whether the current pipeline is live enough to bind this packet."""
    if not (pipeline_generation(pipeline) or pipeline_hash(pipeline)):
        return False
    return not pipeline_is_stale_for_current_repo(pipeline, repo_root=repo_root)


def pipeline_generation(pipeline: object | None) -> str:
    """Return the typed pipeline generation id."""
    return _text(getattr(pipeline, "generation_id", ""))


def pipeline_hash(pipeline: object | None) -> str:
    """Return the typed staged-tree hash bound to the pipeline."""
    intent = getattr(pipeline, "intent", None)
    return _text(getattr(intent, "staged_tree_hash", ""))


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "pipeline_binding_block",
    "pipeline_binding_required",
    "pipeline_generation",
    "pipeline_hash",
]
