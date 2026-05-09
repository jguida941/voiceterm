"""Tests for the governed remote commit/push executor."""

from __future__ import annotations

import json
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
    post_commit_stage_handoff,
)
from dev.scripts.devctl.commands.vcs.governed_executor_commit_runtime import (
    resolve_commit_execution_target as _resolve_commit_execution_target,
)
from dev.scripts.devctl.commands.vcs.governed_executor_commit_runtime import (
    resolve_commit_stage_target as _resolve_commit_stage_target,
)
from dev.scripts.devctl.commands.vcs.governed_executor_packets import (
    CommitStageRequestFields,
    build_commit_stage_request,
)
from dev.scripts.devctl.commands.vcs.governed_executor_phases import (
    _attention_revision_block,
)
from dev.scripts.devctl.commands.vcs.governed_executor_commit_runtime import (
    StartupContextRefreshResult,
    refresh_and_recheck_attention_revision,
    refresh_startup_context_receipt_before_vcs_preflight,
)
from dev.scripts.devctl.commands.vcs.push import build_push_action
from dev.scripts.devctl.review_channel.event_reducer import load_or_refresh_event_bundle
from dev.scripts.devctl.review_channel.event_store import load_events
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
    validate_post_request,
)
from dev.scripts.devctl.review_channel.packet_attestation import (
    PacketGuardAttestation,
)
from dev.scripts.devctl.runtime import ActionResult
from dev.scripts.devctl.runtime.action_contracts import (
    ACTION_RESULT_CONTRACT_ID,
    ACTION_RESULT_SCHEMA_VERSION,
    ActionOutcome,
)
from dev.scripts.devctl.runtime.remote_commit_pipeline_models import (
    RemoteCommitPipelineContract,
)
from dev.scripts.devctl.runtime.review_state_models import (
    ActorAuthorityState,
    CapabilityGrantState,
)
from dev.scripts.devctl.tests.test_review_channel_context_refs import (
    _review_channel_text,
)
from dev.scripts.devctl.tests.vcs._git_helpers import _run_git
from dev.scripts.devctl.tests.vcs._push_policy_helpers import build_test_push_policy


def _actor_authority(
    actor_id: str,
    *,
    role: str = "implementer",
    live: bool = True,
    capabilities: tuple[str, ...] = ("repo.commit",),
    denied_capabilities: tuple[str, ...] = (),
) -> ActorAuthorityState:
    return ActorAuthorityState(
        actor_id=actor_id,
        provider=actor_id,
        role=role,
        live=live,
        status="live" if live else "stale",
        source="test",
        grants=tuple(
            CapabilityGrantState(
                capability=capability,
                granted=True,
                source="test",
            )
            for capability in capabilities
        )
        + tuple(
            CapabilityGrantState(
                capability=capability,
                granted=False,
                source="test",
            )
            for capability in denied_capabilities
        ),
    )


