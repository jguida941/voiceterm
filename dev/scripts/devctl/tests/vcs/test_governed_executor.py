"""Tests for the governed remote commit/push executor."""

from __future__ import annotations

import subprocess
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from dev.scripts.devctl.commands.vcs.governed_executor import (
    APPROVAL_PACKET_KIND,
    GovernedVcsExecutor,
    build_commit_action,
    build_commit_approval_request,
    build_recover_action,
    build_stage_action,
)
from dev.scripts.devctl.commands.vcs.push import build_push_action
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
    assert (repo_root / "dev/reports/review_channel/latest/commit_pipeline.json").exists()


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
    assert result.reason == "operator_approval_missing"


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
        build_post_push_commands_fn=lambda policy, quality_policy_path=None: [],
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


def _run_git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return (completed.stdout or "").strip()
