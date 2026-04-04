"""Focused tests for event-backed push-state parity."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.review_channel.event_projection import (
    enrich_event_review_state,
)
from dev.scripts.devctl.runtime.remote_commit_pipeline_models import (
    RemoteCommitPipelineContract,
)
from dev.scripts.devctl.runtime.review_state_models import (
    ReviewCurrentSessionState,
)
from dev.scripts.devctl.runtime.reviewer_runtime_models import (
    ReviewerAcceptanceState,
    ReviewerRuntimeContract,
)


@dataclass(frozen=True)
class _DummyCollaboration:
    contract_id: str = "CollaborationSession"


_REVIEWER_RUNTIME = ReviewerRuntimeContract(
    reviewer_mode="single_agent",
    effective_reviewer_mode="single_agent",
    publish_clear=True,
    review_acceptance=ReviewerAcceptanceState(
        current_verdict="- accepted",
        open_findings="- none",
        review_accepted=True,
    ),
)


def _current_session() -> ReviewCurrentSessionState:
    return ReviewCurrentSessionState(
        current_instruction="Review the publish state.",
        current_instruction_revision="rev-1",
        implementer_status="- working",
        implementer_ack="- acknowledged",
        implementer_ack_revision="rev-1",
        implementer_ack_state="current",
    )


@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_service_identity_state",
    return_value={},
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_attach_auth_policy_state",
    return_value={},
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_attach_auth_policy",
    return_value={},
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_service_identity",
    return_value={},
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_event_bridge_state_projection",
    return_value={},
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_surface_snapshot_id",
    return_value="snap-1",
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.load_remote_commit_pipeline_contract",
    return_value=RemoteCommitPipelineContract(),
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_reviewer_runtime_contract",
    return_value=_REVIEWER_RUNTIME,
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_collaboration_session",
    return_value=_DummyCollaboration(),
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_event_current_session",
    return_value=_current_session(),
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_bridge_push_enforcement_state",
    return_value={
        "current_branch": "feature/demo",
        "current_head_commit": "abc123",
        "default_remote": "origin",
        "latest_push_report_path": "dev/reports/push/latest.json",
        "latest_push_report_branch": "feature/demo",
        "latest_push_report_remote": "origin",
        "latest_push_report_head_commit": "abc123",
        "latest_push_report_status": "published_remote",
        "latest_push_report_reason": "post_push_bundle_pending",
        "latest_push_report_published_remote": True,
        "latest_push_report_post_push_green": False,
        "current_approved_target_identity": "",
        "latest_push_report_approved_target_identity": "",
        "latest_push_report_matches_current_approved_target": True,
        "latest_push_report_matches_current_branch": True,
        "latest_push_report_matches_current_head": True,
        "worktree_clean": True,
        "worktree_dirty": False,
        "checkpoint_required": False,
        "safe_to_continue_editing": True,
        "recommended_action": "no_push_needed",
        "publication_backlog_state": "none",
    },
)
def test_enrich_event_review_state_attaches_push_truth(
    _push_enforcement_mock,
    _current_session_mock,
    _collaboration_mock,
    _reviewer_runtime_mock,
    _pipeline_mock,
    _snapshot_id_mock,
    _bridge_state_mock,
    _service_identity_mock,
    _attach_auth_policy_mock,
    _attach_auth_policy_state_mock,
    _service_identity_state_mock,
) -> None:
    review_state = {
        "timestamp": "2026-04-04T00:00:00Z",
        "review": {"plan_id": "MP-377", "session_id": "sess-1"},
        "queue": {},
        "_compat": {"runtime": {"daemons": {}}},
    }

    enriched, extras = enrich_event_review_state(
        review_state=review_state,
        repo_root=Path("."),
        review_channel_path=Path("dev/active/review_channel.md"),
        projections_root=Path("dev/reports/review_channel/latest"),
    )

    assert extras["bridge_liveness"]["push_enforcement"]["latest_push_report_path"]
    assert enriched["_compat"]["push_enforcement"]["latest_push_report_path"]
    assert enriched["_compat"]["push_decision"]["action"] == "no_push_needed"
    assert enriched["_compat"]["doctor"]["publication_source"] == "latest_push_report"
    assert enriched["_compat"]["doctor"]["published_remote"] is True


_SNAPSHOT_PUSH_ENFORCEMENT: dict[str, object] = {
    "current_branch": "feature/snapshot",
    "current_head_commit": "snap456",
    "default_remote": "origin",
    "latest_push_report_path": "dev/reports/push/latest.json",
    "latest_push_report_branch": "feature/snapshot",
    "latest_push_report_remote": "origin",
    "latest_push_report_head_commit": "snap456",
    "latest_push_report_status": "published_remote",
    "latest_push_report_reason": "post_push_bundle_pending",
    "latest_push_report_published_remote": True,
    "latest_push_report_post_push_green": False,
    "current_approved_target_identity": "",
    "latest_push_report_approved_target_identity": "",
    "latest_push_report_matches_current_approved_target": True,
    "latest_push_report_matches_current_branch": True,
    "latest_push_report_matches_current_head": True,
    "worktree_clean": True,
    "worktree_dirty": False,
    "checkpoint_required": False,
    "safe_to_continue_editing": True,
    "recommended_action": "no_push_needed",
    "publication_backlog_state": "none",
}


@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_service_identity_state",
    return_value={},
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_attach_auth_policy_state",
    return_value={},
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_attach_auth_policy",
    return_value={},
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_service_identity",
    return_value={},
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_event_bridge_state_projection",
    return_value={},
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_surface_snapshot_id",
    return_value="snap-2",
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.load_remote_commit_pipeline_contract",
    return_value=RemoteCommitPipelineContract(),
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_reviewer_runtime_contract",
    return_value=_REVIEWER_RUNTIME,
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_collaboration_session",
    return_value=_DummyCollaboration(),
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_event_current_session",
    return_value=_current_session(),
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_bridge_push_enforcement_state",
)
def test_enrich_uses_snapshot_push_enforcement_when_provided(
    push_enforcement_mock,
    _current_session_mock,
    _collaboration_mock,
    _reviewer_runtime_mock,
    _pipeline_mock,
    _snapshot_id_mock,
    _bridge_state_mock,
    _service_identity_mock,
    _attach_auth_policy_mock,
    _attach_auth_policy_state_mock,
    _service_identity_state_mock,
) -> None:
    """When push_enforcement is passed, the live filesystem helper is skipped."""
    review_state = {
        "timestamp": "2026-04-04T00:00:00Z",
        "review": {"plan_id": "MP-377", "session_id": "sess-2"},
        "queue": {},
        "_compat": {"runtime": {"daemons": {}}},
    }

    enriched, extras = enrich_event_review_state(
        review_state=review_state,
        repo_root=Path("."),
        review_channel_path=Path("dev/active/review_channel.md"),
        projections_root=Path("dev/reports/review_channel/latest"),
        push_enforcement=_SNAPSHOT_PUSH_ENFORCEMENT,
    )

    push_enforcement_mock.assert_not_called()
    pe = extras["bridge_liveness"]["push_enforcement"]
    assert pe["current_branch"] == "feature/snapshot"
    assert pe["current_head_commit"] == "snap456"
    assert enriched["_compat"]["push_enforcement"]["current_branch"] == "feature/snapshot"