def _remote_control_attachment(
    provider: str,
    *,
    role: str = "operator",
) -> SimpleNamespace:
    """Return a fresh identity-bound remote-control attachment fixture."""
    return SimpleNamespace(
        provider=provider,
        role=role,
        status="attached",
        remote_session_id=f"remote-session-{provider}",
        last_seen_utc="2999-01-01T00:00:00Z",
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
    assert (
        pipeline.intent.validation_plan.staged_tree_hash
        == pipeline.intent.staged_tree_hash
    )
    assert (
        repo_root / "dev/reports/review_channel/latest/commit_pipeline.json"
    ).exists()


def test_commit_stage_request_allows_pre_pipeline_runtime_target() -> None:
    request = build_commit_stage_request(
        CommitStageRequestFields(
            to_agent="claude",
            head_sha="abc123",
            commit_message_draft="feat: checkpoint",
            stage_reason="git_index_write_blocked",
            stage_warnings=("index.lock denied",),
        )
    )

    validate_post_request(request)

    assert request.kind == "action_request"
    assert request.requested_action == "stage_commit_pipeline"
    assert request.to_agent == "claude"
    assert request.target.target_kind == "runtime"
    assert request.target.target_ref == "devctl_commit:abc123"
    assert request.target.target_revision == "abc123"
    assert request.guard_bundle_evidence.full_guard_bundle_evidence == "--profile ci"


def test_commit_stage_handoff_reuses_existing_pending_packet(
    tmp_path: Path,
) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    head_sha = _run_git(repo_root, "rev-parse", "HEAD")
    existing_packet = SimpleNamespace(
        packet_id="rev_pkt_existing_stage",
        kind="action_request",
        from_agent="system",
        to_agent="claude",
        requested_action="stage_commit_pipeline",
        policy_hint="safe_auto_apply",
        target_ref=f"devctl_commit:{head_sha}",
        target_revision=head_sha,
        status="acked",
        applied_at_utc="",
        acked_at_utc="2026-04-28T11:59:59Z",
        posted_at="2026-04-28T11:59:58Z",
        latest_event_id="evt_000002",
    )

    with (
        patch(
            "dev.scripts.devctl.commands.vcs.governed_executor_commit_runtime.load_live_review_state",
            return_value=SimpleNamespace(packets=(existing_packet,)),
        ),
        patch(
            "dev.scripts.devctl.commands.vcs.governed_executor_commit_runtime.resolve_commit_stage_target",
            return_value="claude",
        ),
        patch(
            "dev.scripts.devctl.commands.vcs.governed_executor_commit_runtime.post_packet",
        ) as post_packet_mock,
    ):
        target_agent, packet_id, error = post_commit_stage_handoff(
            repo_root=repo_root,
            review_channel_path=repo_root / "dev/active/review_channel.md",
            commit_message_draft="feat: dashboard unification",
            stage_reason="git_index_write_blocked",
        )

    assert target_agent == "claude"
    assert packet_id == "rev_pkt_existing_stage"
    assert error == ""
    post_packet_mock.assert_not_called()


def test_commit_stage_handoff_does_not_reuse_applied_packet(
    tmp_path: Path,
) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    head_sha = _run_git(repo_root, "rev-parse", "HEAD")
    existing_packet = SimpleNamespace(
        packet_id="rev_pkt_applied_stage",
        kind="action_request",
        from_agent="system",
        to_agent="claude",
        requested_action="stage_commit_pipeline",
        policy_hint="safe_auto_apply",
        target_ref=f"devctl_commit:{head_sha}",
        target_revision=head_sha,
        status="applied",
        applied_at_utc="2026-04-28T12:00:00Z",
        acked_at_utc="2026-04-28T11:59:59Z",
        posted_at="2026-04-28T11:59:58Z",
        latest_event_id="evt_000002",
    )

    with (
        patch(
            "dev.scripts.devctl.commands.vcs.governed_executor_commit_runtime.load_live_review_state",
            return_value=SimpleNamespace(packets=(existing_packet,)),
        ),
        patch(
            "dev.scripts.devctl.commands.vcs.governed_executor_commit_runtime.resolve_commit_stage_target",
            return_value="claude",
        ),
        patch(
            "dev.scripts.devctl.commands.vcs.governed_executor_commit_runtime.post_packet",
            return_value=(None, {"packet_id": "rev_pkt_new_stage"}),
        ) as post_packet_mock,
    ):
        target_agent, packet_id, error = post_commit_stage_handoff(
            repo_root=repo_root,
            review_channel_path=repo_root / "dev/active/review_channel.md",
            commit_message_draft="feat: dashboard unification",
            stage_reason="git_index_write_blocked",
        )

    assert target_agent == "claude"
    assert packet_id == "rev_pkt_new_stage"
    assert error == ""
    post_packet_mock.assert_called_once()


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


def test_commit_approval_request_without_guard_result_has_typed_summary(
    tmp_path: Path,
) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    executor = _executor(repo_root)

    result = executor.execute(
        build_stage_action(
            repo_pack_id="test-pack",
            paths=("tracked.txt",),
            commit_message_draft="feat: approve staged pipeline",
            push_requested=True,
            guard_profile="bundle.tooling",
            work_intake_ref="MP-377",
        )
    )

    assert result.ok is True
    request = build_commit_approval_request(executor.load_pipeline())
    summary = json.loads(request.runtime_approval.guard_results_summary)
    assert summary == {
        "action_id": "quality.guard_bundle",
        "reason": "guard_result_missing",
        "status": "not_recorded",
    }
    validate_post_request(request)


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


def test_stage_surfaces_write_tree_error_when_git_index_is_blocked(
    tmp_path: Path,
) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    executor = _executor(repo_root)

    with patch(
        "dev.scripts.devctl.commands.vcs.governed_executor_stage_index.index_tree_hash_result",
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
    assert result.reason_chain == (
        "staged_tree_hash_unavailable",
        "git_index_write_blocked",
        "sandbox_index_lock_denied",
    )
    assert result.remediation == "stage_commit_pipeline"
    assert result.auto_executable is False
    assert result.retryable is True
    assert result.errors[0]["reason"] == "git_index_write_blocked"
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
        "dev.scripts.devctl.commands.vcs.governed_executor_stage_index.run_git_capture",
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
    assert result.reason_chain == (
        "git_add_failed",
        "git_index_write_blocked",
        "sandbox_index_lock_denied",
    )
    assert result.remediation == "stage_commit_pipeline"
    assert result.auto_executable is False
    assert result.retryable is True
    assert result.errors[0]["reason"] == "git_index_write_blocked"
    assert result.warnings == (
        "fatal: Unable to create '/tmp/repo/.git/index.lock': Operation not permitted",
    )


def test_stage_auto_includes_startup_managed_projection_drift(
    tmp_path: Path,
) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    (repo_root / "bridge.md").write_text("initial bridge\n", encoding="utf-8")
    _run_git(repo_root, "add", "bridge.md")
    _run_git(repo_root, "commit", "-m", "add bridge projection")
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    (repo_root / "bridge.md").write_text("updated bridge\n", encoding="utf-8")

    def startup_context_fn(*, repo_root: Path) -> SimpleNamespace:
        del repo_root
        base = _startup_context(repo_root=Path("/unused"))
        return SimpleNamespace(
            **base.__dict__,
            governance=SimpleNamespace(
                push_enforcement=SimpleNamespace(
                    managed_projection_dirty_paths=("bridge.md",)
                )
            ),
        )

    executor = _executor(repo_root, startup_context_fn=startup_context_fn)

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
    assert "tracked.txt" in pipeline.intent.staged_paths
    assert "bridge.md" in pipeline.intent.staged_paths
    assert any(
        warning == "managed_projection_paths_auto_included=bridge.md"
        for warning in result.warnings
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

    assert result is not None
    assert result["reason"] == "attention_revision_stale"


def test_stage_attention_revision_auto_refreshes_receipt_before_block(
    tmp_path: Path,
) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    receipt_revision = {"value": "receipt-rev"}
    executor = _executor(
        repo_root,
        startup_context_fn=lambda *, repo_root: _startup_context_with_attention(
            attention_revision="live-rev",
            owner="codex",
            agent="codex",
            wake_reason="finding_pending",
        ),
    )

    def _refresh_startup_receipt(**_kwargs):
        receipt_revision["value"] = "live-rev"
        return StartupContextRefreshResult(ok=True, warnings=("refreshed",))

    with (
        patch(
            "dev.scripts.devctl.commands.vcs.governed_executor_stage_attention.load_startup_receipt",
            side_effect=lambda **_kwargs: SimpleNamespace(
                attention_revision=receipt_revision["value"]
            ),
        ),
        patch(
            "dev.scripts.devctl.commands.vcs.governed_executor_stage_attention."
            "refresh_startup_context_receipt_before_vcs_preflight",
            side_effect=_refresh_startup_receipt,
        ) as refresh_mock,
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

    assert result.ok is True
    assert result.reason == "pipeline_staged"
    refresh_mock.assert_called_once()


def test_stage_attention_revision_blocks_when_startup_refresh_fails(
    tmp_path: Path,
) -> None:
    repo_root = _init_repo(tmp_path / "repo")
    (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
    executor = _executor(
        repo_root,
        startup_context_fn=lambda *, repo_root: _startup_context_with_attention(
            attention_revision="live-rev",
            owner="codex",
            agent="codex",
            wake_reason="finding_pending",
        ),
    )

    with (
        patch(
            "dev.scripts.devctl.commands.vcs.governed_executor_stage_attention.load_startup_receipt",
            return_value=SimpleNamespace(attention_revision="receipt-rev"),
        ),
        patch(
            "dev.scripts.devctl.commands.vcs.governed_executor_stage_attention."
            "refresh_startup_context_receipt_before_vcs_preflight",
            return_value=StartupContextRefreshResult(
                ok=False,
                warnings=("startup-context refresh failed",),
            ),
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
    assert result.reason == "startup_context_refresh_failed"
    assert result.warnings == ("startup-context refresh failed",)


def test_commit_attention_refresh_accepts_checkpoint_advisory_exit_one(
    tmp_path: Path,
) -> None:
    repo_root = _repo_with_devctl(tmp_path)
    output = "\n".join(
        (
            "action=checkpoint_before_continue",
            "reason=staged_index_budget_exceeded",
            "interaction_mode=remote_control",
            "observed_control_topology=no_live_agents",
            "implementation_permission=blocked",
            "attention_revision=live-rev",
        )
    )

    result = refresh_startup_context_receipt_before_vcs_preflight(
        repo_root=repo_root,
        next_step_label="commit preflight",
        command_runner=_startup_context_runner(
            returncode=1,
            failure_output=output,
        ),
    )

    assert result.ok is True
    assert result.advisory_action == "checkpoint_before_continue"
    assert result.advisory_reason == "staged_index_budget_exceeded"


def test_commit_attention_refresh_accepts_resume_advisory_exit_one(
    tmp_path: Path,
) -> None:
    repo_root = _repo_with_devctl(tmp_path)
    decision = refresh_and_recheck_attention_revision(
        repo_root=repo_root,
        review_channel_path=None,
        held_lease="",
        next_step_label="commit preflight",
        command_runner=_startup_context_runner(
            returncode=1,
            failure_output=_startup_context_json(
                "resume_implementer_work",
                "implementer_completion_stall",
            ),
        ),
        stale_check_fn=lambda **_kwargs: False,
    )

    assert decision.status == "fresh"
    assert "action=resume_implementer_work" in decision.warnings[0]


def test_commit_attention_refresh_blocks_unparseable_exit_one(
    tmp_path: Path,
) -> None:
    repo_root = _repo_with_devctl(tmp_path)
    decision = refresh_and_recheck_attention_revision(
        repo_root=repo_root,
        review_channel_path=None,
        held_lease="",
        next_step_label="commit preflight",
        command_runner=_startup_context_runner(
            returncode=1,
            failure_output="Traceback: startup-context crashed",
        ),
        stale_check_fn=lambda **_kwargs: False,
    )

    assert decision.status == "refresh_failed"
    assert "startup-context refresh failed before commit preflight" in (
        decision.warnings[0]
    )


def test_commit_attention_refresh_exit_zero_proceeds_without_payload(
    tmp_path: Path,
) -> None:
    repo_root = _repo_with_devctl(tmp_path)
    decision = refresh_and_recheck_attention_revision(
        repo_root=repo_root,
        review_channel_path=None,
        held_lease="",
        next_step_label="commit preflight",
        command_runner=_startup_context_runner(returncode=0),
        stale_check_fn=lambda **_kwargs: False,
    )

    assert decision.status == "fresh"
    assert decision.warnings == (
        "Refreshed startup-context receipt before commit preflight.",
    )


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
            role_assignments=(
                SimpleNamespace(
                    role_id="coding_agent",
                    provider="claude",
                    agent_id="claude",
                    live=True,
                ),
            ),
            participants=(
                SimpleNamespace(
                    provider="claude",
                    agent_id="claude",
                    role="implementer",
                    live=True,
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
    ), patch(
        "dev.scripts.devctl.commands.vcs.governed_executor_commit_runtime.load_live_review_state",
        return_value=live_writable_lane,
    ):
        result = executor.execute(
            build_commit_action(
                repo_pack_id="test-pack", pipeline_id=pipeline.pipeline_id
            )
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
    assert (
        action_requests[0]["target_ref"]
        == f"remote_commit_pipeline:{pipeline.pipeline_id}"
    )
    assert action_requests[0]["pipeline_generation"] == pipeline.generation_id
    assert (
        action_requests[0]["staged_snapshot_hash"] == pipeline.intent.staged_tree_hash
    )
    assert action_requests[0]["approval_required"] is False
    assert any(
        warning.startswith("commit_execution_request_packet=rev_pkt_")
        for warning in result.warnings
    )


def test_commit_auto_executable_failure_routes_through_failure_packet_router(
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

    def _routable_failure_kwargs(*, error: str, reason: str, default_reason: str):
        return {
            "errors": (
                {
                    "reason": reason,
                    "message": error,
                    "remediation": "stage_commit_pipeline",
                    "auto_executable": True,
                },
            ),
            "reason_chain": (default_reason, reason),
            "remediation": "stage_commit_pipeline",
            "auto_executable": True,
        }

    with patch(
        "dev.scripts.devctl.commands.vcs.governed_executor_commit_phase.run_git_capture",
        return_value=(1, "", "fatal: simulated auto-remediable commit failure"),
    ), patch(
        "dev.scripts.devctl.commands.vcs.governed_executor_commit_phase._git_index_result_kwargs",
        side_effect=_routable_failure_kwargs,
    ):
        result = executor.execute(
            build_commit_action(
                repo_pack_id="test-pack", pipeline_id=pipeline.pipeline_id
            )
        )

    events = load_events(Path(artifact_paths.event_log_path))
    routed = [
        event
        for event in events
        if event.get("source") == "failure_packet_router"
        or event.get("packet_id", "").startswith("auto_pkt:")
    ]

    assert result.ok is False
    assert result.reason == "commit_failed"
    assert result.remediation == "stage_commit_pipeline"
    assert result.auto_executable is True
    assert [event["event_type"] for event in routed] == [
        "packet_posted",
        "packet_acked",
        "packet_applied",
    ]
    assert routed[0]["requested_action"] == "stage_commit_pipeline"
    assert any(
        warning.startswith("failure_packet_router_packet=auto_pkt:")
        for warning in result.warnings
    )


def test_commit_execution_target_falls_back_to_writable_reviewer_lane() -> None:
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="single_agent",
            coding_agent="claude",
            review_agent="codex",
            role_assignments=(
                SimpleNamespace(
                    role_id="review_agent",
                    provider="codex",
                    agent_id="codex",
                    live=True,
                ),
            ),
            participants=(
                SimpleNamespace(
                    provider="codex",
                    agent_id="codex",
                    role="reviewer",
                    live=True,
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
                may_edit_repo=True,
            ),
            effective_reviewer_mode="single_agent",
            reviewer_mode="single_agent",
        ),
    )

    assert _resolve_commit_execution_target(review_state) == "codex"


def test_commit_execution_target_uses_live_actor_authority_mutation_owner_grant() -> (
    None
):
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="tools_only",
            coding_agent="claude",
            review_agent="codex",
            mutation_owner="claude",
            actor_authorities=(
                _actor_authority("claude", capabilities=("repo.commit",)),
            ),
            role_assignments=(
                SimpleNamespace(
                    role_id="coding_agent",
                    provider="claude",
                    agent_id="claude",
                    live=True,
                ),
            ),
            participants=(
                SimpleNamespace(
                    provider="claude",
                    agent_id="claude",
                    role="implementer",
                    live=True,
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
            reviewer_mode="tools_only",
        ),
    )

    assert _resolve_commit_execution_target(review_state) == "claude"


def test_commit_execution_target_ignores_denied_actor_authority_and_falls_back() -> (
    None
):
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="active_dual_agent",
            coding_agent="claude",
            review_agent="codex",
            mutation_owner="claude",
            actor_authorities=(
                _actor_authority(
                    "claude",
                    capabilities=(),
                    denied_capabilities=("repo.commit",),
                ),
            ),
            role_assignments=(
                SimpleNamespace(
                    role_id="coding_agent",
                    provider="claude",
                    agent_id="claude",
                    live=True,
                ),
            ),
            participants=(
                SimpleNamespace(
                    provider="claude",
                    agent_id="claude",
                    role="implementer",
                    live=True,
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
    )

    assert _resolve_commit_execution_target(review_state) == "claude"


def test_commit_execution_target_does_not_treat_approval_grant_as_mutation() -> None:
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="active_dual_agent",
            coding_agent="claude",
            review_agent="codex",
            mutation_owner="claude",
            actor_authorities=(
                _actor_authority(
                    "claude",
                    role="operator",
                    capabilities=("approval.commit",),
                ),
            ),
            role_assignments=(
                SimpleNamespace(
                    role_id="operator_agent",
                    provider="claude",
                    agent_id="claude",
                    live=True,
                ),
            ),
            participants=(
                SimpleNamespace(
                    provider="claude",
                    agent_id="claude",
                    role="operator",
                    live=True,
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
            effective_reviewer_mode="active_dual_agent",
            reviewer_mode="active_dual_agent",
        ),
    )

    assert _resolve_commit_execution_target(review_state) == ""


def test_commit_execution_target_prefers_effective_mode_when_declared_mode_is_stale() -> (
    None
):
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="active_dual_agent",
            coding_agent="claude",
            review_agent="codex",
            role_assignments=(
                SimpleNamespace(
                    role_id="review_agent",
                    provider="codex",
                    agent_id="codex",
                    live=True,
                ),
            ),
            participants=(
                SimpleNamespace(
                    provider="codex",
                    agent_id="codex",
                    role="reviewer",
                    live=True,
                ),
            ),
        ),
        bridge=SimpleNamespace(
            implementer_capability=None,
            reviewer_capability=None,
            effective_reviewer_mode="single_agent",
            reviewer_mode="active_dual_agent",
        ),
    )

    assert _resolve_commit_execution_target(review_state) == "codex"


def test_commit_execution_target_role_flipped_codex_as_coder_claude_as_reviewer() -> (
    None
):
    """Resolver must follow typed roles, not provider names.

    Operator architectural rule: either AI can play either typed role.
    The resolver reads `collaboration.coding_agent` /
    `collaboration.review_agent` from typed state, so flipping the
    pairing — codex as the implementer, claude as the reviewer — must
    resolve to ``codex`` (the live writable implementer), not ``claude``
    (the historic implementer name).
    """
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="active_dual_agent",
            coding_agent="codex",
            review_agent="claude",
            role_assignments=(
                SimpleNamespace(
                    role_id="coding_agent",
                    provider="codex",
                    agent_id="codex",
                    live=True,
                ),
                SimpleNamespace(
                    role_id="review_agent",
                    provider="claude",
                    agent_id="claude",
                    live=True,
                ),
            ),
            participants=(
                SimpleNamespace(
                    provider="codex",
                    agent_id="codex",
                    role="implementer",
                    live=True,
                ),
                SimpleNamespace(
                    provider="claude",
                    agent_id="claude",
                    role="reviewer",
                    live=True,
                ),
            ),
        ),
        bridge=SimpleNamespace(
            implementer_capability=SimpleNamespace(
                provider="codex",
                may_edit_repo=True,
            ),
            reviewer_capability=SimpleNamespace(
                provider="claude",
                may_edit_repo=False,
            ),
            effective_reviewer_mode="active_dual_agent",
            reviewer_mode="active_dual_agent",
        ),
    )

    assert _resolve_commit_execution_target(review_state) == "codex"


def test_commit_execution_target_admits_third_party_provider_as_coder() -> None:
    """Arbitrary provider ids (gemini, future agents) must work in any role.

    Operator architectural rule: the typed state admits any provider via
    ``packet_agents.py``; the resolver must follow whatever
    ``collaboration.coding_agent`` names, even when the provider is not
    one of the historic codex/claude/cursor triple.
    """
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="active_dual_agent",
            coding_agent="gemini",
            review_agent="codex",
            role_assignments=(
                SimpleNamespace(
                    role_id="coding_agent",
                    provider="gemini",
                    agent_id="gemini",
                    live=True,
                ),
                SimpleNamespace(
                    role_id="review_agent",
                    provider="codex",
                    agent_id="codex",
                    live=True,
                ),
            ),
            participants=(
                SimpleNamespace(
                    provider="gemini",
                    agent_id="gemini",
                    role="implementer",
                    live=True,
                ),
                SimpleNamespace(
                    provider="codex",
                    agent_id="codex",
                    role="reviewer",
                    live=True,
                ),
            ),
        ),
        bridge=SimpleNamespace(
            implementer_capability=SimpleNamespace(
                provider="gemini",
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

    assert _resolve_commit_execution_target(review_state) == "gemini"


def test_commit_execution_target_picks_by_typed_role_not_participant_order() -> None:
    """N participants: pick by typed role, not by name order in the list.

    Operator architectural rule: identity is bound to the typed role,
    not to the order in which participants happen to appear. Listing a
    reviewer first must not cause the resolver to mistake it for the
    coder.
    """
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="active_dual_agent",
            coding_agent="claude",
            review_agent="codex",
            role_assignments=(
                SimpleNamespace(
                    role_id="review_agent",
                    provider="codex",
                    agent_id="codex",
                    live=True,
                ),
                SimpleNamespace(
                    role_id="coding_agent",
                    provider="claude",
                    agent_id="claude",
                    live=True,
                ),
                SimpleNamespace(
                    role_id="coding_agent",
                    provider="gemini",
                    agent_id="gemini",
                    live=False,
                ),
            ),
            participants=(
                SimpleNamespace(
                    provider="codex",
                    agent_id="codex",
                    role="reviewer",
                    live=True,
                ),
                SimpleNamespace(
                    provider="claude",
                    agent_id="claude",
                    role="implementer",
                    live=True,
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
    )

    assert _resolve_commit_execution_target(review_state) == "claude"


def test_commit_execution_target_fails_closed_without_live_role_evidence() -> None:
    """Capability alone is not proof of liveness — codex finding rev_pkt_1780.

    When ``_provider_has_live_role`` cannot find any live participant or
    live role-assignment evidence for the candidate provider, returning
    True would let the executor route a `commit` action_request to a
    queue no live conductor owns. Fail-closed at the resolver instead so
    the caller can defer or escalate to the operator.
    """
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="single_agent",
            coding_agent="claude",
            review_agent="codex",
            role_assignments=(),
            participants=(),
        ),
        bridge=SimpleNamespace(
            implementer_capability=SimpleNamespace(
                provider="claude",
                may_edit_repo=True,
            ),
            reviewer_capability=SimpleNamespace(
                provider="codex",
                may_edit_repo=True,
            ),
            effective_reviewer_mode="single_agent",
            reviewer_mode="single_agent",
        ),
    )

    assert _resolve_commit_execution_target(review_state) == ""


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


def test_commit_execution_target_routes_remote_control_publication_to_implementer() -> (
    None
):
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
            remote_control_attachment=_remote_control_attachment("claude")
        ),
    )

    assert _resolve_commit_execution_target(review_state) == "claude"


def test_commit_execution_target_fails_closed_when_provider_is_live_as_operator_only() -> (
    None
):
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
            remote_control_attachment=_remote_control_attachment("claude")
        ),
    )

    assert _resolve_commit_execution_target(review_state) == ""


def test_commit_stage_target_routes_remote_operator_attachment() -> None:
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="single_agent",
            coding_agent="",
            review_agent="",
            role_assignments=(
                SimpleNamespace(role_id="operator_agent", provider="claude", live=True),
            ),
            topology_mode="single_agent",
            participants=(
                SimpleNamespace(
                    provider="claude",
                    agent_id="claude",
                    role="operator",
                    live=True,
                    capture_mode="remote-control",
                ),
            ),
        ),
        bridge=SimpleNamespace(
            implementer_capability=SimpleNamespace(
                provider="",
                may_edit_repo=False,
            ),
            reviewer_capability=SimpleNamespace(
                provider="",
                may_edit_repo=False,
            ),
            effective_reviewer_mode="single_agent",
            reviewer_mode="single_agent",
        ),
        reviewer_runtime=SimpleNamespace(
            remote_control_attachment=_remote_control_attachment("claude")
        ),
    )

    assert _resolve_commit_execution_target(review_state) == ""
    assert _resolve_commit_stage_target(review_state) == "claude"


