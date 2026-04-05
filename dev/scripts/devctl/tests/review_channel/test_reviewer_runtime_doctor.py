"""Focused tests for reviewer doctor publish-truth projection."""

from __future__ import annotations

from types import SimpleNamespace

from dev.scripts.devctl.commands.review_channel.reviewer_runtime_snapshot import (
    attach_reviewer_runtime_snapshot,
)
from dev.scripts.devctl.review_channel.reviewer_runtime_doctor import (
    build_reviewer_doctor_surface,
)
from dev.scripts.devctl.runtime.action_contracts import ActionResult
from dev.scripts.devctl.runtime.remote_commit_pipeline_models import (
    RemoteCommitPipelineContract,
)
from dev.scripts.devctl.runtime.review_state_models import ReviewAttentionState
from dev.scripts.devctl.runtime.reviewer_runtime_models import (
    ReviewerAcceptanceState,
    ReviewerRuntimeContract,
)


def _runtime_contract(*, publish_clear: bool = True) -> ReviewerRuntimeContract:
    return ReviewerRuntimeContract(
        reviewer_mode="single_agent",
        effective_reviewer_mode="single_agent",
        publish_clear=publish_clear,
        review_acceptance=ReviewerAcceptanceState(
            current_verdict="- accepted",
            open_findings="- none",
            review_accepted=publish_clear,
        ),
    )


def test_build_reviewer_doctor_surface_treats_partial_progress_push_as_published() -> None:
    pipeline = RemoteCommitPipelineContract(
        state="push_blocked",
        push_report_path="dev/reports/push/latest.json",
        push_result=ActionResult(
            schema_version=1,
            contract_id="ActionResult",
            action_id="vcs.push",
            ok=False,
            status="fail",
            reason="post_push_bundle_failed",
            partial_progress=True,
        ),
        blocked_reason="post_push_bundle_failed",
    )

    doctor = build_reviewer_doctor_surface(
        contract=_runtime_contract(),
        commit_pipeline=pipeline,
    )

    assert doctor["published_remote"] is True
    assert doctor["post_push_green"] is False
    assert doctor["push_report_path"] == "dev/reports/push/latest.json"
    assert doctor["publication_source"] == "commit_pipeline"
    assert "post-push follow-up is not green yet" in doctor["summary"]


def test_attach_reviewer_runtime_snapshot_recovers_publish_truth_from_push_enforcement() -> None:
    review_state = SimpleNamespace(
        reviewer_runtime=_runtime_contract(),
        commit_pipeline=RemoteCommitPipelineContract(),
    )
    report = {
        "bridge_liveness": {
            "push_enforcement": {
                "current_branch": "feature/demo",
                "current_head_commit": "abc123",
                "default_remote": "origin",
                "upstream_ref": "origin/feature/demo",
                "latest_push_report_path": "dev/reports/push/latest.json",
                "latest_push_report_branch": "feature/demo",
                "latest_push_report_remote": "origin",
                "latest_push_report_head_commit": "abc123",
                "latest_push_report_status": "published_remote",
                "latest_push_report_reason": "post_push_bundle_failed",
                "latest_push_report_published_remote": True,
                "latest_push_report_post_push_green": False,
                "current_approved_target_identity": "",
                "latest_push_report_approved_target_identity": "",
                "latest_push_report_matches_current_approved_target": True,
                "latest_push_report_matches_current_branch": True,
                "latest_push_report_matches_current_head": True,
            }
        },
        "publisher": {"running": False},
        "reviewer_supervisor": {"running": False},
    }

    attach_reviewer_runtime_snapshot(
        report,
        review_state=review_state,
        attention={},
    )

    doctor = report["doctor"]
    assert doctor["published_remote"] is True
    assert doctor["post_push_green"] is False
    assert doctor["push_report_path"] == "dev/reports/push/latest.json"
    assert doctor["publication_source"] == "latest_push_report"
    assert "post-push follow-up is not green yet" in doctor["summary"]


