"""Focused tests for event-backed push-state parity."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.review_channel.event_projection import (
    EventProjectionContext,
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
    participants: tuple[object, ...] = ()


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
    "dev.scripts.devctl.review_channel.event_projection.build_typed_bridge_liveness",
    side_effect=lambda **kwargs: {
        **kwargs["bridge_liveness"],
        "reviewer_mode": "active_dual_agent",
        "effective_reviewer_mode": "tools_only",
    },
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
    "dev.scripts.devctl.review_channel.event_projection_assembly.build_surface_snapshot_id",
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
    return_value=_DummyCollaboration(
        participants=(
            SimpleNamespace(
                provider="claude",
                agent_id="claude",
                role="implementer",
                live=True,
            ),
        ),
    ),
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_event_current_session",
    return_value=_current_session(),
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.attach_conductor_session_state",
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
    _attach_conductor_session_state_mock,
    _current_session_mock,
    _collaboration_mock,
    _reviewer_runtime_mock,
    _pipeline_mock,
    _snapshot_id_mock,
    _bridge_state_mock,
    _service_identity_mock,
    _attach_auth_policy_mock,
    _typed_bridge_liveness_mock,
    _attach_auth_policy_state_mock,
    _service_identity_state_mock,
) -> None:
    review_state = {
        "timestamp": "2026-04-04T00:00:00Z",
        "review": {"plan_id": "MP-377", "session_id": "sess-1"},
        "queue": {},
        "_compat": {"runtime": {"daemons": {}}},
    }

    with patch(
        "dev.scripts.devctl.review_channel.event_projection_assembly._load_bridge_inputs",
        return_value=("", None),
    ):
        enriched, extras = enrich_event_review_state(
            review_state=review_state,
            context=EventProjectionContext(
                repo_root=Path("."),
                review_channel_path=Path("dev/active/review_channel.md"),
                projections_root=Path("dev/reports/review_channel/latest"),
            ),
        )

    assert extras["bridge_liveness"]["push_enforcement"]["latest_push_report_path"]
    assert enriched["_compat"]["push_enforcement"]["latest_push_report_path"]
    assert enriched["_compat"]["push_decision"]["action"] == "no_push_needed"
    assert enriched["_compat"]["doctor"]["publication_source"] == "latest_push_report"
    assert enriched["_compat"]["doctor"]["published_remote"] is True
    assert (
        enriched["_compat"]["bridge_projection"]["metadata"]["snapshot_id"]
        == enriched["snapshot_id"]
    )
    assert (
        enriched["attention"]["status"]
        == enriched["recovery_assessment"]["diagnosis"]["status"]
    )
    assert (
        enriched["attention"]["owner"]
        == enriched["recovery_assessment"]["decision"]["execution_owner"]
    )
    assert (
        enriched["attention"]["recommended_command"]
        == enriched["recovery_assessment"]["decision"]["command"]
    )
    runtime_inputs = _reviewer_runtime_mock.call_args.args[0]
    assert runtime_inputs.bridge_liveness["effective_reviewer_mode"] == "tools_only"


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
    "dev.scripts.devctl.review_channel.event_projection_assembly.build_surface_snapshot_id",
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
    return_value=_DummyCollaboration(
        participants=(
            SimpleNamespace(
                provider="claude",
                agent_id="claude",
                role="implementer",
                live=True,
            ),
        ),
    ),
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_event_current_session",
    return_value=_current_session(),
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.attach_conductor_session_state",
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_bridge_push_enforcement_state",
)
def test_enrich_uses_snapshot_push_enforcement_when_provided(
    push_enforcement_mock,
    _attach_conductor_session_state_mock,
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

    with patch(
        "dev.scripts.devctl.review_channel.event_projection_assembly._load_bridge_inputs",
        return_value=("", None),
    ):
        enriched, extras = enrich_event_review_state(
            review_state=review_state,
            context=EventProjectionContext(
                repo_root=Path("."),
                review_channel_path=Path("dev/active/review_channel.md"),
                projections_root=Path("dev/reports/review_channel/latest"),
                push_enforcement=_SNAPSHOT_PUSH_ENFORCEMENT,
            ),
        )

    push_enforcement_mock.assert_not_called()
    pe = extras["bridge_liveness"]["push_enforcement"]
    assert pe["current_branch"] == "feature/snapshot"
    assert pe["current_head_commit"] == "snap456"
    assert enriched["_compat"]["push_enforcement"]["current_branch"] == "feature/snapshot"


@patch(
    "dev.scripts.devctl.review_channel.event_projection.load_coordination_snapshot",
    return_value=SimpleNamespace(
        to_dict=lambda: {
            "current_slice": "Fresh coordination from loader.",
            "observed_topology": "single_agent",
            "recommended_topology": "single_agent",
            "resync_required": False,
        }
    ),
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
    return_value="snap-3",
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
    "dev.scripts.devctl.review_channel.event_projection.attach_conductor_session_state",
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_bridge_push_enforcement_state",
    return_value=_SNAPSHOT_PUSH_ENFORCEMENT,
)
def test_enrich_event_review_state_uses_shared_coordination_loader(
    _push_enforcement_mock,
    _attach_conductor_session_state_mock,
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
    coordination_loader_mock,
) -> None:
    review_state = {
        "timestamp": "2026-04-04T00:00:00Z",
        "review": {"plan_id": "MP-377", "session_id": "sess-3"},
        "queue": {},
        "_compat": {"runtime": {"daemons": {}}},
    }

    enriched, _ = enrich_event_review_state(
        review_state=review_state,
        context=EventProjectionContext(
            repo_root=Path("."),
            review_channel_path=Path("dev/active/review_channel.md"),
            projections_root=Path("dev/reports/review_channel/latest"),
        ),
    )

    coordination_loader_mock.assert_called_once()
    assert enriched["coordination"]["current_slice"] == "Fresh coordination from loader."


@patch(
    "dev.scripts.devctl.review_channel.event_projection.load_coordination_snapshot",
    return_value=None,
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
    return_value="snap-4",
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
    "dev.scripts.devctl.review_channel.event_projection.attach_conductor_session_state",
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_bridge_push_enforcement_state",
    return_value=_SNAPSHOT_PUSH_ENFORCEMENT,
)
def test_enrich_event_review_state_reads_sessions_from_latest_root(
    _push_enforcement_mock,
    attach_conductor_session_state_mock,
    _current_session_mock,
    collaboration_mock,
    reviewer_runtime_mock,
    _pipeline_mock,
    _snapshot_id_mock,
    _bridge_state_mock,
    _service_identity_mock,
    _attach_auth_policy_mock,
    _attach_auth_policy_state_mock,
    _service_identity_state_mock,
    _coordination_loader_mock,
) -> None:
    review_state = {
        "timestamp": "2026-04-04T00:00:00Z",
        "review": {"plan_id": "MP-377", "session_id": "sess-4"},
        "queue": {},
        "_compat": {"runtime": {"daemons": {}}},
    }
    projections_root = Path("dev/reports/review_channel/projections/latest")

    enrich_event_review_state(
        review_state=review_state,
        context=EventProjectionContext(
            repo_root=Path("."),
            review_channel_path=Path("dev/active/review_channel.md"),
            projections_root=projections_root,
        ),
    )

    expected_session_root = Path("dev/reports/review_channel/latest")
    assert collaboration_mock.call_args.kwargs["session_output_root"] == expected_session_root
    reviewer_inputs = reviewer_runtime_mock.call_args.args[0]
    assert reviewer_inputs.session_output_root == expected_session_root
    assert (
        attach_conductor_session_state_mock.call_args.kwargs["output_root"]
        == expected_session_root
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
    return_value="snap-5",
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
    "dev.scripts.devctl.review_channel.event_projection.build_event_bridge_liveness_projection",
    return_value={
        "overall_state": "fresh",
        "codex_poll_state": "fresh",
        "reviewer_freshness": "fresh",
        "reviewer_mode": "active_dual_agent",
        "last_codex_poll_age_seconds": 0,
        "claude_status_present": True,
        "claude_ack_present": True,
        "claude_ack_current": True,
        "reviewed_hash_current": True,
        "implementer_completion_stall": False,
        "publisher_running": True,
        "reviewer_supervisor_running": False,
        "review_needed": False,
    },
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.attach_conductor_session_state",
    side_effect=lambda **kwargs: kwargs["bridge_liveness"].update(
        {
            "active_conductor_providers": ["claude"],
            "codex_conductor_active": False,
            "claude_conductor_active": True,
            "conductor_visibility": "claude_only",
            "launch_truth": "hybrid_claude_only",
            "effective_reviewer_mode": "active_dual_agent",
        }
    ),
)
@patch(
    "dev.scripts.devctl.review_channel.event_projection.build_bridge_push_enforcement_state",
    return_value={
        "checkpoint_required": True,
        "safe_to_continue_editing": False,
        "recommended_action": "checkpoint_before_continue",
    },
)
def test_enrich_event_review_state_prioritizes_checkpoint_when_conductor_helper_marks_hybrid_claude_only(
    _push_enforcement_mock,
    _attach_conductor_session_state_mock,
    _bridge_liveness_mock,
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
        "review": {"plan_id": "MP-377", "session_id": "sess-5"},
        "queue": {},
        "_compat": {"runtime": {"daemons": {}}},
    }

    enriched, _ = enrich_event_review_state(
        review_state=review_state,
        context=EventProjectionContext(
            repo_root=Path("."),
            review_channel_path=Path("dev/active/review_channel.md"),
            projections_root=Path("dev/reports/review_channel/projections/latest"),
        ),
    )

    assert enriched["attention"]["status"] == "checkpoint_required"
    assert enriched["recovery_assessment"]["diagnosis"]["status"] == (
        "checkpoint_required"
    )