def test_commit_stage_target_prefers_remote_attachment_over_local_executor() -> None:
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="single_agent",
            coding_agent="codex",
            review_agent="codex",
            role_assignments=(
                SimpleNamespace(role_id="review_agent", provider="codex", live=True),
                SimpleNamespace(role_id="operator_agent", provider="claude", live=True),
            ),
            topology_mode="single_agent",
            participants=(
                SimpleNamespace(
                    provider="codex",
                    agent_id="codex",
                    role="reviewer",
                    live=True,
                    capture_mode="terminal-script",
                ),
                SimpleNamespace(
                    provider="claude",
                    agent_id="claude",
                    role="operator",
                    live=True,
                    capture_mode="remote-control",
                ),
            ),
        ),
        bridge=SimpleNamespace(
            implementer_capability=SimpleNamespace(
                provider="codex",
                may_edit_repo=True,
            ),
            reviewer_capability=SimpleNamespace(
                provider="codex",
                may_edit_repo=True,
            ),
            effective_reviewer_mode="single_agent",
            reviewer_mode="single_agent",
        ),
        reviewer_runtime=SimpleNamespace(
            remote_control_attachment=_remote_control_attachment("claude")
        ),
    )

    assert _resolve_commit_execution_target(review_state) == "codex"
    assert _resolve_commit_stage_target(review_state) == "claude"


