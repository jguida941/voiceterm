"""Tests for the governed remote commit/push executor."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.commands.vcs.governed_executor import (
    APPROVAL_PACKET_KIND,
    GovernedVcsExecutor,
    build_commit_action,
    build_commit_approval_request,
    build_recover_action,
    build_stage_action,
)
from dev.scripts.devctl.commands.vcs.governed_executor_commit_runtime import (
    attention_revision_stale,
    post_commit_execution_handoff,
    resolve_commit_execution_target as _resolve_commit_execution_target,
)
from dev.scripts.devctl.commands.vcs.governed_executor_phases import (
    _attention_revision_block,
)
from dev.scripts.devctl.commands.vcs.push import build_push_action
from dev.scripts.devctl.review_channel.event_reducer import load_or_refresh_event_bundle
from dev.scripts.devctl.governance.push_policy import (
    PushBypassPolicy,
    PushCheckpointPolicy,
    PushPolicy,
    PushPostPushPolicy,
    PushPreflightPolicy,
    PushPublicationPolicy,
)
from dev.scripts.devctl.review_channel.events import (
    post_packet,
    resolve_artifact_paths,
    transition_packet,
)
from dev.scripts.devctl.review_channel.packet_contract import (
    PacketPostRequest,
    PacketRuntimeApprovalFields,
    PacketTargetFields,
    PacketTransitionRequest,
)
from dev.scripts.devctl.runtime.action_contracts import (
    ACTION_RESULT_CONTRACT_ID,
    ACTION_RESULT_SCHEMA_VERSION,
    ActionOutcome,
)
from dev.scripts.devctl.runtime import ActionResult
from dev.scripts.devctl.runtime.remote_commit_pipeline_models import (
    RemoteCommitPipelineContract,
)
from dev.scripts.devctl.tests.vcs._git_helpers import _run_git
from dev.scripts.devctl.tests.test_review_channel_context_refs import (
    _review_channel_text,
)


def test_stage_action_persists_staged_snapshot_hash(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    executor = _executor(repo_root)

    result = executor.execute(
        build_stage_action(
            repo_pack_id="test-pack",
            paths=("tracked.txt",),
            commit_message_draft="feat: update tracked file",
            push_requested=True,
            guard_profile="bundle.tooling",
            work_intake_ref="MP-377",
        )
    )

    pipeline = executor.load_pipeline()
    assert result.ok is True
    assert result.status == ActionOutcome.PASS
    assert pipeline.state == "staged"
    assert pipeline.intent.staged_tree_hash
    assert pipeline.intent.staged_paths == ("tracked.txt",)
    assert pipeline.intent.validation_plan is not None
    assert pipeline.intent.validation_plan.bundle_id == "bundle.tooling"
    assert pipeline.intent.validation_plan.staged_tree_hash == pipeline.intent.staged_tree_hash
    assert (repo_root / "dev/reports/review_channel/latest/commit_pipeline.json").exists()


def test_stage_replaces_cross_branch_active_pipeline(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    executor = _executor(repo_root)
    executor._persist_pipeline(
        RemoteCommitPipelineContract(
            pipeline_id="pipeline-old",
            state="push_pending",
            branch="feature/other",
            commit_sha="old-sha",
        )
    )

    result = executor.execute(
        build_stage_action(
            repo_pack_id="test-pack",
            paths=("tracked.txt",),
            commit_message_draft="feat: replace stale cross-branch pipeline",
            push_requested=True,
            guard_profile="bundle.tooling",
            work_intake_ref="MP-377",
        )
    )

    pipeline = executor.load_pipeline()
    assert result.ok is True
    assert pipeline.state == "staged"
    assert pipeline.pipeline_id != "pipeline-old"
    assert pipeline.branch != "feature/other"


def test_stage_replaces_stale_same_branch_pipeline_with_old_commit_sha(
    tmp_path: Path,
) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    executor = _executor(repo_root)
    executor._persist_pipeline(
        RemoteCommitPipelineContract(
            pipeline_id="pipeline-old",
            state="push_pending",
            branch=_run_git(repo_root, "rev-parse", "--abbrev-ref", "HEAD"),
            commit_sha="old-sha",
        )
    )

    result = executor.execute(
        build_stage_action(
            repo_pack_id="test-pack",
            paths=("tracked.txt",),
            commit_message_draft="feat: replace stale same-branch pipeline",
            push_requested=True,
            guard_profile="bundle.tooling",
            work_intake_ref="MP-377",
        )
    )

    pipeline = executor.load_pipeline()
    assert result.ok is True
    assert pipeline.state == "staged"
    assert pipeline.pipeline_id != "pipeline-old"
    assert pipeline.commit_sha == ""


def test_stage_surfaces_write_tree_error_when_git_index_is_blocked(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    executor = _executor(repo_root)

    with patch(
        "dev.scripts.devctl.commands.vcs.governed_executor_phases.index_tree_hash_result",
        return_value=(
            "",
            "fatal: Unable to create '/tmp/repo/.git/index.lock': Operation not permitted",
        ),
    ):
        result = executor.execute(
            build_stage_action(
                repo_pack_id="test-pack",
                paths=("tracked.txt",),
                commit_message_draft="feat: update tracked file",
                push_requested=True,
                guard_profile="bundle.tooling",
                work_intake_ref="MP-377",
            )
        )

    assert result.ok is False
    assert result.reason == "git_index_write_blocked"
    assert ".git/index.lock" in result.operator_guidance
    assert result.warnings == (
        "fatal: Unable to create '/tmp/repo/.git/index.lock': Operation not permitted",
    )


def test_stage_surfaces_git_add_sandbox_block_as_index_write_blocked(
    tmp_path: Path,
) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    executor = _executor(repo_root)

    with patch(
        "dev.scripts.devctl.commands.vcs.governed_executor_phases.run_git_capture",
        return_value=(
            128,
            "",
            "fatal: Unable to create '/tmp/repo/.git/index.lock': Operation not permitted",
        ),
    ):
        result = executor.execute(
            build_stage_action(
                repo_pack_id="test-pack",
                paths=("tracked.txt",),
                commit_message_draft="feat: update tracked file",
                push_requested=True,
                guard_profile="bundle.tooling",
                work_intake_ref="MP-377",
            )
        )

    assert result.ok is False
    assert result.reason == "git_index_write_blocked"
    assert ".git/index.lock" in result.operator_guidance
    assert result.warnings == (
        "fatal: Unable to create '/tmp/repo/.git/index.lock': Operation not permitted",
    )


def test_stage_reuse_staged_index_fails_if_snapshot_refresh_drops_user_paths(
    tmp_path: Path,
) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    executor = _executor(repo_root)

    with (
        patch(
            "dev.scripts.devctl.commands.vcs.governed_executor_phases.refresh_snapshot_staging",
            return_value=(
                [],
                ["dev/audits/REVIEW_SNAPSHOT.md"],
                ["tracked.txt", "extra.py"],
            ),
        ),
    ):
        result = executor.execute(
            build_stage_action(
                repo_pack_id="test-pack",
                commit_message_draft="feat: preserve staged index",
                push_requested=False,
                guard_profile="bundle.tooling",
                work_intake_ref="MP-377",
                reuse_staged_index=True,
            )
        )

    assert result.ok is False
    assert result.reason == "staged_index_preservation_failed"
    assert "tracked.txt" in result.warnings
    assert "extra.py" in result.warnings


def test_commit_requires_applied_operator_approval(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    executor = _executor(repo_root)

    executor.execute(
        build_stage_action(
            repo_pack_id="test-pack",
            paths=("tracked.txt",),
            commit_message_draft="feat: update tracked file",
            push_requested=True,
            guard_profile="bundle.tooling",
            work_intake_ref="MP-377",
        )
    )
    executor.record_guard_result(_passing_guard_result())
    pipeline = executor.load_pipeline()

    result = executor.execute(
        build_commit_action(
            repo_pack_id="test-pack",
            pipeline_id=pipeline.pipeline_id,
        )
    )

    assert result.ok is False
    assert result.reason == "pending_reviewer_packets"
    assert "typed review state could not be loaded" in result.operator_guidance


def test_commit_attention_revision_ignores_expired_unresolved_only() -> None:
    review_state = SimpleNamespace(
        packet_inbox=SimpleNamespace(
            attention_revision="live-rev",
            agents=(
                SimpleNamespace(
                    agent="codex",
                    attention_status="review_needed",
                    wake_reason="expired_unresolved_packet",
                    pending_actionable_packet_ids=(),
                ),
            ),
        )
    )

    with (
        patch(
            "dev.scripts.devctl.commands.vcs.governed_executor_commit_runtime.load_live_review_state",
            return_value=review_state,
        ),
        patch(
            "dev.scripts.devctl.commands.vcs.governed_executor_commit_runtime.resolve_commit_execution_target",
            return_value="codex",
        ),
        patch(
            "dev.scripts.devctl.commands.vcs.governed_executor_commit_runtime.load_startup_receipt",
            return_value=SimpleNamespace(attention_revision="receipt-rev"),
        ),
    ):
        assert (
            attention_revision_stale(
                repo_root=Path("."),
                review_channel_path=Path("dev/active/review_channel.md"),
            )
            is False
        )


def test_commit_attention_revision_blocks_on_live_finding_attention() -> None:
    review_state = SimpleNamespace(
        packet_inbox=SimpleNamespace(
            attention_revision="live-rev",
            agents=(
                SimpleNamespace(
                    agent="codex",
                    attention_status="review_needed",
                    wake_reason="finding_pending",
                    pending_actionable_packet_ids=(),
                ),
            ),
        )
    )

    with (
        patch(
            "dev.scripts.devctl.commands.vcs.governed_executor_commit_runtime.load_live_review_state",
            return_value=review_state,
        ),
        patch(
            "dev.scripts.devctl.commands.vcs.governed_executor_commit_runtime.resolve_commit_execution_target",
            return_value="codex",
        ),
        patch(
            "dev.scripts.devctl.commands.vcs.governed_executor_commit_runtime.load_startup_receipt",
            return_value=SimpleNamespace(attention_revision="receipt-rev"),
        ),
    ):
        assert (
            attention_revision_stale(
                repo_root=Path("."),
                review_channel_path=Path("dev/active/review_channel.md"),
            )
            is True
        )


def test_commit_attention_revision_ignores_other_agents_actionable_packets() -> None:
    review_state = SimpleNamespace(
        packet_inbox=SimpleNamespace(
            attention_revision="live-rev",
            agents=(
                SimpleNamespace(
                    agent="claude",
                    attention_status="review_needed",
                    wake_reason="finding_pending",
                    pending_actionable_packet_ids=(),
                ),
            ),
        )
    )

    with (
        patch(
            "dev.scripts.devctl.commands.vcs.governed_executor_commit_runtime.load_live_review_state",
            return_value=review_state,
        ),
        patch(
            "dev.scripts.devctl.commands.vcs.governed_executor_commit_runtime.resolve_commit_execution_target",
            return_value="codex",
        ),
        patch(
            "dev.scripts.devctl.commands.vcs.governed_executor_commit_runtime.load_startup_receipt",
            return_value=SimpleNamespace(attention_revision="receipt-rev"),
        ),
    ):
        assert (
            attention_revision_stale(
                repo_root=Path("."),
                review_channel_path=Path("dev/active/review_channel.md"),
            )
            is False
        )


def test_stage_attention_revision_ignores_expired_unresolved_only() -> None:
    action = SimpleNamespace(action_id="vcs.stage")
    startup_context = {
        "work_intake": {"coordination": {"active_implementation_owner": "codex"}},
        "packet_inbox": {
            "attention_revision": "live-rev",
            "agents": [
                {
                    "agent": "codex",
                    "attention_status": "review_needed",
                    "wake_reason": "expired_unresolved_packet",
                    "pending_actionable_total": 0,
                }
            ],
        }
    }

    with patch(
        "dev.scripts.devctl.commands.vcs.governed_executor_stage_attention.load_startup_receipt",
        return_value=SimpleNamespace(attention_revision="receipt-rev"),
    ):
        result = _attention_revision_block(
            action=action,
            repo_root=Path("."),
            startup_context=startup_context,
            result_builder=lambda **kwargs: kwargs,
        )

    assert result is None


def test_stage_attention_revision_blocks_on_live_finding_attention() -> None:
    action = SimpleNamespace(action_id="vcs.stage")
    startup_context = {
        "work_intake": {"coordination": {"active_implementation_owner": "codex"}},
        "packet_inbox": {
            "attention_revision": "live-rev",
            "agents": [
                {
                    "agent": "codex",
                    "attention_status": "review_needed",
                    "wake_reason": "finding_pending",
                    "pending_actionable_total": 0,
                }
            ],
        }
    }

    with patch(
        "dev.scripts.devctl.commands.vcs.governed_executor_stage_attention.load_startup_receipt",
        return_value=SimpleNamespace(attention_revision="receipt-rev"),
    ):
        result = _attention_revision_block(
            action=action,
            repo_root=Path("."),
            startup_context=startup_context,
            result_builder=lambda **kwargs: kwargs,
        )

    assert result is not None
    assert result["reason"] == "attention_revision_stale"


def test_stage_attention_revision_ignores_other_agents_actionable_packets() -> None:
    action = SimpleNamespace(action_id="vcs.stage")
    startup_context = {
        "work_intake": {"coordination": {"active_implementation_owner": "codex"}},
        "packet_inbox": {
            "attention_revision": "live-rev",
            "agents": [
                {
                    "agent": "claude",
                    "attention_status": "review_needed",
                    "wake_reason": "finding_pending",
                    "pending_actionable_total": 0,
                }
            ],
        },
    }

    with patch(
        "dev.scripts.devctl.commands.vcs.governed_executor_stage_attention.load_startup_receipt",
        return_value=SimpleNamespace(attention_revision="receipt-rev"),
    ):
        result = _attention_revision_block(
            action=action,
            repo_root=Path("."),
            startup_context=startup_context,
            result_builder=lambda **kwargs: kwargs,
        )

    assert result is None


def test_commit_posts_runtime_action_request_when_git_index_write_is_blocked(
    tmp_path: Path,
) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    executor = _executor(repo_root)

    executor.execute(
        build_stage_action(
            repo_pack_id="test-pack",
            paths=("tracked.txt",),
            commit_message_draft="feat: governed remote pipeline",
            push_requested=True,
            guard_profile="bundle.tooling",
            work_intake_ref="MP-377",
        )
    )
    executor.record_guard_result(_passing_guard_result())
    pipeline = executor.load_pipeline()
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    _approve_pipeline(repo_root=repo_root, pipeline=pipeline)

    live_writable_lane = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="active_dual_agent",
            coding_agent="claude",
            review_agent="codex",
            role_assignments=(),
        ),
        bridge=SimpleNamespace(
            implementer_capability=SimpleNamespace(
                provider="claude",
                may_edit_repo=True,
            ),
            reviewer_capability=SimpleNamespace(
                provider="codex",
                may_edit_repo=False,
            ),
            effective_reviewer_mode="active_dual_agent",
            reviewer_mode="active_dual_agent",
        ),
    )

    with patch(
        "dev.scripts.devctl.commands.vcs.governed_executor_commit_phase.run_git_capture",
        return_value=(
            128,
            "",
            "fatal: Unable to create '/tmp/repo/.git/index.lock': Operation not permitted",
        ),
    ), patch(
        "dev.scripts.devctl.commands.vcs.governed_executor_commit_phase.runtime_load_live_review_state",
        return_value=live_writable_lane,
    ):
        result = executor.execute(
            build_commit_action(repo_pack_id="test-pack", pipeline_id=pipeline.pipeline_id)
        )

    bundle = load_or_refresh_event_bundle(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
    )
    action_requests = [
        packet
        for packet in bundle.review_state["packets"]
        if packet.get("kind") == "action_request"
        and packet.get("requested_action") == "commit"
    ]
    current_pipeline = executor.load_pipeline()

    assert result.ok is False
    assert result.reason == "git_index_write_blocked"
    assert current_pipeline.blocked_reason == "git_index_write_blocked"
    assert current_pipeline.commit_result is not None
    assert current_pipeline.commit_result.reason == "git_index_write_blocked"
    assert len(action_requests) == 1
    assert action_requests[0]["to_agent"] == "claude"
    assert action_requests[0]["target_kind"] == "runtime"
    assert action_requests[0]["target_ref"] == f"remote_commit_pipeline:{pipeline.pipeline_id}"
    assert action_requests[0]["pipeline_generation"] == pipeline.generation_id
    assert action_requests[0]["staged_snapshot_hash"] == pipeline.intent.staged_tree_hash
    assert action_requests[0]["approval_required"] is False
    assert any(
        warning.startswith("commit_execution_request_packet=rev_pkt_")
        for warning in result.warnings
    )


def test_commit_execution_target_falls_back_to_writable_reviewer_lane() -> None:
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="single_agent",
            coding_agent="claude",
            review_agent="codex",
            role_assignments=(),
        ),
        bridge=SimpleNamespace(
            implementer_capability=SimpleNamespace(
                provider="claude",
                may_edit_repo=False,
            ),
            reviewer_capability=SimpleNamespace(
                provider="codex",
                may_edit_repo=True,
            ),
            effective_reviewer_mode="single_agent",
            reviewer_mode="single_agent",
        ),
    )

    assert _resolve_commit_execution_target(review_state) == "codex"


def test_commit_execution_target_prefers_effective_mode_when_declared_mode_is_stale(
) -> None:
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="active_dual_agent",
            coding_agent="claude",
            review_agent="codex",
            role_assignments=(),
        ),
        bridge=SimpleNamespace(
            implementer_capability=None,
            reviewer_capability=None,
            effective_reviewer_mode="single_agent",
            reviewer_mode="active_dual_agent",
        ),
    )

    assert _resolve_commit_execution_target(review_state) == "codex"


def test_commit_execution_target_fails_closed_without_writable_lane() -> None:
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="active_dual_agent",
            coding_agent="claude",
            review_agent="codex",
            role_assignments=(),
        ),
        bridge=SimpleNamespace(
            implementer_capability=SimpleNamespace(
                provider="claude",
                may_edit_repo=False,
            ),
            reviewer_capability=SimpleNamespace(
                provider="codex",
                may_edit_repo=False,
            ),
            effective_reviewer_mode="active_dual_agent",
            reviewer_mode="active_dual_agent",
        ),
    )

    assert _resolve_commit_execution_target(review_state) == ""


def test_commit_execution_target_routes_remote_control_publication_to_implementer() -> None:
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="active_dual_agent",
            coding_agent="claude",
            review_agent="codex",
            role_assignments=(),
            topology_mode="single_implementer_single_reviewer",
            restart=SimpleNamespace(source="remote_control_attachment"),
            participants=(
                SimpleNamespace(
                    provider="codex",
                    agent_id="codex",
                    role="reviewer",
                    live=True,
                    capture_mode="local-reviewer",
                ),
                SimpleNamespace(
                    provider="claude",
                    agent_id="claude",
                    role="implementer",
                    live=True,
                    capture_mode="remote-control",
                ),
            ),
        ),
        bridge=SimpleNamespace(
            implementer_capability=SimpleNamespace(
                provider="claude",
                may_edit_repo=False,
            ),
            reviewer_capability=SimpleNamespace(
                provider="codex",
                may_edit_repo=False,
            ),
            effective_reviewer_mode="tools_only",
            reviewer_mode="active_dual_agent",
        ),
        reviewer_runtime=SimpleNamespace(
            remote_control_attachment=SimpleNamespace(
                provider="claude",
                status="attached",
            )
        ),
    )

    assert _resolve_commit_execution_target(review_state) == "claude"


def test_commit_execution_target_fails_closed_when_provider_is_live_as_operator_only(
) -> None:
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="active_dual_agent",
            coding_agent="claude",
            review_agent="codex",
            role_assignments=(
                SimpleNamespace(role_id="coding_agent", provider="claude", live=True),
                SimpleNamespace(role_id="review_agent", provider="codex", live=True),
                SimpleNamespace(role_id="operator_agent", provider="claude", live=True),
            ),
            topology_mode="single_implementer_single_reviewer",
            restart=SimpleNamespace(source="remote_control_attachment"),
            participants=(
                SimpleNamespace(
                    provider="claude",
                    agent_id="claude",
                    role="operator",
                    live=True,
                    capture_mode="remote-control",
                ),
                SimpleNamespace(
                    provider="codex",
                    agent_id="codex",
                    role="reviewer",
                    live=True,
                    capture_mode="local-reviewer",
                ),
            ),
        ),
        bridge=SimpleNamespace(
            implementer_capability=SimpleNamespace(
                provider="claude",
                may_edit_repo=True,
            ),
            reviewer_capability=SimpleNamespace(
                provider="codex",
                may_edit_repo=False,
            ),
            effective_reviewer_mode="active_dual_agent",
            reviewer_mode="active_dual_agent",
        ),
        reviewer_runtime=SimpleNamespace(
            remote_control_attachment=SimpleNamespace(
                provider="claude",
                status="attached",
            )
        ),
    )

    assert _resolve_commit_execution_target(review_state) == ""


def test_post_commit_execution_handoff_fails_closed_without_live_writable_target(
) -> None:
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="active_dual_agent",
            coding_agent="claude",
            review_agent="codex",
            role_assignments=(
                SimpleNamespace(role_id="coding_agent", provider="claude", live=True),
                SimpleNamespace(role_id="review_agent", provider="codex", live=True),
            ),
            participants=(
                SimpleNamespace(provider="claude", role="operator", live=True),
                SimpleNamespace(provider="codex", role="reviewer", live=True),
            ),
        ),
        bridge=SimpleNamespace(
            implementer_capability=SimpleNamespace(
                provider="claude",
                may_edit_repo=True,
            ),
            reviewer_capability=SimpleNamespace(
                provider="codex",
                may_edit_repo=False,
            ),
            effective_reviewer_mode="active_dual_agent",
            reviewer_mode="active_dual_agent",
        ),
    )

    with patch(
        "dev.scripts.devctl.commands.vcs.governed_executor_commit_runtime.load_live_review_state",
        return_value=review_state,
    ):
        target_agent, packet_id, error = post_commit_execution_handoff(
            pipeline=RemoteCommitPipelineContract(pipeline_id="pipeline-123"),
            repo_root=Path("."),
            review_channel_path=Path("dev/active/review_channel.md"),
        )

    assert target_agent == ""
    assert packet_id == ""
    assert error == "commit_execution_target_unavailable"


def test_recover_clear_resets_blocked_pipeline(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    executor = _executor(repo_root)

    executor.execute(
        build_stage_action(
            repo_pack_id="test-pack",
            paths=("tracked.txt",),
            commit_message_draft="feat: update tracked file",
            push_requested=True,
            guard_profile="bundle.tooling",
            work_intake_ref="MP-377",
        )
    )
    executor.record_guard_result(
        ActionResult(
            schema_version=ACTION_RESULT_SCHEMA_VERSION,
            contract_id=ACTION_RESULT_CONTRACT_ID,
            action_id="quality.guard_bundle",
            ok=False,
            status=ActionOutcome.FAIL,
            reason="bundle_failed",
        )
    )

    result = executor.execute(
        build_recover_action(repo_pack_id="test-pack", strategy="clear")
    )

    pipeline = executor.load_pipeline()
    assert result.ok is True
    assert pipeline.pipeline_id == ""
    assert pipeline.state == "push_blocked"
    assert pipeline.blocked_reason == "pipeline_unavailable"


def test_full_pipeline_commits_and_pushes_to_local_remote(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    remote_root = tmp_path / "remote.git"
    _run_git(remote_root.parent, "init", "--bare", str(remote_root))
    _run_git(repo_root, "remote", "add", "origin", str(remote_root))
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    executor = _executor(repo_root)

    stage_result = executor.execute(
        build_stage_action(
            repo_pack_id="test-pack",
            paths=("tracked.txt",),
            commit_message_draft="feat: governed remote pipeline",
            push_requested=True,
            guard_profile="bundle.tooling",
            work_intake_ref="MP-377",
        )
    )
    assert stage_result.ok is True

    executor.record_guard_result(_passing_guard_result())
    pipeline = executor.load_pipeline()
    assert pipeline.validation_receipt is not None
    assert pipeline.validation_receipt.plan_id == pipeline.intent.validation_plan.plan_id
    assert pipeline.validation_receipt.checkpoint_sufficient is True
    assert pipeline.validation_receipt.push_sufficient is True
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)

    post_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=build_commit_approval_request(pipeline),
    )
    _, decision_event = post_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=PacketPostRequest(
            from_agent="operator",
            to_agent="system",
            kind=APPROVAL_PACKET_KIND,
            summary="Approve governed commit pipeline",
            body="Operator approved the guarded staged snapshot.",
            requested_action="approve_commit_pipeline",
            policy_hint="operator_approval_required",
            approval_required=False,
            trace_id=pipeline.pipeline_id,
            target=PacketTargetFields.from_values(
                target_kind="runtime",
                target_ref=f"remote_commit_pipeline:{pipeline.pipeline_id}",
                target_revision=pipeline.generation_id,
            ),
            runtime_approval=PacketRuntimeApprovalFields.from_values(
                pipeline_generation=pipeline.generation_id,
                staged_snapshot_hash=pipeline.intent.staged_tree_hash,
                guard_results_summary='{"action_id": "quality.guard_bundle", "reason": "", "status": "pass"}',
            ),
        ),
    )
    transition_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=PacketTransitionRequest(
            action="apply",
            packet_id=str(decision_event["packet_id"]),
            actor="operator",
        ),
    )

    commit_result = executor.execute(
        build_commit_action(
            repo_pack_id="test-pack",
            pipeline_id=pipeline.pipeline_id,
        )
    )
    assert commit_result.ok is True

    committed_pipeline = executor.load_pipeline()
    assert committed_pipeline.push_authorization is not None
    assert committed_pipeline.push_authorization.authorized_head_sha == committed_pipeline.commit_sha
    assert committed_pipeline.push_authorization.approval_mode == "commit_pipeline_approval"
    push_result = executor.execute(
        build_push_action(
            repo_pack_id="test-pack",
            branch="feature/pipeline-e2e",
            remote="origin",
            execute=True,
            skip_preflight=True,
            skip_post_push=False,
            requested_by="remote_commit_pipeline",
        )
    )

    pushed_pipeline = executor.load_pipeline()
    assert push_result.ok is True
    assert pushed_pipeline.state == "push_completed"
    assert pushed_pipeline.commit_sha == committed_pipeline.commit_sha
    remote_head = _run_git(remote_root, "rev-parse", "refs/heads/feature/pipeline-e2e")
    assert remote_head == pushed_pipeline.commit_sha


def test_push_override_reissues_publication_authorization_through_pipeline(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    remote_root = tmp_path / "remote.git"
    _run_git(remote_root.parent, "init", "--bare", str(remote_root))
    _run_git(repo_root, "remote", "add", "origin", str(remote_root))
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    executor = _executor(repo_root)

    executor.execute(
        build_stage_action(
            repo_pack_id="test-pack",
            paths=("tracked.txt",),
            commit_message_draft="feat: override push auth",
            push_requested=True,
            guard_profile="bundle.tooling",
            work_intake_ref="MP-377",
        )
    )
    executor.record_guard_result(_passing_guard_result())
    pipeline = executor.load_pipeline()
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    post_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=build_commit_approval_request(pipeline),
    )
    _, decision_event = post_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=PacketPostRequest(
            from_agent="operator",
            to_agent="system",
            kind=APPROVAL_PACKET_KIND,
            summary="Approve governed commit pipeline",
            body="Operator approved the guarded staged snapshot.",
            requested_action="approve_commit_pipeline",
            policy_hint="operator_approval_required",
            approval_required=False,
            trace_id=pipeline.pipeline_id,
            target=PacketTargetFields.from_values(
                target_kind="runtime",
                target_ref=f"remote_commit_pipeline:{pipeline.pipeline_id}",
                target_revision=pipeline.generation_id,
            ),
            runtime_approval=PacketRuntimeApprovalFields.from_values(
                pipeline_generation=pipeline.generation_id,
                staged_snapshot_hash=pipeline.intent.staged_tree_hash,
                guard_results_summary='{"action_id": "quality.guard_bundle", "reason": "", "status": "pass"}',
            ),
        ),
    )
    transition_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=PacketTransitionRequest(
            action="apply",
            packet_id=str(decision_event["packet_id"]),
            actor="operator",
        ),
    )

    commit_result = executor.execute(
        build_commit_action(repo_pack_id="test-pack", pipeline_id=pipeline.pipeline_id)
    )
    assert commit_result.ok is True

    committed_pipeline = executor.load_pipeline()
    expired_auth = replace(
        committed_pipeline.push_authorization,
        expires_at_utc="2026-04-01T00:00:00Z",
    )
    executor._persist_pipeline(
        replace(
            committed_pipeline,
            state="push_blocked",
            blocked_reason="push_authorization_expired",
            push_authorization=expired_auth,
        )
    )
    _, override_event = post_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=PacketPostRequest(
            from_agent="operator",
            to_agent="system",
            kind=APPROVAL_PACKET_KIND,
            summary="Override push authorization",
            body="Operator approved publication of the exact already-reviewed commit.",
            requested_action="override_push",
            policy_hint="operator_approval_required",
            approval_required=False,
            trace_id=committed_pipeline.pipeline_id,
            target=PacketTargetFields.from_values(
                target_kind="runtime",
                target_ref=f"remote_commit_pipeline:{committed_pipeline.pipeline_id}",
                target_revision=committed_pipeline.approved_target_identity,
            ),
            runtime_approval=PacketRuntimeApprovalFields.from_values(
                pipeline_generation=committed_pipeline.generation_id,
                staged_snapshot_hash=committed_pipeline.intent.staged_tree_hash,
                guard_results_summary='{"action_id": "quality.guard_bundle", "reason": "", "status": "pass"}',
            ),
        ),
    )
    transition_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=PacketTransitionRequest(
            action="apply",
            packet_id=str(override_event["packet_id"]),
            actor="operator",
        ),
    )

    push_result = executor.execute(
        build_push_action(
            repo_pack_id="test-pack",
            branch="feature/pipeline-e2e",
            remote="origin",
            execute=True,
            skip_preflight=True,
            skip_post_push=False,
            requested_by="remote_commit_pipeline",
        )
    )

    pushed_pipeline = executor.load_pipeline()
    assert push_result.ok is True
    assert pushed_pipeline.push_authorization is not None
    assert pushed_pipeline.push_authorization.approval_mode == "override_push"
    assert pushed_pipeline.push_authorization.review_verdict == "override_push_approved"
    assert (
        pushed_pipeline.push_authorization.decision_packet_id
        == str(override_event["packet_id"])
    )


def test_commit_does_not_reread_startup_publish_gate_after_approval(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    startup_calls = 0

    def startup_context_once(*, repo_root: Path) -> SimpleNamespace:
        nonlocal startup_calls
        del repo_root
        startup_calls += 1
        if startup_calls > 1:
            raise AssertionError(
                "`vcs.commit` should use pipeline proof, not live startup context."
            )
        return _startup_context(repo_root=Path("."))

    executor = _executor(repo_root, startup_context_fn=startup_context_once)

    executor.execute(
        build_stage_action(
            repo_pack_id="test-pack",
            paths=("tracked.txt",),
            commit_message_draft="feat: pipeline proof owns commit",
            push_requested=True,
            guard_profile="bundle.tooling",
            work_intake_ref="MP-377",
        )
    )
    executor.record_guard_result(_passing_guard_result())
    pipeline = executor.load_pipeline()
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    post_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=build_commit_approval_request(pipeline),
    )
    _, decision_event = post_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=PacketPostRequest(
            from_agent="operator",
            to_agent="system",
            kind=APPROVAL_PACKET_KIND,
            summary="Approve governed commit pipeline",
            body="Operator approved the guarded staged snapshot.",
            requested_action="approve_commit_pipeline",
            policy_hint="operator_approval_required",
            approval_required=False,
            trace_id=pipeline.pipeline_id,
            target=PacketTargetFields.from_values(
                target_kind="runtime",
                target_ref=f"remote_commit_pipeline:{pipeline.pipeline_id}",
                target_revision=pipeline.generation_id,
            ),
            runtime_approval=PacketRuntimeApprovalFields.from_values(
                pipeline_generation=pipeline.generation_id,
                staged_snapshot_hash=pipeline.intent.staged_tree_hash,
                guard_results_summary='{"action_id": "quality.guard_bundle", "reason": "", "status": "pass"}',
            ),
        ),
    )
    transition_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=PacketTransitionRequest(
            action="apply",
            packet_id=str(decision_event["packet_id"]),
            actor="operator",
        ),
    )

    commit_result = executor.execute(
        build_commit_action(repo_pack_id="test-pack", pipeline_id=pipeline.pipeline_id)
    )

    committed_pipeline = executor.load_pipeline()
    assert commit_result.ok is True
    assert committed_pipeline.state == "commit_recorded"
    assert committed_pipeline.push_authorization is not None
    assert startup_calls == 1


def test_commit_does_not_refresh_review_projections_after_approval(
    tmp_path: Path,
) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    executor = _executor(repo_root)

    executor.execute(
        build_stage_action(
            repo_pack_id="test-pack",
            paths=("tracked.txt",),
            commit_message_draft="feat: commit without projection drift",
            push_requested=True,
            guard_profile="bundle.tooling",
            work_intake_ref="MP-377",
        )
    )
    executor.record_guard_result(_passing_guard_result())
    pipeline = executor.load_pipeline()
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    post_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=build_commit_approval_request(pipeline),
    )
    _, decision_event = post_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=PacketPostRequest(
            from_agent="operator",
            to_agent="system",
            kind=APPROVAL_PACKET_KIND,
            summary="Approve governed commit pipeline",
            body="Operator approved the guarded staged snapshot.",
            requested_action="approve_commit_pipeline",
            policy_hint="operator_approval_required",
            approval_required=False,
            trace_id=pipeline.pipeline_id,
            target=PacketTargetFields.from_values(
                target_kind="runtime",
                target_ref=f"remote_commit_pipeline:{pipeline.pipeline_id}",
                target_revision=pipeline.generation_id,
            ),
            runtime_approval=PacketRuntimeApprovalFields.from_values(
                pipeline_generation=pipeline.generation_id,
                staged_snapshot_hash=pipeline.intent.staged_tree_hash,
                guard_results_summary='{"action_id": "quality.guard_bundle", "reason": "", "status": "pass"}',
            ),
        ),
    )
    transition_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=PacketTransitionRequest(
            action="apply",
            packet_id=str(decision_event["packet_id"]),
            actor="operator",
        ),
    )

    with patch(
        "dev.scripts.devctl.commands.vcs.governed_executor_sync.refresh_review_projections",
        side_effect=AssertionError(
            "`vcs.commit` must not refresh review projections after approval."
        ),
    ):
        commit_result = executor.execute(
            build_commit_action(repo_pack_id="test-pack", pipeline_id=pipeline.pipeline_id)
        )

    committed_pipeline = executor.load_pipeline()
    assert commit_result.ok is True
    assert committed_pipeline.state == "commit_recorded"
    assert committed_pipeline.push_authorization is not None


def test_commit_marks_git_invocation_as_governed(tmp_path: Path) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    executor = _executor(repo_root)

    stage_result = executor.execute(
        build_stage_action(
            repo_pack_id="test-pack",
            paths=("tracked.txt",),
            commit_message_draft="feat: governed marker",
            push_requested=True,
            guard_profile="bundle.tooling",
            work_intake_ref="MP-377",
        )
    )
    assert stage_result.ok is True

    executor.record_guard_result(_passing_guard_result())
    pipeline = executor.load_pipeline()
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    post_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=build_commit_approval_request(pipeline),
    )
    _, decision_event = post_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=PacketPostRequest(
            from_agent="operator",
            to_agent="system",
            kind=APPROVAL_PACKET_KIND,
            summary="Approve governed commit pipeline",
            body="Operator approved the guarded staged snapshot.",
            requested_action="approve_commit_pipeline",
            policy_hint="operator_approval_required",
            approval_required=False,
            trace_id=pipeline.pipeline_id,
            target=PacketTargetFields.from_values(
                target_kind="runtime",
                target_ref=f"remote_commit_pipeline:{pipeline.pipeline_id}",
                target_revision=pipeline.generation_id,
            ),
            runtime_approval=PacketRuntimeApprovalFields.from_values(
                pipeline_generation=pipeline.generation_id,
                staged_snapshot_hash=pipeline.intent.staged_tree_hash,
                guard_results_summary='{"action_id": "quality.guard_bundle", "reason": "", "status": "pass"}',
            ),
        ),
    )
    transition_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=PacketTransitionRequest(
            action="apply",
            packet_id=str(decision_event["packet_id"]),
            actor="operator",
        ),
    )

    original_run_git_capture = __import__(
        "dev.scripts.devctl.commands.vcs.governed_executor_commit_phase",
        fromlist=["run_git_capture"],
    ).run_git_capture
    captured_calls: list[tuple[tuple[str, ...], dict[str, str] | None]] = []

    def _capture_commit_args(args, *, repo_root: Path, extra_env=None):
        captured_calls.append((tuple(args), extra_env))
        return original_run_git_capture(args, repo_root=repo_root, extra_env=extra_env)

    with patch(
        "dev.scripts.devctl.commands.vcs.governed_executor_commit_phase.run_git_capture",
        side_effect=_capture_commit_args,
    ):
        commit_result = executor.execute(
            build_commit_action(repo_pack_id="test-pack", pipeline_id=pipeline.pipeline_id)
        )

    assert commit_result.ok is True
    assert any(
        args[:3] == ("-c", "devctl.governed-commit=true", "commit")
        and "--no-verify" in args
        and extra_env == {"DEVCTL_GOVERNED_COMMIT": "1"}
        for args, extra_env in captured_calls
    )


def _executor(
    repo_root: Path,
    *,
    startup_context_fn=None,
) -> GovernedVcsExecutor:
    if startup_context_fn is None:
        startup_context_fn = _startup_context
    return GovernedVcsExecutor(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        startup_context_fn=startup_context_fn,
        push_policy=_push_policy(),
        build_post_push_commands_fn=lambda policy, quality_policy_path=None, since_ref=None: [],
        refresh_projections=True,
    )


def _init_repo(repo_root: Path) -> Path:
    repo_root.mkdir(parents=True, exist_ok=True)
    _run_git(repo_root, "init")
    _run_git(repo_root, "config", "user.name", "VoiceTerm Tests")
    _run_git(repo_root, "config", "user.email", "tests@example.com")
    _run_git(repo_root, "checkout", "-b", "feature/pipeline-e2e")
    (repo_root / ".gitignore").write_text("dev/reports/\n", encoding="utf-8")
    review_channel_path = repo_root / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
    (repo_root / "tracked.txt").write_text("initial\n", encoding="utf-8")
    _run_git(repo_root, "add", ".")
    _run_git(repo_root, "commit", "-m", "initial")
    return repo_root


def _push_policy() -> PushPolicy:
    return PushPolicy(
        policy_path="dev/config/devctl_repo_policy.json",
        repo_pack_id="test-pack",
        warnings=(),
        default_remote="origin",
        development_branch="develop",
        release_branch="master",
        protected_branches=("develop", "master"),
        allowed_branch_prefixes=("feature/",),
        preflight=PushPreflightPolicy(),
        post_push=PushPostPushPolicy(bundle="bundle.post-push"),
        bypass=PushBypassPolicy(allow_skip_preflight=True),
        checkpoint=PushCheckpointPolicy(
            compatibility_projection_paths=(
                "dev/reports/push/latest.json",
            )
        ),
        publication=PushPublicationPolicy(),
    )


def _startup_context(*, repo_root: Path) -> SimpleNamespace:
    del repo_root
    return SimpleNamespace(
        reviewer_gate=SimpleNamespace(
            implementation_blocked=False,
            implementation_block_reason="",
            review_gate_allows_push=True,
            reviewer_mode="single_agent",
            effective_reviewer_mode="single_agent",
        ),
        push_decision=SimpleNamespace(
            action="run_devctl_push",
            reason="push_preconditions_satisfied",
            next_step_summary="Use the governed push path now.",
            next_step_command="python3 dev/scripts/devctl.py push --execute",
        ),
        advisory_action="checkpoint_allowed",
        advisory_reason="worktree_dirty_within_budget",
    )


def _passing_guard_result() -> ActionResult:
    return ActionResult(
        schema_version=ACTION_RESULT_SCHEMA_VERSION,
        contract_id=ACTION_RESULT_CONTRACT_ID,
        action_id="quality.guard_bundle",
        ok=True,
        status=ActionOutcome.PASS,
        reason="",
    )


def _approve_pipeline(
    *,
    repo_root: Path,
    pipeline,
) -> None:
    artifact_paths = resolve_artifact_paths(repo_root=repo_root)
    post_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=build_commit_approval_request(pipeline),
    )
    _, decision_event = post_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=PacketPostRequest(
            from_agent="operator",
            to_agent="system",
            kind=APPROVAL_PACKET_KIND,
            summary="Approve governed commit pipeline",
            body="Operator approved the guarded staged snapshot.",
            requested_action="approve_commit_pipeline",
            policy_hint="operator_approval_required",
            approval_required=False,
            trace_id=pipeline.pipeline_id,
            target=PacketTargetFields.from_values(
                target_kind="runtime",
                target_ref=f"remote_commit_pipeline:{pipeline.pipeline_id}",
                target_revision=pipeline.generation_id,
            ),
            runtime_approval=PacketRuntimeApprovalFields.from_values(
                pipeline_generation=pipeline.generation_id,
                staged_snapshot_hash=pipeline.intent.staged_tree_hash,
                guard_results_summary='{"action_id": "quality.guard_bundle", "reason": "", "status": "pass"}',
            ),
        ),
    )
    transition_packet(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        artifact_paths=artifact_paths,
        request=PacketTransitionRequest(
            action="apply",
            packet_id=str(decision_event["packet_id"]),
            actor="operator",
        ),
    )