def test_attach_reviewer_runtime_snapshot_rejects_stale_approved_target_receipt() -> None:
    review_state = SimpleNamespace(
        reviewer_runtime=_runtime_contract(),
        commit_pipeline=RemoteCommitPipelineContract(),
    )
    report = {
        "bridge_liveness": {
            "push_enforcement": {
                "current_branch": "feature/demo",
                "current_head_commit": "abc123",
                "default_remote": "origin",
                "upstream_ref": "origin/feature/demo",
                "latest_push_report_path": "dev/reports/push/latest.json",
                "latest_push_report_branch": "feature/demo",
                "latest_push_report_remote": "origin",
                "latest_push_report_head_commit": "abc123",
                "latest_push_report_status": "published_remote",
                "latest_push_report_reason": "post_push_bundle_failed",
                "latest_push_report_published_remote": True,
                "latest_push_report_post_push_green": False,
                "current_approved_target_identity": "tree-receipt:new",
                "latest_push_report_approved_target_identity": "tree-receipt:old",
                "latest_push_report_matches_current_approved_target": False,
                "latest_push_report_matches_current_branch": True,
                "latest_push_report_matches_current_head": True,
            }
        },
        "publisher": {"running": False},
        "reviewer_supervisor": {"running": False},
    }

    attach_reviewer_runtime_snapshot(
        report,
        review_state=review_state,
        attention={},
    )

    doctor = report["doctor"]
    assert doctor["published_remote"] is False
    assert doctor["post_push_green"] is False
    assert doctor["push_report_path"] == "dev/reports/push/latest.json"
    assert doctor["publication_source"] == "none"


def test_follow_publisher_carries_operator_interaction_mode() -> None:
    """Verify the follow controller deps propagate operator mode into report frames."""
    from dev.scripts.devctl.review_channel.follow_controller import EnsureFollowDeps

    deps = EnsureFollowDeps(
        ensure_reviewer_heartbeat_fn=lambda **_kw: None,
        reviewer_state_write_to_dict_fn=lambda _sw: None,
        run_status_action_fn=lambda **_kw: ({}, 0),
        attach_reviewer_worker_fn=lambda *_a, **_kw: None,
        ensure_reviewer_supervisor_running_fn=None,
        emit_follow_ndjson_frame_fn=lambda _f, **_kw: 0,
        reset_follow_output_fn=lambda _o: None,
        build_follow_completion_report_fn=lambda **_kw: {},
        build_follow_output_error_report_fn=lambda **_kw: {},
        write_publisher_heartbeat_fn=lambda _r, _h: None,
        read_publisher_state_fn=lambda _s: {},
        utc_timestamp_fn=lambda: "2026-04-04T00:00:00Z",
        sleep_fn=lambda _s: None,
        operator_interaction_mode="remote_control",
    )
    assert deps.operator_interaction_mode == "remote_control"


def test_attach_reviewer_runtime_snapshot_prefers_review_state_attention_projection() -> None:
    review_state = SimpleNamespace(
        reviewer_runtime=_runtime_contract(publish_clear=False),
        commit_pipeline=RemoteCommitPipelineContract(),
        attention=ReviewAttentionState(
            status="implementer_state_reset_required",
            owner="reviewer",
            summary="Claude Ack is stale for the live instruction.",
            recommended_action="Reset the implementer state before resuming work.",
            recommended_command="python3 dev/scripts/devctl.py review-channel --action reset-implementer-state --terminal none --format md",
        ),
    )
    report = {
        "bridge_liveness": {"push_enforcement": {}},
        "publisher": {"running": False},
        "reviewer_supervisor": {"running": False},
        "attention": {
            "status": "healthy",
            "owner": "operator",
            "summary": "stale summary",
            "recommended_action": "old action",
            "recommended_command": "legacy command",
        },
    }

    attach_reviewer_runtime_snapshot(
        report,
        review_state=review_state,
        attention=report["attention"],
    )

    assert report["attention"]["status"] == "implementer_state_reset_required"
    assert report["doctor"]["root_cause"] == "Claude Ack is stale for the live instruction."
    assert "reset-implementer-state" in report["doctor"]["recommended_command"]