def test_commit_stage_target_prefers_implementer_when_reviewer_is_attached() -> None:
    """When the remote-control attachment provider is the reviewer-bound
    agent and a separate implementer is bound, route the pre-pipeline
    stage handoff to the implementer. Otherwise the handoff recirculates
    back to the blocked reviewer queue (observed as
    `resolve_commit_stage_target(...) == "codex"` when the attachment is
    `provider="codex", role="operator"` while claude holds the coder role).
    """
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="active_dual_agent",
            coding_agent="claude",
            review_agent="codex",
            role_assignments=(
                SimpleNamespace(role_id="coding_agent", provider="claude", live=True),
                SimpleNamespace(role_id="review_agent", provider="codex", live=True),
            ),
            topology_mode="active_dual_agent",
            participants=(
                SimpleNamespace(
                    provider="claude",
                    agent_id="claude",
                    role="implementer",
                    live=True,
                    capture_mode="terminal-script",
                ),
                SimpleNamespace(
                    provider="codex",
                    agent_id="codex",
                    role="reviewer",
                    live=True,
                    capture_mode="remote-control",
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
            remote_control_attachment=_remote_control_attachment("codex")
        ),
    )

    assert _resolve_commit_stage_target(review_state) == "claude"


def test_commit_stage_target_reroutes_reviewer_role_attachment() -> None:
    """Reroute must fire regardless of attachment.role label.

    The live remote-control session uses ``role="reviewer"`` for the codex
    attachment (not ``operator``). The deeper invariant — provider is the
    reviewer-bound agent + coding_agent is a different live writable lane
    — should trigger the reroute under any role label, not only
    ``role="operator"``. Repro at rev_pkt_1768.
    """
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="active_dual_agent",
            coding_agent="claude",
            review_agent="codex",
            role_assignments=(
                SimpleNamespace(role_id="coding_agent", provider="claude", live=True),
                SimpleNamespace(role_id="review_agent", provider="codex", live=True),
            ),
            topology_mode="active_dual_agent",
            participants=(
                SimpleNamespace(
                    provider="claude",
                    agent_id="claude",
                    role="implementer",
                    live=True,
                    capture_mode="terminal-script",
                ),
                SimpleNamespace(
                    provider="codex",
                    agent_id="codex",
                    role="reviewer",
                    live=True,
                    capture_mode="remote-control",
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
            remote_control_attachment=_remote_control_attachment(
                "codex",
                role="reviewer",  # NOT "operator"; mirrors live session shape
            )
        ),
    )

    # Attachment role is "reviewer" not "operator". Reroute MUST still fire
    # because provider==review_agent and coding_agent is a separate live
    # writable lane. Without this, stage_commit_pipeline recirculates back
    # to the blocked reviewer (codex).
    assert _resolve_commit_stage_target(review_state) == "claude"


