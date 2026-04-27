"""Shared commit-pipeline visibility helpers for operator-facing reports."""

from __future__ import annotations

from ...runtime.remote_commit_pipeline_state import (
    STATE_DELIVERED_LOCALLY_PENDING_PUBLISH,
)

_COMMIT_PENDING_PIPELINE_STATES = frozenset(
    {
        "staged",
        "guards_running",
        "guards_passed",
        "operator_approval_pending",
        "approved",
        "commit_pending",
        "push_pending",
    }
)


def commit_visibility_payload(pipeline) -> dict[str, object]:
    """Return explicit progress fields for one governed commit pipeline."""
    pipeline_id = str(getattr(pipeline, "pipeline_id", "") or "").strip()
    state = str(getattr(pipeline, "state", "") or "").strip()
    approval_state = str(getattr(pipeline, "approval_state", "") or "").strip()
    pipeline_pending = state in _COMMIT_PENDING_PIPELINE_STATES
    commit_phase = state or "unknown"
    commit_progress = f"pipeline_state:{state or 'unknown'}"
    git_commit_state = _git_commit_state(pipeline, state=state)
    publication_state = _publication_state(pipeline, state=state)
    post_commit_state = _post_commit_state(pipeline, state=state)
    if not pipeline_id:
        pipeline_pending = False
        commit_phase = "idle"
        commit_progress = "no_active_pipeline"
    elif state == "commit_recorded":
        pipeline_pending = False
        commit_phase = "committed"
        commit_progress = "commit_recorded"
    elif state == "push_pending":
        pipeline_pending = True
        commit_phase = "ready_to_push"
        commit_progress = "commit_recorded_waiting_for_push"
    elif state == "push_completed":
        pipeline_pending = False
        commit_phase = "published"
        commit_progress = "push_completed"
    elif state == STATE_DELIVERED_LOCALLY_PENDING_PUBLISH:
        pipeline_pending = False
        commit_phase = "delivered_local_publication_pending"
        commit_progress = "local_commit_delivered_publication_pending"
    elif state == "rejected":
        pipeline_pending = False
        commit_phase = "rejected"
        commit_progress = "operator_rejected_pipeline"
    elif state == "guards_failed":
        pipeline_pending = False
        commit_phase = "guards_failed"
        commit_progress = "guard_bundle_failed"
    elif state == "push_blocked":
        pipeline_pending = False
        commit_phase = "push_blocked"
        commit_progress = "publication_requires_recovery"
    elif approval_state == "approved" or state in {"approved", "commit_pending"}:
        pipeline_pending = True
        commit_phase = "ready_to_commit"
        commit_progress = "approval_recorded_waiting_for_commit"
    elif state == "operator_approval_pending" or approval_state == "pending":
        pipeline_pending = True
        commit_phase = "awaiting_operator_approval"
        commit_progress = "guarded_pipeline_waiting_for_operator_approval"
    elif state in {"staged", "guards_running", "guards_passed"}:
        pipeline_pending = True
        commit_phase = "preflight"
        commit_progress = "building_guarded_commit_pipeline"
    payload: dict[str, object] = {}
    payload["pipeline_pending"] = pipeline_pending
    payload["commit_phase"] = commit_phase
    payload["commit_progress"] = commit_progress
    payload["git_commit_state"] = git_commit_state
    payload["post_commit_state"] = post_commit_state
    payload["publication_state"] = publication_state
    return payload


def _git_commit_state(pipeline, *, state: str) -> str:
    commit_sha = str(getattr(pipeline, "commit_sha", "") or "").strip()
    if commit_sha:
        return "landed"
    commit_result = getattr(pipeline, "commit_result", None)
    reason = str(getattr(commit_result, "reason", "") or "").strip()
    ok = getattr(commit_result, "ok", None)
    if ok is False or reason in {"commit_failed", "git_index_write_blocked"}:
        return "failed"
    if state in {"commit_pending", "approved"}:
        return "pending"
    return "not_started"


def _post_commit_state(pipeline, *, state: str) -> str:
    if _git_commit_state(pipeline, state=state) == "failed":
        return "blocked_by_commit_failure"
    if state == "commit_recorded":
        return "commit_recorded_projection_pending"
    if state == "push_pending":
        return "publication_pending"
    if state == STATE_DELIVERED_LOCALLY_PENDING_PUBLISH:
        return "publication_pending"
    if state == "push_completed":
        return "complete"
    if state == "push_blocked" and str(getattr(pipeline, "commit_sha", "") or "").strip():
        return "publication_blocked_after_commit"
    return "not_started"


def _publication_state(pipeline, *, state: str) -> str:
    commit_sha = str(getattr(pipeline, "commit_sha", "") or "").strip()
    if state == "push_completed":
        return "published"
    if state == STATE_DELIVERED_LOCALLY_PENDING_PUBLISH and commit_sha:
        return "pending_after_local_delivery"
    if state in {"commit_recorded", "push_pending"} and commit_sha:
        return "awaiting_governed_push"
    if state == "push_blocked" and commit_sha:
        return "blocked_after_commit"
    if state == "push_blocked":
        return "blocked_before_commit"
    return "not_ready"
