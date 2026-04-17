"""Shared commit-pipeline visibility helpers for operator-facing reports."""

from __future__ import annotations

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
    if not pipeline_id:
        pipeline_pending = False
        commit_phase = "idle"
        commit_progress = "no_active_pipeline"
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
    return {
        "pipeline_pending": pipeline_pending,
        "commit_phase": commit_phase,
        "commit_progress": commit_progress,
    }