def test_commit_stage_target_reroutes_to_actor_authority_mutation_owner() -> None:
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="tools_only",
            coding_agent="claude",
            review_agent="codex",
            mutation_owner="claude",
            actor_authorities=(
                _actor_authority("claude", capabilities=("repo.stage",)),
            ),
            role_assignments=(
                SimpleNamespace(role_id="coding_agent", provider="claude", live=True),
                SimpleNamespace(role_id="review_agent", provider="codex", live=True),
            ),
            topology_mode="active_dual_agent",
            participants=(
                SimpleNamespace(
                    provider="claude",
                    agent_id="claude",
                    role="implementer",
                    live=True,
                    capture_mode="terminal-script",
                ),
                SimpleNamespace(
                    provider="codex",
                    agent_id="codex",
                    role="reviewer",
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
            reviewer_mode="tools_only",
        ),
        reviewer_runtime=SimpleNamespace(
            remote_control_attachment=_remote_control_attachment(
                "codex",
                role="reviewer",
            )
        ),
    )

    assert _resolve_commit_stage_target(review_state) == "claude"


def test_commit_stage_target_ignores_mismatched_capability_provider() -> None:
    """Capability ownership must match the reroute target.

    Otherwise a stale ``codex`` implementer_capability (in a single-agent
    state) could authorize rerouting ``stage_commit_pipeline`` to a
    ``claude`` coding lane based on the wrong agent's may_edit_repo flag,
    suppressing the normal fallback and parking the handoff on an
    unverified executor. Repro: implementer_capability.provider == "codex"
    while reroute target would be "claude" → must not authorize reroute on
    the codex capability.
    """
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="single_agent",
            coding_agent="claude",
            review_agent="codex",
            role_assignments=(
                SimpleNamespace(role_id="coding_agent", provider="claude", live=True),
                SimpleNamespace(role_id="review_agent", provider="codex", live=True),
            ),
            topology_mode="single_agent",
            participants=(
                SimpleNamespace(
                    provider="codex",
                    agent_id="codex",
                    role="reviewer",
                    live=True,
                    capture_mode="remote-control",
                ),
            ),
        ),
        bridge=SimpleNamespace(
            implementer_capability=SimpleNamespace(
                provider="codex",
                may_edit_repo=True,
            ),
            reviewer_capability=SimpleNamespace(
                provider="codex",
                may_edit_repo=True,
            ),
            effective_reviewer_mode="single_agent",
            reviewer_mode="single_agent",
        ),
        reviewer_runtime=SimpleNamespace(
            remote_control_attachment=_remote_control_attachment("codex")
        ),
    )

    # Reroute target would be "claude" (coding_agent), but cached
    # implementer_capability is for "codex". Reroute must NOT fire on a
    # mismatched capability; falls through to attached provider ("codex").
    assert _resolve_commit_stage_target(review_state) == "codex"


