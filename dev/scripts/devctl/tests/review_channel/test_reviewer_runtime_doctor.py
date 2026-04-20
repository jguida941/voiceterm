"""Focused tests for reviewer doctor publish-truth projection."""

from __future__ import annotations

from types import SimpleNamespace

from dev.scripts.devctl.commands.review_channel.reviewer_runtime_snapshot import (
    attach_reviewer_runtime_snapshot,
)
from dev.scripts.devctl.commands.review_channel.doctor_support import (
    build_doctor_report,
)
from dev.scripts.devctl.review_channel.reviewer_runtime_doctor import (
    build_reviewer_doctor_surface,
)
from dev.scripts.devctl.runtime.authority_snapshot import AuthoritySnapshot
from dev.scripts.devctl.runtime.action_contracts import ActionResult
from dev.scripts.devctl.platform.coordination_snapshot_models import (
    CoordinationSnapshot,
)
from dev.scripts.devctl.runtime.remote_commit_pipeline_models import (
    RemoteCommitPipelineContract,
)
from dev.scripts.devctl.runtime.review_state_models import (
    ReviewAttentionState,
    ReviewCurrentSessionState,
)
from dev.scripts.devctl.runtime.review_state_collaboration_models import (
    CollaborationArbitrationState,
    CollaborationPeerReviewState,
    CollaborationRestartState,
    CollaborationSessionState,
)
from dev.scripts.devctl.runtime.reviewer_runtime_models import (
    ReviewerAcceptanceState,
    ReviewerLastPollState,
    ReviewerRuntimeContract,
    ReviewerRolloverState,
    ReviewerSessionOwnerState,
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


def test_build_reviewer_doctor_surface_rejects_stale_pipeline_identity() -> None:
    doctor = build_reviewer_doctor_surface(
        contract=_runtime_contract(),
        commit_pipeline=RemoteCommitPipelineContract(
            pipeline_id="pipeline-old",
            state="push_completed",
            branch="feature/governance-quality-sweep",
            remote="origin",
            commit_sha="0936a4e543f5a3c38d0e8a9348718bd50c533a05",
            push_report_path="dev/reports/push/latest.json",
            approved_target_identity="tree-receipt:old",
            worktree_identity="worktree:old",
        ),
        push_enforcement={
            "current_branch": "codex-role-portability",
            "current_head_commit": "687c04784daa99a93258a4570445b334fa4413b3",
            "default_remote": "origin",
            "latest_push_report_path": "dev/reports/push/latest.json",
            "latest_push_report_branch": "feature/governance-quality-sweep",
            "latest_push_report_remote": "origin",
            "latest_push_report_head_commit": "0936a4e543f5a3c38d0e8a9348718bd50c533a05",
            "latest_push_report_status": "blocked",
            "latest_push_report_reason": "validation_failed",
            "latest_push_report_published_remote": False,
            "latest_push_report_post_push_green": False,
            "current_worktree_identity": "worktree:new",
            "current_approved_target_identity": "tree-receipt:new",
            "latest_push_report_matches_current_approved_target": False,
            "latest_push_report_matches_current_worktree": True,
            "latest_push_report_matches_current_branch": False,
            "latest_push_report_matches_current_head": False,
        },
    )

    assert doctor["pipeline_id"] == ""
    assert doctor["pipeline_state"] == "push_blocked"
    assert doctor["commit_sha"] == ""
    assert doctor["published_remote"] is False
    assert doctor["publication_source"] == "none"
    assert doctor["push_report_path"] == "dev/reports/push/latest.json"


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
        write_monitor_snapshot_fn=None,
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
            summary="Implementer ACK (`Claude Ack` compatibility heading) is stale for the live instruction.",
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
    assert (
        report["doctor"]["root_cause"]
        == "Implementer ACK (`Claude Ack` compatibility heading) is stale for the live instruction."
    )
    assert "reset-implementer-state" in report["doctor"]["recommended_command"]


def test_attach_reviewer_runtime_snapshot_projects_authority_snapshot() -> None:
    review_state = SimpleNamespace(
        reviewer_runtime=ReviewerRuntimeContract(
            reviewer_mode="active_dual_agent",
            effective_reviewer_mode="active_dual_agent",
            reviewer_freshness="fresh",
            stale_reason="claude_ack_stale",
            implementer_ack_current=False,
            implementation_blocked=True,
            implementation_block_reason="implementer_ack_stale",
            last_poll=ReviewerLastPollState(
                last_codex_poll_utc="2026-04-13T12:00:00Z",
                last_codex_poll_age_seconds=5,
                last_reviewer_poll_utc="2026-04-13T12:00:00Z",
                last_reviewer_poll_age_seconds=5,
            ),
            rollover=ReviewerRolloverState(),
            review_acceptance=ReviewerAcceptanceState(
                current_verdict="- pending",
                open_findings="- handshake drift",
                review_accepted=False,
            ),
        ),
        commit_pipeline=RemoteCommitPipelineContract(),
        current_session=ReviewCurrentSessionState(
            current_instruction="- implement the active slice",
            current_instruction_revision="rev-123",
            implementer_status="- working",
            implementer_ack="- acknowledged",
            implementer_ack_revision="rev-122",
            implementer_ack_state="stale",
        ),
        bridge={
            "reviewer_mode": "active_dual_agent",
            "effective_reviewer_mode": "active_dual_agent",
            "codex_conductor_active": True,
            "claude_conductor_active": True,
        },
        collaboration=CollaborationSessionState(
            schema_version=1,
            contract_id="CollaborationSession",
            session_id="session-1",
            plan_id="MP-355",
            status="active",
            reviewer_mode="active_dual_agent",
            operator_mode="remote_control",
            lead_agent="codex",
            review_agent="codex",
            coding_agent="claude",
            current_slice="MP-355",
            peer_review=CollaborationPeerReviewState(
                current_instruction="- implement the active slice",
                current_instruction_revision="rev-123",
                open_findings="- handshake drift",
                implementer_status="- working",
                implementer_ack="- acknowledged",
                implementer_ack_state="stale",
            ),
            arbitration=CollaborationArbitrationState(
                status="idle",
                summary="",
            ),
            restart=CollaborationRestartState(
                status="ready",
                resumable=True,
                source="typed",
            ),
            ready_gates=(),
            role_assignments=(),
            participants=(),
            delegated_work=(),
            mutation_owner="claude",
            verification_owner="codex",
            verification_status="live",
            watcher_owner="claude",
            watcher_status="live",
        ),
        authority_snapshot=AuthoritySnapshot(
            coordination_state="handshake_stale",
            reviewer_mode="tools_only",
            current_instruction_revision="rev-123",
            implementer_ack_state="stale",
            next_command=(
                "python3 dev/scripts/devctl.py review-channel --action status "
                "--terminal none --format json"
            ),
            observed_control_topology="single_implementer_single_reviewer",
            implementation_permission="active",
            safe_to_continue=False,
        ),
        coordination=CoordinationSnapshot(
            observed_topology="single_implementer_single_reviewer",
            recommended_topology="single_implementer_single_reviewer",
            ownership_status="scope_aligned",
            safe_to_fanout=False,
            resync_required=True,
        ),
        snapshot_id="snap-1234567890ab",
        zref="zref_12345678_deadbeef",
    )
    report = {
        "bridge_liveness": {
            "reviewer_mode": "active_dual_agent",
            "effective_reviewer_mode": "active_dual_agent",
            "reviewer_freshness": "fresh",
        },
        "publisher": {"running": False},
        "reviewer_supervisor": {"running": False},
    }

    attach_reviewer_runtime_snapshot(
        report,
        review_state=review_state,
        attention={},
    )

    snapshot = report["authority_snapshot"]
    assert report["collaboration"]["mutation_owner"] == "claude"
    assert report["current_session"]["current_instruction_revision"] == "rev-123"
    assert report["coordination"]["observed_topology"] == "single_implementer_single_reviewer"
    assert snapshot["coordination_state"] == "resync_required"
    assert snapshot["current_instruction_revision"] == "rev-123"
    assert snapshot["implementer_ack_state"] == "stale"
    assert snapshot["mutation_owner"] == "claude"
    assert snapshot["verification_owner"] == "codex"
    assert snapshot["watcher_owner"] == "claude"
    assert snapshot["next_command"].startswith(
        "python3 dev/scripts/devctl.py review-channel --action status"
    )
    assert report["reviewer_mode"] == snapshot["reviewer_mode"]
    assert report["effective_reviewer_mode"] == "active_dual_agent"
    assert report["reviewer_freshness"] == "fresh"
    assert report["current_instruction_revision"] == "rev-123"
    assert report["implementer_ack_state"] == "stale"
    assert report["safe_to_fanout"] is False
    assert report["resync_required"] is True
    assert report["ownership_status"] == "scope_aligned"
    assert report["next_command"].startswith(
        "python3 dev/scripts/devctl.py review-channel --action status"
    )
    assert report["last_codex_poll"] == "2026-04-13T12:00:00Z"
    assert report["snapshot_id"] == "snap-1234567890ab"
    assert report["zref"] == "zref_12345678_deadbeef"
    assert report["observed_control_topology"] == "single_implementer_single_reviewer"
    assert report["implementation_permission"] == "active"

    doctor_report, _ = build_doctor_report(status_report=report, exit_code=1)
    assert doctor_report["authority_snapshot"]["coordination_state"] == "resync_required"


def test_build_reviewer_doctor_surface_exposes_visibility_state() -> None:
    doctor = build_reviewer_doctor_surface(
        contract=ReviewerRuntimeContract(
            reviewer_mode="active_dual_agent",
            effective_reviewer_mode="active_dual_agent",
            reviewer_freshness="fresh",
            conductor_visibility="mixed",
            session_owner=ReviewerSessionOwnerState(
                provider="codex",
                session_name="codex-conductor",
                terminal_window_id=77,
                script_path="/tmp/codex-conductor.sh",
                session_visibility="visible",
            ),
        )
    )

    assert doctor["conductor_visibility"] == "mixed"
    assert doctor["session_visibility"] == "visible"


def test_build_reviewer_doctor_surface_prefers_inactive_diagnosis_over_publish_clear() -> None:
    doctor = build_reviewer_doctor_surface(
        contract=ReviewerRuntimeContract(
            reviewer_mode="single_agent",
            effective_reviewer_mode="single_agent",
            publish_clear=True,
            stale_reason="inactive",
            review_acceptance=ReviewerAcceptanceState(
                current_verdict="- accepted",
                open_findings="- all clear",
                review_accepted=True,
            ),
        )
    )

    assert doctor["status"] == "inactive"
    assert "dual-agent heartbeat enforcement is suspended" in doctor["summary"]


def test_build_reviewer_doctor_surface_includes_runtime_counts() -> None:
    doctor = build_reviewer_doctor_surface(
        contract=_runtime_contract(),
        collaboration={
            "participants": [
                {
                    "agent_id": "codex",
                    "role": "reviewer",
                    "live": True,
                    "planned_lane_count": 8,
                    "requested_worker_budget": 0,
                },
                {
                    "agent_id": "claude",
                    "role": "implementer",
                    "live": True,
                    "planned_lane_count": 8,
                    "requested_worker_budget": 0,
                },
            ],
            "delegated_work": [
                {"receipt_id": "receipt_001", "live": False},
                {"receipt_id": "receipt_002", "live": True},
            ],
        },
        runtime_state={
            "publisher": {"running": True},
            "reviewer_supervisor": {"running": False},
        },
    )

    counts = doctor["runtime_counts"]
    assert counts["participants_total"] == 2
    assert counts["live_participants_total"] == 2
    assert counts["active_conductor_count"] == 2
    assert counts["live_participant_count"] == 2
    assert counts["delegated_receipt_total"] == 2
    assert counts["delegated_work_total"] == 2
    assert counts["running_daemon_count"] == 1


def test_build_doctor_report_hoists_push_decision_command_when_doctor_is_blank() -> None:
    report, _ = build_doctor_report(
        status_report={
            "timestamp": "2026-04-09T12:00:00Z",
            "ok": True,
            "doctor": {"recommended_command": ""},
            "attention": {"recommended_command": ""},
            "push_decision": {
                "action": "run_devctl_push",
                "next_step_command": "python3 dev/scripts/devctl.py push --execute",
            },
        },
        exit_code=0,
    )

    assert report["recommended_command"] == "python3 dev/scripts/devctl.py push --execute"
    assert report["recommended_command_source"] == "push_decision"


def test_build_doctor_report_prefers_doctor_command_over_push_decision() -> None:
    report, _ = build_doctor_report(
        status_report={
            "timestamp": "2026-04-09T12:00:00Z",
            "ok": True,
            "doctor": {
                "recommended_command": (
                    "python3 dev/scripts/devctl.py review-channel --action ensure "
                    "--terminal none --format json"
                )
            },
            "attention": {"recommended_command": ""},
            "push_decision": {
                "action": "run_devctl_push",
                "next_step_command": "python3 dev/scripts/devctl.py push --execute",
            },
        },
        exit_code=0,
    )

    assert "review-channel --action ensure" in report["recommended_command"]
    assert report["recommended_command_source"] == "doctor"