def test_commit_stage_target_does_not_reroute_to_dead_implementer_lane() -> None:
    """Role-aware reroute must fail-closed when the coding_agent lane is
    dead or cannot edit the repo. Otherwise a degraded session would post
    a stage_commit_pipeline action_request to a stale implementer lane,
    which then suppresses the normal execution-handoff fallback in
    commit_preflight_validators.post_commit_stage_handoff().
    """
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="single_agent",
            coding_agent="claude",
            review_agent="codex",
            role_assignments=(
                SimpleNamespace(role_id="coding_agent", provider="claude", live=False),
                SimpleNamespace(role_id="review_agent", provider="codex", live=True),
            ),
            topology_mode="single_agent",
            participants=(
                SimpleNamespace(
                    provider="claude",
                    agent_id="claude",
                    role="implementer",
                    live=False,
                    capture_mode="terminal-script",
                ),
                SimpleNamespace(
                    provider="codex",
                    agent_id="codex",
                    role="reviewer",
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
            effective_reviewer_mode="single_agent",
            reviewer_mode="single_agent",
        ),
        reviewer_runtime=SimpleNamespace(
            remote_control_attachment=_remote_control_attachment("codex")
        ),
    )

    # Role-aware reroute target (coding_agent="claude") is dead +
    # may_edit_repo=False, so the reroute must fall through to the
    # attachment provider ("codex") rather than posting to a dead lane.
    assert _resolve_commit_stage_target(review_state) == "codex"


def test_commit_stage_target_fails_closed_without_remote_control_attachment() -> None:
    """When no remote-control executor lane is attached, the stage handoff
    must return an empty target so callers fail-closed instead of self-
    routing the request back to the same local lane that just got
    sandbox-blocked. Stage handoffs are only meaningful when there is an
    external writable lane to receive them.
    """
    review_state = SimpleNamespace(
        collaboration=SimpleNamespace(
            reviewer_mode="single_agent",
            coding_agent="claude",
            review_agent="claude",
            role_assignments=(
                SimpleNamespace(role_id="coding_agent", provider="claude", live=True),
            ),
            topology_mode="single_agent",
            participants=(
                SimpleNamespace(
                    provider="claude",
                    agent_id="claude",
                    role="implementer",
                    live=True,
                    capture_mode="terminal-script",
                ),
            ),
        ),
        bridge=SimpleNamespace(
            implementer_capability=SimpleNamespace(
                provider="claude",
                may_edit_repo=True,
            ),
            reviewer_capability=SimpleNamespace(
                provider="claude",
                may_edit_repo=True,
            ),
            effective_reviewer_mode="single_agent",
            reviewer_mode="single_agent",
        ),
        reviewer_runtime=SimpleNamespace(
            remote_control_attachment=None,
        ),
    )

    assert _resolve_commit_stage_target(review_state) == ""


def test_post_commit_execution_handoff_fails_closed_without_live_writable_target() -> (
    None
):
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
    assert (
        pipeline.validation_receipt.plan_id == pipeline.intent.validation_plan.plan_id
    )
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
            guard_attestation=_approval_attestation(
                decision_event["packet_id"],
                pipeline,
            ),
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
    assert (
        committed_pipeline.push_authorization.authorized_head_sha
        == committed_pipeline.commit_sha
    )
    assert (
        committed_pipeline.push_authorization.approval_mode
        == "commit_pipeline_approval"
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
    assert pushed_pipeline.state == "push_completed"
    assert pushed_pipeline.commit_sha == committed_pipeline.commit_sha
    remote_head = _run_git(remote_root, "rev-parse", "refs/heads/feature/pipeline-e2e")
    assert remote_head == pushed_pipeline.commit_sha


def test_push_override_reissues_publication_authorization_through_pipeline(
    tmp_path: Path,
) -> None:
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
            guard_attestation=_approval_attestation(
                decision_event["packet_id"],
                pipeline,
            ),
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
            guard_attestation=_approval_attestation(
                override_event["packet_id"],
                committed_pipeline,
            ),
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
    assert pushed_pipeline.push_authorization.decision_packet_id == str(
        override_event["packet_id"]
    )


def test_commit_does_not_reread_startup_publish_gate_after_approval(
    tmp_path: Path,
) -> None:
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
            guard_attestation=_approval_attestation(
                decision_event["packet_id"],
                pipeline,
            ),
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
            guard_attestation=_approval_attestation(
                decision_event["packet_id"],
                pipeline,
            ),
        ),
    )

    with patch(
        "dev.scripts.devctl.commands.vcs.governed_executor_sync.refresh_review_projections",
        side_effect=AssertionError(
            "`vcs.commit` must not refresh review projections after approval."
        ),
    ):
        commit_result = executor.execute(
            build_commit_action(
                repo_pack_id="test-pack",
                pipeline_id=pipeline.pipeline_id,
            )
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
            guard_attestation=_approval_attestation(
                decision_event["packet_id"],
                pipeline,
            ),
        ),
    )

    original_run_git_capture = __import__(
        "dev.scripts.devctl.commands.vcs.governed_executor_commit_phase",
        fromlist=["run_git_capture"],
    ).run_git_capture
    captured_calls: list[tuple[tuple[str, ...], dict[str, str] | None, bool]] = []

    def _capture_commit_args(
        args,
        *,
        repo_root: Path,
        extra_env=None,
        stream_output=False,
    ):
        captured_calls.append((tuple(args), extra_env, stream_output))
        return original_run_git_capture(
            args,
            repo_root=repo_root,
            extra_env=extra_env,
            stream_output=stream_output,
        )

    with patch(
        "dev.scripts.devctl.commands.vcs.governed_executor_commit_phase.run_git_capture",
        side_effect=_capture_commit_args,
    ), patch(
        "dev.scripts.devctl.commands.vcs.governed_executor_commit_phase.pending_packet_queue_block_commit",
        return_value=None,
    ):
        commit_result = executor.execute(
            build_commit_action(
                repo_pack_id="test-pack",
                pipeline_id=pipeline.pipeline_id,
                action_request_packet_id="rev_pkt_fixture_commit",
                action_request_target_agent="codex",
            )
        )

    assert commit_result.ok is True
    assert any(
        args[:3] == ("-c", "devctl.governed-commit=true", "commit")
        and "--no-verify" in args
        and extra_env == {"DEVCTL_GOVERNED_COMMIT": "1"}
        and stream_output is True
        for args, extra_env, stream_output in captured_calls
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


def _repo_with_devctl(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    scripts_dir = repo_root / "dev/scripts"
    scripts_dir.mkdir(parents=True)
    (scripts_dir / "devctl.py").write_text("", encoding="utf-8")
    return repo_root


def _startup_context_json(action: str, reason: str) -> str:
    return json.dumps(
        {
            "schema_version": 1,
            "contract_id": "StartupContext",
            "action": action,
            "reason": reason,
            "advisory_action": action,
            "advisory_reason": reason,
        },
        separators=(",", ":"),
        sort_keys=True,
    )


def _startup_context_runner(
    *,
    returncode: int,
    failure_output: str = "",
):
    def _runner(name, command, cwd):
        del cwd
        assert name == "commit-refresh-startup-context"
        assert command[-2:] == ["--format", "summary"]
        result: dict[str, object] = {
            "name": name,
            "cmd": command,
            "cwd": ".",
            "returncode": returncode,
            "duration_s": 0.1,
            "skipped": False,
        }
        if failure_output:
            result["failure_output"] = failure_output
        return result

    return _runner


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


def _push_policy():
    return build_test_push_policy()


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


def _startup_context_with_attention(
    *,
    attention_revision: str,
    owner: str,
    agent: str,
    wake_reason: str,
) -> SimpleNamespace:
    ctx = _startup_context(repo_root=Path("."))
    ctx.work_intake = SimpleNamespace(
        coordination=SimpleNamespace(active_implementation_owner=owner)
    )
    ctx.packet_inbox = SimpleNamespace(
        attention_revision=attention_revision,
        agents=(
            SimpleNamespace(
                agent=agent,
                attention_status="review_needed",
                wake_reason=wake_reason,
                pending_actionable_total=0,
            ),
        ),
    )
    return ctx


def _passing_guard_result() -> ActionResult:
    return ActionResult(
        schema_version=ACTION_RESULT_SCHEMA_VERSION,
        contract_id=ACTION_RESULT_CONTRACT_ID,
        action_id="quality.guard_bundle",
        ok=True,
        status=ActionOutcome.PASS,
        reason="",
    )


def _approval_attestation(packet_id: object, pipeline) -> PacketGuardAttestation:
    return PacketGuardAttestation(
        packet_id=str(packet_id),
        attestation_kind="commit_approval_guard",
        run_record_ids=("quality.guard_bundle",),
        pipeline_generation=pipeline.generation_id,
        staged_snapshot_hash=pipeline.intent.staged_tree_hash,
        operator_signature="operator",
        attested_by="operator",
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
            guard_attestation=_approval_attestation(
                decision_event["packet_id"],
                pipeline,
            ),
        ),
    )
