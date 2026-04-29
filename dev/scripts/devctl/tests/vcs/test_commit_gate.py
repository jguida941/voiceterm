"""Tests for the governed commit gate and typed commit pipeline."""

from __future__ import annotations

import importlib
import os
import stat
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands.governance import (
    startup_context as startup_context_command,
)
from dev.scripts.devctl.commands.vcs.commit import (
    _build_git_commit_cmd,
    _commit_permission_report,
    _pipeline_has_checkpoint_snapshot,
    _pipeline_has_validation_plan,
    _report_commit_shas,
    _resolve_interaction_mode,
    _run_guard_bundle,
    run_commit,
)
from dev.scripts.devctl.commands.vcs.commit_guard_bundle import guard_result
from dev.scripts.devctl.commands.vcs.commit_pipeline_blocking import (
    build_active_pipeline_block_report,
)
from dev.scripts.devctl.commands.vcs.commit_preflight import (
    apply_explicit_operator_approval,
    load_pipeline_for_explicit_approval,
    prepare_pipeline,
)
from dev.scripts.devctl.commands.vcs.commit_preflight_approval_packets import (
    build_commit_approval_attestation,
)
from dev.scripts.devctl.commands.vcs.commit_preflight_validators import (
    CommitPreflightDeps,
    prepare_pipeline as prepare_pipeline_with_deps,
)
from dev.scripts.devctl.commands.vcs.commit_preflight_support import (
    build_commit_approval_authority,
)
from dev.scripts.devctl.commands.vcs.governed_executor import GovernedVcsExecutor
from dev.scripts.devctl.commands.vcs.governed_executor_actions import (
    APPROVAL_PACKET_KIND,
    build_stage_action,
)
from dev.scripts.devctl.commands.vcs.governed_executor_packets import (
    build_commit_approval_decision,
    pipeline_target_ref,
)
from dev.scripts.devctl.config import REPO_ROOT
from dev.scripts.devctl.platform.coordination_snapshot_models import (
    CoordinationActorRecord,
    CoordinationSnapshot,
)
from dev.scripts.devctl.repo_packs import active_path_config
from dev.scripts.devctl.review_channel.events import (
    load_events,
    post_packet,
    resolve_artifact_paths,
    transition_packet,
)
from dev.scripts.devctl.review_channel.packet_contract import PacketTransitionRequest
from dev.scripts.devctl.review_channel.remote_control_attachment_artifact import (
    persist_remote_control_attachment,
)
from dev.scripts.devctl.runtime.commit_permission import CommitPermissionDecision
from dev.scripts.devctl.runtime.remote_commit_pipeline_models import (
    RemoteCommitPipelineContract,
)
from dev.scripts.devctl.runtime.remote_commit_pipeline_state import (
    STATE_DELIVERED_LOCALLY_PENDING_PUBLISH,
)
from dev.scripts.devctl.runtime.review_state_packet_models import ReviewPacketState
from dev.scripts.devctl.runtime.reviewer_runtime_models import (
    RemoteControlAttachmentState,
)
from dev.scripts.devctl.runtime.startup_context import ReviewerGateState, StartupContext
from dev.scripts.devctl.runtime.validation_contracts import ValidationPlan
from dev.scripts.devctl.runtime.work_intake_models import (
    WorkIntakeCoordinationState,
    WorkIntakePacket,
)
from dev.scripts.devctl.tests.vcs._git_helpers import _run_git
from dev.scripts.devctl.tests.vcs._push_policy_helpers import build_test_push_policy


def _make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "message": "test commit",
        "amend": False,
        "approve_pending": False,
        "role": None,
        "paths": (),
        "passthrough": [],
        "format": "json",
        "output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _mock_subprocess_result(returncode: int, stdout: str = "", stderr: str = ""):
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


def _evaluate_raw_git_commit_permission(repo_root: Path):
    module = importlib.import_module(
        "dev.scripts.devctl.runtime.commit_permission_hook"
    )
    return module.evaluate_raw_git_commit_permission(repo_root)


def _init_repo(repo_root: Path) -> Path:
    repo_root.mkdir(parents=True, exist_ok=True)
    _run_git(repo_root, "init")
    _run_git(repo_root, "config", "user.name", "VoiceTerm Tests")
    _run_git(repo_root, "config", "user.email", "tests@example.com")
    _run_git(repo_root, "checkout", "-b", "feature/pipeline-e2e")
    (repo_root / ".gitignore").write_text("dev/reports/\n", encoding="utf-8")
    review_channel_path = repo_root / "dev/active/review_channel.md"
    review_channel_path.parent.mkdir(parents=True, exist_ok=True)
    review_channel_path.write_text("# Review Channel\n", encoding="utf-8")
    (repo_root / "tracked.txt").write_text("initial\n", encoding="utf-8")
    _run_git(repo_root, "add", ".")
    _run_git(repo_root, "commit", "-m", "initial")
    return repo_root


def _push_policy():
    return build_test_push_policy()


def _executor(repo_root: Path) -> GovernedVcsExecutor:
    def _startup_context_fn(*, repo_root: Path):
        del repo_root
        return SimpleNamespace(
            implementation_permission="active",
            observed_control_topology="single_implementer_single_reviewer",
            reviewer_gate=SimpleNamespace(
                implementation_blocked=False,
                implementation_block_reason="",
                review_gate_allows_push=True,
            ),
            governance=SimpleNamespace(
                push_enforcement=SimpleNamespace(
                    checkpoint_required=False,
                    safe_to_continue_editing=True,
                )
            ),
        )

    return GovernedVcsExecutor(
        repo_root=repo_root,
        review_channel_path=repo_root / "dev/active/review_channel.md",
        push_policy=_push_policy(),
        startup_context_fn=_startup_context_fn,
        refresh_projections=True,
    )


def _persist_remote_operator_attachment(
    repo_root: Path,
    *,
    provider: str = "claude",
) -> None:
    persist_remote_control_attachment(
        RemoteControlAttachmentState(
            provider=provider,
            role="operator",
            attachment_id=f"{provider}-remote-operator",
            session_name=f"{provider}-remote-control",
            remote_session_id=f"{provider}-session",
            session_url=f"https://example.invalid/{provider}-session",
            status="attached",
            attached_at_utc="2026-04-18T14:00:00Z",
            last_seen_utc="2026-04-18T14:00:01Z",
        ),
        output_root=repo_root / active_path_config().review_status_dir_rel,
    )


def _capture_startup_context_payload(
    ctx: StartupContext,
    argv: list[str],
) -> tuple[int, dict[str, object]]:
    args = build_parser().parse_args(argv)
    captured: dict[str, object] = {}

    def _fake_emit(*_args, **kwargs):
        captured.update(kwargs["json_payload"])
        return 0

    with (
        patch.object(
            startup_context_command,
            "build_startup_context",
            return_value=ctx,
        ),
        patch.object(
            startup_context_command,
            "build_startup_authority_report",
            return_value={
                "ok": True,
                "checks_run": 10,
                "checks_passed": 10,
                "errors": [],
                "warnings": [],
            },
        ),
        patch.object(
            startup_context_command,
            "write_startup_receipt",
            return_value=Path("/tmp/startup-receipt.json"),
        ),
        patch.object(
            startup_context_command,
            "emit_machine_artifact_output",
            side_effect=_fake_emit,
        ),
    ):
        rc = startup_context_command.run(args)

    return rc, captured


class CommitReportShaTests(unittest.TestCase):
    def test_report_commit_shas_prefers_content_commit_when_head_is_receipt(
        self,
    ) -> None:
        with (
            patch(
                "dev.scripts.devctl.commands.vcs.commit.scan_repo_governance_safely",
                return_value=None,
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.commit.receipt_commit_parent_sha",
                return_value="content-sha",
            ),
        ):
            commit_sha, receipt_commit_sha = _report_commit_shas(
                repo_root=Path("/tmp/repo"),
                commit_sha="receipt-sha",
            )

        self.assertEqual(commit_sha, "content-sha")
        self.assertEqual(receipt_commit_sha, "receipt-sha")

    def test_report_commit_shas_uses_head_when_no_receipt_parent_exists(self) -> None:
        with (
            patch(
                "dev.scripts.devctl.commands.vcs.commit.scan_repo_governance_safely",
                return_value=None,
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.commit.receipt_commit_parent_sha",
                return_value="",
            ),
        ):
            commit_sha, receipt_commit_sha = _report_commit_shas(
                repo_root=Path("/tmp/repo"),
                commit_sha="head-sha",
            )

        self.assertEqual(commit_sha, "head-sha")
        self.assertEqual(receipt_commit_sha, "")


class TestStartupActionRouting(unittest.TestCase):
    def test_commit_parser_accepts_approve_pending_flag(self) -> None:
        args = build_parser().parse_args(["commit", "--approve-pending"])

        self.assertTrue(args.approve_pending)

    def test_dashboard_role_projects_read_only_agent_lane(self) -> None:
        rc, captured = _capture_startup_context_payload(
            StartupContext(
                reviewer_gate=ReviewerGateState(),
                advisory_action="continue_editing",
                advisory_reason="clean_worktree",
                implementation_permission="active",
            ),
            ["startup-context", "--role", "dashboard", "--format", "json"],
        )

        self.assertEqual(rc, 0)
        self.assertEqual(captured["agent_lane"]["lane"], "dashboard")
        self.assertIn("implementation.edit", captured["blocked_actions"])
        self.assertIn("vcs.commit", captured["blocked_actions"])
        self.assertIn("review-channel.status", captured["allowed_actions"])
        self.assertFalse(captured["lane_edit_gate"]["edit_allowed"])
        self.assertEqual(captured["lane_edit_gate"]["status"], "findings_only")
        self.assertEqual(
            captured["next_command"],
            "python3 dev/scripts/devctl.py context-graph --mode bootstrap --format md",
        )

    def test_dashboard_role_names_live_implementation_owner_in_edit_gate(self) -> None:
        rc, captured = _capture_startup_context_payload(
            StartupContext(
                reviewer_gate=ReviewerGateState(),
                advisory_action="continue_editing",
                advisory_reason="clean_worktree",
                implementation_permission="active",
                work_intake=WorkIntakePacket(
                    coordination=WorkIntakeCoordinationState(
                        implementation_permission="active",
                        active_implementation_owner="codex",
                        active_participants=("codex:implementer",),
                    )
                ),
                coordination=CoordinationSnapshot(
                    actors=(
                        CoordinationActorRecord(
                            actor_id="codex",
                            provider="codex",
                            role="implementer",
                            presence="live",
                        ),
                    ),
                ),
            ),
            ["startup-context", "--role", "dashboard", "--format", "json"],
        )

        self.assertEqual(rc, 0)
        self.assertEqual(
            captured["lane_edit_gate"]["active_implementation_owner"],
            "codex",
        )
        self.assertEqual(
            captured["lane_edit_gate"]["reason"],
            "active_implementation_lane_owned_by_other_agent",
        )
        self.assertEqual(
            captured["agent_lane"]["edit_gate"]["allowed_outputs"],
            ["finding_packet", "action_request_packet"],
        )

    def test_blocked_permission_projects_action_routing(self) -> None:
        rc, captured = _capture_startup_context_payload(
            StartupContext(
                reviewer_gate=ReviewerGateState(),
                advisory_action="continue_editing",
                advisory_reason="collapsed_topology",
                observed_control_topology="no_live_agents",
                implementation_permission="blocked",
                work_intake=WorkIntakePacket(
                    coordination=WorkIntakeCoordinationState(
                        implementation_permission="blocked",
                        active_implementation_owner="codex",
                        active_participants=("codex:implementer",),
                    )
                ),
            ),
            ["startup-context", "--format", "json"],
        )

        self.assertEqual(rc, 0)
        self.assertIn("implementation.edit", captured["blocked_actions"])
        self.assertIn("vcs.stage", captured["allowed_actions"])
        self.assertIn("vcs.commit", captured["allowed_actions"])
        self.assertEqual(captured["recovery_action"], "none")
        self.assertEqual(
            captured["control_recovery_action"],
            "refresh_startup_or_review_status",
        )
        self.assertEqual(captured["escalation_action"], "operator_resync_required")
        self.assertEqual(
            captured["next_command"],
            "python3 dev/scripts/devctl.py review-channel --action status "
            "--terminal none --format json",
        )

    def test_prepare_pipeline_blocks_push_blocked_pipeline_with_exact_next_command(
        self,
    ) -> None:
        pipeline = SimpleNamespace(
            pipeline_id="pipeline-123",
            state="push_blocked",
            approval_state="approved",
            commit_sha="abc123",
        )
        executor = MagicMock()
        executor.load_pipeline.return_value = pipeline

        with (
            patch(
                "dev.scripts.devctl.commands.vcs.commit_preflight.pipeline_is_stale_for_current_repo",
                return_value=False,
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.commit_preflight.build_active_pipeline_block_report",
                return_value={
                    "reason": "active_pipeline_requires_publish_or_recovery",
                    "recommended_next_action": "refresh-authorization",
                    "next_command": "python3 dev/scripts/devctl.py push --execute",
                    "pipeline_state": "push_blocked",
                    "commit_phase": "push_blocked",
                },
            ),
        ):
            returned_pipeline, warnings, report = prepare_pipeline(
                args=_make_args(),
                repo_root=Path("/tmp/repo"),
                resolved_policy=SimpleNamespace(repo_pack_id="voiceterm"),
                vcs_executor=executor,
            )

        self.assertIs(returned_pipeline, pipeline)
        self.assertEqual(warnings, [])
        self.assertEqual(
            report["reason"], "active_pipeline_requires_publish_or_recovery"
        )
        self.assertEqual(report["pipeline_state"], "push_blocked")
        self.assertEqual(report["recommended_next_action"], "refresh-authorization")
        self.assertEqual(
            report["next_command"],
            "python3 dev/scripts/devctl.py push --execute",
        )
        self.assertEqual(report["commit_phase"], "push_blocked")

    def test_prepare_pipeline_auto_transitions_non_destructive_push_block(
        self,
    ) -> None:
        blocked_pipeline = SimpleNamespace(
            pipeline_id="pipeline-123",
            state="push_blocked",
            approval_state="approved",
            commit_sha="abc123",
        )
        delivered_pipeline = SimpleNamespace(
            pipeline_id="pipeline-123",
            state=STATE_DELIVERED_LOCALLY_PENDING_PUBLISH,
            approval_state="approved",
            commit_sha="abc123",
        )
        staged_pipeline = SimpleNamespace(
            pipeline_id="pipeline-456",
            state="staged",
            approval_state="pending",
        )
        stage_result = SimpleNamespace(ok=True, warnings=(), reason="staged")
        executor = MagicMock()
        executor.load_pipeline.side_effect = [
            blocked_pipeline,
            delivered_pipeline,
            staged_pipeline,
        ]
        executor.execute.return_value = stage_result

        block_report = MagicMock()
        auto_transition = MagicMock(return_value=True)

        with (
            patch(
                "dev.scripts.devctl.commands.vcs.commit_preflight_validators.preflight_import_index_atomicity",
                side_effect=lambda **kwargs: (kwargs["stage_warnings"], None),
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.commit_preflight_validators.append_orphan_snapshot_advisory",
            ),
        ):
            returned_pipeline, warnings, report = prepare_pipeline_with_deps(
                args=_make_args(),
                repo_root=Path("/tmp/repo"),
                resolved_policy=SimpleNamespace(repo_pack_id="voiceterm"),
                vcs_executor=executor,
                deps=CommitPreflightDeps(
                    pipeline_is_stale_for_current_repo_fn=lambda **_: False,
                    build_active_pipeline_block_report_fn=block_report,
                    auto_transition_non_destructive_push_failure_fn=auto_transition,
                ),
            )

        self.assertIs(returned_pipeline, staged_pipeline)
        self.assertEqual(warnings, [])
        self.assertIsNone(report)
        auto_transition.assert_called_once_with(
            repo_root=Path("/tmp/repo"),
            pipeline=blocked_pipeline,
        )
        block_report.assert_not_called()
        executor.execute.assert_called_once()

    def test_prepare_pipeline_posts_handoff_when_reuse_staged_index_hits_git_lock(
        self,
    ) -> None:
        pipeline = SimpleNamespace(
            pipeline_id="pipeline-123",
            state="abandoned",
            approval_state="approved",
            intent=SimpleNamespace(staged_tree_hash="tree-123"),
        )
        stage_result = SimpleNamespace(
            ok=False,
            reason="git_index_write_blocked",
            operator_guidance="generic git guidance",
            warnings=(
                "fatal: Unable to create '/tmp/repo/.git/index.lock': Operation not permitted",
            ),
        )
        executor = MagicMock()
        executor.load_pipeline.side_effect = [pipeline, pipeline]
        executor.execute.return_value = stage_result
        executor.review_channel_path = Path("/tmp/repo/dev/active/review_channel.md")

        with (
            patch(
                "dev.scripts.devctl.commands.vcs.commit_preflight.pipeline_is_stale_for_current_repo",
                return_value=False,
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.commit_preflight.post_commit_execution_handoff",
                return_value=("claude", "rev_pkt_123", ""),
            ) as handoff_mock,
        ):
            returned_pipeline, warnings, report = prepare_pipeline(
                args=_make_args(),
                repo_root=Path("/tmp/repo"),
                resolved_policy=SimpleNamespace(repo_pack_id="voiceterm"),
                vcs_executor=executor,
            )

        self.assertIs(returned_pipeline, pipeline)
        self.assertEqual(warnings, list(stage_result.warnings))
        self.assertEqual(report["reason"], "git_index_write_blocked")
        self.assertIn("rev_pkt_123", report["operator_guidance"])
        self.assertIn("claude", report["operator_guidance"])
        self.assertIn("commit_execution_request_packet=rev_pkt_123", report["warnings"])
        self.assertIn("commit_execution_request_target=claude", report["warnings"])
        handoff_mock.assert_called_once_with(
            pipeline=pipeline,
            repo_root=Path("/tmp/repo"),
            review_channel_path=Path("/tmp/repo/dev/active/review_channel.md"),
        )
        execute_action = executor.execute.call_args.args[0]
        self.assertTrue(execute_action.parameters["reuse_staged_index"])

    def test_prepare_pipeline_blocks_on_import_index_atomicity_violation(
        self,
    ) -> None:
        empty_pipeline = SimpleNamespace(
            pipeline_id="",
            state="",
            approval_state="",
        )
        staged_pipeline = SimpleNamespace(
            pipeline_id="pipeline-123",
            state="staged",
            approval_state="pending",
        )
        stage_result = SimpleNamespace(
            ok=True,
            reason="staged",
            warnings=(),
        )
        executor = MagicMock()
        executor.load_pipeline.side_effect = [empty_pipeline, staged_pipeline]
        executor.execute.return_value = stage_result
        violation = (
            "app/operator_console/state/snapshots/phone_status_snapshot.py: "
            "`from dev.scripts.devctl.phone_status_views import compact_view` "
            "resolves to module candidates `dev/scripts/devctl/phone_status_views.py`, "
            "`dev/scripts/devctl/phone_status_views/__init__.py` missing from git "
            "index (staged)."
        )

        with (
            patch(
                "dev.scripts.devctl.commands.vcs.commit_preflight.pipeline_is_stale_for_current_repo",
                return_value=False,
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.commit_preflight_atomicity.list_staged_new_python_module_paths",
                return_value=(("dev/scripts/devctl/mobile/phone_views.py",), None),
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.commit_preflight_atomicity.collect_import_index_atomicity_findings",
                return_value=([violation], []),
            ),
        ):
            returned_pipeline, warnings, report = prepare_pipeline(
                args=_make_args(),
                repo_root=Path("/tmp/repo"),
                resolved_policy=SimpleNamespace(repo_pack_id="voiceterm"),
                vcs_executor=executor,
            )

        self.assertIs(returned_pipeline, staged_pipeline)
        self.assertEqual(warnings, [])
        self.assertEqual(report["reason"], "import_index_atomicity_violation")
        self.assertEqual(
            report["staged_new_python_module_paths"],
            ["dev/scripts/devctl/mobile/phone_views.py"],
        )
        self.assertEqual(report["import_index_atomicity_findings"], [violation])
        self.assertIn("phone_status_views.py", report["operator_guidance"])

    def test_prepare_pipeline_consults_orphan_snapshot_advisory(self) -> None:
        empty_pipeline = SimpleNamespace(
            pipeline_id="",
            state="",
            approval_state="",
        )
        staged_pipeline = SimpleNamespace(
            pipeline_id="pipeline-123",
            state="staged",
            approval_state="pending",
        )
        stage_result = SimpleNamespace(
            ok=True,
            reason="staged",
            warnings=(),
        )
        executor = MagicMock()
        executor.load_pipeline.side_effect = [empty_pipeline, staged_pipeline]
        executor.execute.return_value = stage_result

        def _append_advisory(warnings, *, repo_root, scan_trigger):
            self.assertEqual(repo_root, Path("/tmp/repo"))
            self.assertEqual(scan_trigger, "commit_preflight")
            warnings.append("orphan_snapshot_advisory snapshot_hash=sha256:test")
            return None

        with (
            patch(
                "dev.scripts.devctl.commands.vcs.commit_preflight.pipeline_is_stale_for_current_repo",
                return_value=False,
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.commit_preflight_validators.preflight_import_index_atomicity",
                side_effect=lambda **kwargs: (kwargs["stage_warnings"], None),
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.commit_preflight_validators.append_orphan_snapshot_advisory",
                side_effect=_append_advisory,
            ) as advisory_mock,
        ):
            returned_pipeline, warnings, report = prepare_pipeline(
                args=_make_args(),
                repo_root=Path("/tmp/repo"),
                resolved_policy=SimpleNamespace(repo_pack_id="voiceterm"),
                vcs_executor=executor,
            )

        self.assertIs(returned_pipeline, staged_pipeline)
        self.assertIsNone(report)
        self.assertIn("orphan_snapshot_advisory snapshot_hash=sha256:test", warnings)
        advisory_mock.assert_called_once()

    def test_load_pipeline_for_explicit_approval_projects_commit_command(self) -> None:
        pipeline = SimpleNamespace(
            pipeline_id="",
            state="",
            approval_state="",
        )
        executor = MagicMock()
        executor.load_pipeline.return_value = pipeline

        returned_pipeline, report = load_pipeline_for_explicit_approval(
            repo_root=Path("/tmp/repo"),
            vcs_executor=executor,
        )

        self.assertIs(returned_pipeline, pipeline)
        self.assertEqual(report["reason"], "no_pending_pipeline_to_approve")
        self.assertEqual(
            report["next_command"],
            'python3 dev/scripts/devctl.py commit -m "<descriptive message>"',
        )
        self.assertEqual(report["recommended_next_action"], "stage_commit_pipeline")

    def test_active_pipeline_block_report_auto_refreshes_same_head_authorization(
        self,
    ) -> None:
        pipeline = SimpleNamespace(
            pipeline_id="pipeline-123",
            state="commit_recorded",
            approval_state="approved",
            commit_sha="abc123",
        )
        stale_view = {
            "state": "commit_recorded",
            "recommended_next_action": "refresh-authorization",
            "next_command": (
                "python3 dev/scripts/devctl.py pipeline --action "
                "refresh-authorization --format json"
            ),
            "authorized_head_sha": "abc123",
            "current_head_sha": "abc123",
        }
        refreshed_view = {
            "state": "commit_recorded",
            "recommended_next_action": "mark-delivered-local",
            "next_command": (
                "python3 dev/scripts/devctl.py pipeline --action mark-delivered-local "
                '--reason "<descriptive reason>" --format json'
            ),
            "authorized_head_sha": "abc123",
            "current_head_sha": "abc123",
        }
        with (
            patch(
                "dev.scripts.devctl.commands.vcs.commit_pipeline_blocking.build_status_view",
                side_effect=[stale_view, refreshed_view],
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.commit_pipeline_blocking.apply_refresh_authorization",
                return_value={"ok": True, "receipt_path": "/tmp/refresh.json"},
            ) as refresh_mock,
        ):
            report = build_active_pipeline_block_report(
                repo_root=Path("/tmp/repo"),
                pipeline=pipeline,
            )

        refresh_mock.assert_called_once()
        self.assertEqual(
            report["next_command"],
            "python3 dev/scripts/devctl.py pipeline --action mark-delivered-local "
            '--reason "<descriptive reason>" --format json',
        )
        self.assertEqual(report["recommended_next_action"], "mark-delivered-local")
        self.assertEqual(
            report["operator_guidance"],
            "Run `python3 dev/scripts/devctl.py pipeline --action mark-delivered-local "
            '--reason "<descriptive reason>" --format json` before creating '
            "another commit.",
        )
        self.assertTrue(report["authorization_refreshed"])
        self.assertEqual(report["refresh_receipt_path"], "/tmp/refresh.json")

    def test_active_pipeline_block_report_marks_superseded_commit_delivered_local(
        self,
    ) -> None:
        pipeline = SimpleNamespace(
            pipeline_id="pipeline-123",
            state="commit_recorded",
            approval_state="approved",
            commit_sha="abc123",
        )
        status_view = {
            "recommended_next_action": "none",
            "next_command": "python3 dev/scripts/devctl.py push --execute",
            "current_head_sha": "abc123",
        }
        with (
            patch(
                "dev.scripts.devctl.commands.vcs.commit_pipeline_blocking.build_status_view",
                return_value=status_view,
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.commit_pipeline_blocking.scan_repo_governance_safely",
                return_value=SimpleNamespace(
                    push_enforcement=SimpleNamespace(
                        ahead_of_upstream_commits=1,
                        worktree_dirty=True,
                        recommended_action="commit_before_push",
                    )
                ),
            ),
        ):
            report = build_active_pipeline_block_report(
                repo_root=Path("/tmp/repo"),
                pipeline=pipeline,
            )

        self.assertEqual(report["recommended_next_action"], "mark-delivered-local")
        self.assertEqual(
            report["next_command"],
            "python3 dev/scripts/devctl.py pipeline --action mark-delivered-local "
            '--reason "<descriptive reason>" --format json',
        )
        self.assertEqual(
            report["operator_guidance"],
            "Run `python3 dev/scripts/devctl.py pipeline --action mark-delivered-local "
            '--reason "<descriptive reason>" --format json` before creating '
            "another commit.",
        )


class TestPreCommitHookTemplate(unittest.TestCase):
    HOOK_PATH = (
        REPO_ROOT / "dev/config/templates/portable_governance_pre_commit_hook.sh"
    )

    def test_hook_template_exists(self):
        self.assertTrue(self.HOOK_PATH.exists())

    def test_hook_template_is_executable(self):
        mode = os.stat(self.HOOK_PATH).st_mode
        self.assertTrue(mode & stat.S_IXUSR)

    def test_hook_template_uses_quick_profile(self):
        content = self.HOOK_PATH.read_text()
        self.assertIn("--profile quick", content)
        self.assertNotIn("--profile ci", content)

    def test_hook_template_checks_commit_permission(self):
        content = self.HOOK_PATH.read_text()
        self.assertIn("commit_permission_hook", content)


class TestManagedPreCommitHookTemplate(unittest.TestCase):
    HOOK_PATH = REPO_ROOT / "dev/config/git_hooks/pre-commit-review-snapshot.sh"

    def test_managed_hook_checks_commit_permission(self):
        content = self.HOOK_PATH.read_text()
        self.assertIn("commit_permission_hook", content)
        self.assertIn("DEVCTL_REVIEW_SNAPSHOT_RECEIPT_COMMIT", content)
        self.assertIn("devctl.governed-commit", content)
        self.assertIn("DEVCTL_GOVERNED_COMMIT", content)
        self.assertIn("review-channel --action status", content)


class TestRawGitCommitPermissionHook(unittest.TestCase):
    def test_evaluate_raw_git_commit_permission_allows_valid_authority(self) -> None:
        ctx = SimpleNamespace(
            implementation_permission="active",
            observed_control_topology="single_implementer_single_reviewer",
            reviewer_gate=SimpleNamespace(
                review_gate_allows_push=True,
                implementation_blocked=False,
                implementation_block_reason="",
            ),
            governance=SimpleNamespace(
                push_enforcement=SimpleNamespace(
                    checkpoint_required=False,
                    safe_to_continue_editing=True,
                )
            ),
        )
        with patch(
            "dev.scripts.devctl.runtime.startup_context.build_startup_context",
            return_value=ctx,
        ):
            allowed, lines = _evaluate_raw_git_commit_permission(Path("/tmp/repo"))

        self.assertTrue(allowed)
        self.assertEqual(lines, ())

    def test_evaluate_raw_git_commit_permission_blocks_with_guidance(self) -> None:
        ctx = SimpleNamespace(
            implementation_permission="blocked",
            observed_control_topology="no_live_agents",
            reviewer_gate=SimpleNamespace(
                review_gate_allows_push=False,
                implementation_blocked=True,
                implementation_block_reason="reviewer_loop_relaunch_required",
            ),
            governance=SimpleNamespace(
                push_enforcement=SimpleNamespace(
                    checkpoint_required=False,
                    safe_to_continue_editing=True,
                )
            ),
        )
        with patch(
            "dev.scripts.devctl.runtime.startup_context.build_startup_context",
            return_value=ctx,
        ):
            allowed, lines = _evaluate_raw_git_commit_permission(Path("/tmp/repo"))

        rendered = "\n".join(lines)
        self.assertFalse(allowed)
        self.assertIn("Raw git commit is blocked", rendered)
        self.assertIn("implementation_permission_blocked", rendered)
        self.assertIn("review_authority_stale", rendered)
        self.assertIn("review-channel --action status", rendered)

    def test_evaluate_raw_git_commit_permission_allows_managed_projection_handoff_receipt(
        self,
    ) -> None:
        ctx = SimpleNamespace(
            implementation_permission="blocked",
            observed_control_topology="no_live_agents",
            reviewer_gate=SimpleNamespace(
                review_gate_allows_push=False,
                implementation_blocked=True,
                implementation_block_reason="runtime_missing",
            ),
            governance=SimpleNamespace(
                push_enforcement=SimpleNamespace(
                    checkpoint_required=False,
                    safe_to_continue_editing=True,
                )
            ),
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _run_git(repo_root, "init")
            _run_git(repo_root, "config", "user.email", "test@example.com")
            _run_git(repo_root, "config", "user.name", "Test User")
            snapshot_path = repo_root / "dev/audits/REVIEW_SNAPSHOT.md"
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot_path.write_text("base\n", encoding="utf-8")
            _run_git(repo_root, "add", "dev/audits/REVIEW_SNAPSHOT.md")
            _run_git(repo_root, "commit", "-m", "base")
            snapshot_path.write_text("receipt\n", encoding="utf-8")
            _run_git(repo_root, "add", "dev/audits/REVIEW_SNAPSHOT.md")

            with (
                patch(
                    "dev.scripts.devctl.runtime.startup_context.build_startup_context",
                    return_value=ctx,
                ),
                patch(
                    "dev.scripts.devctl.runtime.completed_handoff_authority."
                    "current_completed_handoff_outcome",
                    return_value=SimpleNamespace(outcome="completed_handoff"),
                ),
                patch.dict(
                    os.environ,
                    {"DEVCTL_MANAGED_PROJECTION_RECEIPT_COMMIT": "1"},
                ),
            ):
                allowed, lines = _evaluate_raw_git_commit_permission(repo_root)

        self.assertTrue(allowed)
        self.assertEqual(lines, ())

    def test_evaluate_raw_git_commit_permission_blocks_source_commit_despite_handoff_receipt(
        self,
    ) -> None:
        ctx = SimpleNamespace(
            implementation_permission="blocked",
            observed_control_topology="no_live_agents",
            reviewer_gate=SimpleNamespace(
                review_gate_allows_push=False,
                implementation_blocked=True,
                implementation_block_reason="runtime_missing",
            ),
            governance=SimpleNamespace(
                push_enforcement=SimpleNamespace(
                    checkpoint_required=False,
                    safe_to_continue_editing=True,
                )
            ),
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _run_git(repo_root, "init")
            _run_git(repo_root, "config", "user.email", "test@example.com")
            _run_git(repo_root, "config", "user.name", "Test User")
            source_path = repo_root / "source.py"
            source_path.write_text("print('base')\n", encoding="utf-8")
            _run_git(repo_root, "add", "source.py")
            _run_git(repo_root, "commit", "-m", "base")
            source_path.write_text("print('blocked')\n", encoding="utf-8")
            _run_git(repo_root, "add", "source.py")

            with (
                patch(
                    "dev.scripts.devctl.runtime.startup_context.build_startup_context",
                    return_value=ctx,
                ),
                patch(
                    "dev.scripts.devctl.runtime.completed_handoff_authority."
                    "current_completed_handoff_outcome",
                    return_value=SimpleNamespace(outcome="completed_handoff"),
                ),
                patch.dict(
                    os.environ,
                    {"DEVCTL_MANAGED_PROJECTION_RECEIPT_COMMIT": "1"},
                ),
            ):
                allowed, lines = _evaluate_raw_git_commit_permission(repo_root)

        rendered = "\n".join(lines)
        self.assertFalse(allowed)
        self.assertIn("implementation_permission_blocked", rendered)
        self.assertIn("review_authority_stale", rendered)

    def test_evaluate_raw_git_commit_permission_blocks_managed_projection_without_handoff(
        self,
    ) -> None:
        ctx = SimpleNamespace(
            implementation_permission="blocked",
            observed_control_topology="no_live_agents",
            reviewer_gate=SimpleNamespace(
                review_gate_allows_push=False,
                implementation_blocked=True,
                implementation_block_reason="runtime_missing",
            ),
            governance=SimpleNamespace(
                push_enforcement=SimpleNamespace(
                    checkpoint_required=False,
                    safe_to_continue_editing=True,
                )
            ),
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _run_git(repo_root, "init")
            _run_git(repo_root, "config", "user.email", "test@example.com")
            _run_git(repo_root, "config", "user.name", "Test User")
            snapshot_path = repo_root / "dev/audits/REVIEW_SNAPSHOT.md"
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot_path.write_text("base\n", encoding="utf-8")
            _run_git(repo_root, "add", "dev/audits/REVIEW_SNAPSHOT.md")
            _run_git(repo_root, "commit", "-m", "base")
            snapshot_path.write_text("receipt\n", encoding="utf-8")
            _run_git(repo_root, "add", "dev/audits/REVIEW_SNAPSHOT.md")

            with (
                patch(
                    "dev.scripts.devctl.runtime.startup_context.build_startup_context",
                    return_value=ctx,
                ),
                patch(
                    "dev.scripts.devctl.runtime.completed_handoff_authority."
                    "current_completed_handoff_outcome",
                    return_value=None,
                ),
                patch.dict(
                    os.environ,
                    {"DEVCTL_MANAGED_PROJECTION_RECEIPT_COMMIT": "1"},
                ),
            ):
                allowed, lines = _evaluate_raw_git_commit_permission(repo_root)

        rendered = "\n".join(lines)
        self.assertFalse(allowed)
        self.assertIn("implementation_permission_blocked", rendered)
        self.assertIn("review_authority_stale", rendered)

    def test_evaluate_raw_git_commit_permission_stays_blocked_for_checkpoint_only_state(
        self,
    ) -> None:
        ctx = SimpleNamespace(
            implementation_permission="blocked",
            observed_control_topology="no_live_agents",
            advisory_action="checkpoint_allowed",
            push_decision=SimpleNamespace(action="await_checkpoint"),
            reviewer_gate=SimpleNamespace(
                review_gate_allows_push=True,
                implementation_blocked=False,
                implementation_block_reason="",
                checkpoint_permitted=True,
            ),
            governance=SimpleNamespace(
                push_enforcement=SimpleNamespace(
                    checkpoint_required=False,
                    safe_to_continue_editing=True,
                )
            ),
        )
        with patch(
            "dev.scripts.devctl.runtime.startup_context.build_startup_context",
            return_value=ctx,
        ):
            allowed, lines = _evaluate_raw_git_commit_permission(Path("/tmp/repo"))

        rendered = "\n".join(lines)
        self.assertFalse(allowed)
        self.assertIn("implementation_permission_blocked", rendered)
        self.assertIn("review-channel --action status", rendered)

    def test_evaluate_raw_git_commit_permission_stays_blocked_for_suspended_checkpoint_recovery(
        self,
    ) -> None:
        ctx = SimpleNamespace(
            implementation_permission="suspended",
            observed_control_topology="implementer_without_reviewer",
            advisory_action="checkpoint_before_continue",
            push_decision=SimpleNamespace(action="await_checkpoint"),
            reviewer_gate=SimpleNamespace(
                review_gate_allows_push=False,
                implementation_blocked=True,
                implementation_block_reason="runtime_missing",
                checkpoint_permitted=True,
            ),
            governance=SimpleNamespace(
                push_enforcement=SimpleNamespace(
                    checkpoint_required=True,
                    safe_to_continue_editing=False,
                )
            ),
        )
        with patch(
            "dev.scripts.devctl.runtime.startup_context.build_startup_context",
            return_value=ctx,
        ):
            allowed, lines = _evaluate_raw_git_commit_permission(Path("/tmp/repo"))

        rendered = "\n".join(lines)
        self.assertFalse(allowed)
        self.assertIn("implementation_permission_suspended", rendered)
        self.assertIn("review_authority_stale", rendered)
        self.assertIn("review-channel --action status", rendered)

    def test_evaluate_raw_git_commit_permission_fails_closed_when_context_load_errors(
        self,
    ) -> None:
        with patch(
            "dev.scripts.devctl.runtime.startup_context.build_startup_context",
            side_effect=ValueError("review state unavailable"),
        ):
            allowed, lines = _evaluate_raw_git_commit_permission(Path("/tmp/repo"))

        rendered = "\n".join(lines)
        self.assertFalse(allowed)
        self.assertIn("failing closed", rendered)
        self.assertIn("review state unavailable", rendered)
        self.assertIn("startup-context --format summary", rendered)


class TestBuildGitCommitCmd(unittest.TestCase):
    def test_message_only(self):
        args = _make_args(message="fix: resolve bug")
        self.assertEqual(
            _build_git_commit_cmd(args), ["git", "commit", "-m", "fix: resolve bug"]
        )

    def test_amend(self):
        args = _make_args(message=None, amend=True)
        self.assertEqual(_build_git_commit_cmd(args), ["git", "commit", "--amend"])

    def test_message_and_passthrough(self):
        args = _make_args(message="updated msg", passthrough=["--allow-empty"])
        self.assertEqual(
            _build_git_commit_cmd(args),
            ["git", "commit", "-m", "updated msg", "--allow-empty"],
        )


class TestGuardBundleRunner(unittest.TestCase):
    def test_guard_bundle_calls_check_quick_with_validation_plan_bypass(self):
        mock_runner = MagicMock(return_value=_mock_subprocess_result(0))
        pipeline = SimpleNamespace(
            intent=SimpleNamespace(
                validation_plan=ValidationPlan(
                    plan_id="validation-plan-1",
                    bundle_id="quick",
                    staged_tree_hash="tree-123",
                )
            )
        )
        rc = _run_guard_bundle(runner=mock_runner, pipeline=pipeline)

        self.assertEqual(rc, 0)
        call_args = mock_runner.call_args
        cmd = call_args[1].get("cmd") or call_args[0][0]
        cmd_str = " ".join(cmd)
        self.assertIn("check", cmd_str)
        self.assertIn("--profile", cmd_str)
        self.assertIn("quick", cmd_str)
        env = call_args[1]["env"]
        self.assertEqual(env["DEVCTL_COMMIT_GATE_BYPASS_STARTUP_AUTHORITY"], "1")

    def test_guard_bundle_does_not_bypass_without_validation_plan(self):
        mock_runner = MagicMock(return_value=_mock_subprocess_result(0))

        rc = _run_guard_bundle(runner=mock_runner)

        self.assertEqual(rc, 0)
        env = mock_runner.call_args[1]["env"]
        self.assertNotIn("DEVCTL_COMMIT_GATE_BYPASS_STARTUP_AUTHORITY", env)

    def test_guard_bundle_bypasses_with_staged_checkpoint_snapshot(self):
        mock_runner = MagicMock(return_value=_mock_subprocess_result(0))
        pipeline = SimpleNamespace(
            intent=SimpleNamespace(
                validation_plan=None,
                staged_tree_hash="tree-123",
                staged_path_count=4,
            )
        )

        rc = _run_guard_bundle(runner=mock_runner, pipeline=pipeline)

        self.assertEqual(rc, 0)
        env = mock_runner.call_args[1]["env"]
        self.assertEqual(env["DEVCTL_COMMIT_GATE_BYPASS_STARTUP_AUTHORITY"], "1")


class TestValidationPlanDetection(unittest.TestCase):
    def test_pipeline_has_validation_plan_requires_typed_fields(self) -> None:
        pipeline = SimpleNamespace(
            intent=SimpleNamespace(
                validation_plan=ValidationPlan(
                    plan_id="validation-plan-1",
                    bundle_id="quick",
                    staged_tree_hash="tree-123",
                )
            )
        )

        self.assertTrue(_pipeline_has_validation_plan(pipeline))
        self.assertFalse(
            _pipeline_has_validation_plan(
                SimpleNamespace(intent=SimpleNamespace(validation_plan=None))
            )
        )

    def test_pipeline_has_checkpoint_snapshot_accepts_staged_tree_without_validation_plan(
        self,
    ) -> None:
        pipeline = SimpleNamespace(
            intent=SimpleNamespace(
                validation_plan=None,
                staged_tree_hash="tree-123",
                staged_path_count=2,
            )
        )

        self.assertTrue(_pipeline_has_checkpoint_snapshot(pipeline))
        self.assertFalse(
            _pipeline_has_checkpoint_snapshot(
                SimpleNamespace(
                    intent=SimpleNamespace(
                        validation_plan=None,
                        staged_tree_hash="",
                        staged_path_count=0,
                    )
                )
            )
        )


class TestInteractionModeResolution(unittest.TestCase):
    def test_resolve_interaction_mode_threads_governance_into_read_model(self) -> None:
        repo_root = Path("/tmp/repo")
        governance = SimpleNamespace(bridge_config=SimpleNamespace())
        with (
            patch(
                "dev.scripts.devctl.commands.vcs.commit_preflight.scan_repo_governance_safely",
                return_value=governance,
            ) as scan_mock,
            patch(
                "dev.scripts.devctl.commands.vcs.commit_preflight.build_control_plane_read_model",
                return_value=SimpleNamespace(operator_interaction_mode="single_agent"),
            ) as build_model_mock,
        ):
            self.assertEqual(_resolve_interaction_mode(repo_root), "single_agent")

        scan_mock.assert_called_once_with(repo_root)
        build_model_mock.assert_called_once()
        args, kwargs = build_model_mock.call_args
        self.assertEqual(args, (repo_root,))
        self.assertIs(kwargs["options"].governance, governance)


class TestGovernedCommitPipeline(unittest.TestCase):
    def test_commit_parser_accepts_governed_path_selection(self) -> None:
        args = build_parser().parse_args(
            [
                "commit",
                "--paths",
                "tracked.txt",
                "dev/scripts/devctl.py",
                "-m",
                "feat: selected paths",
            ]
        )

        self.assertEqual(args.paths, ["tracked.txt", "dev/scripts/devctl.py"])
        self.assertEqual(args.message, "feat: selected paths")

    def test_commit_paths_stage_selected_dirty_paths_through_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            executor = _executor(repo_root)
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            guard_runner = MagicMock(return_value=_mock_subprocess_result(0))

            rc = run_commit(
                _make_args(
                    message="feat: selected governed path",
                    paths=("tracked.txt",),
                ),
                repo_root=repo_root,
                policy=_push_policy(),
                executor=executor,
                interaction_mode="local_terminal",
                guard_runner=guard_runner,
            )

            pipeline = executor.load_pipeline()
            self.assertEqual(rc, 0)
            self.assertEqual(pipeline.state, "commit_recorded")
            self.assertIn("tracked.txt", pipeline.intent.staged_paths)
            self.assertTrue(pipeline.commit_sha)

    def test_commit_paths_fail_closed_when_dirty_work_is_outside_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            executor = _executor(repo_root)
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            (repo_root / "outside.txt").write_text("outside\n", encoding="utf-8")
            guard_runner = MagicMock(return_value=_mock_subprocess_result(0))
            captured: dict[str, object] = {}

            with patch(
                "dev.scripts.devctl.commands.vcs.commit._emit_report",
                side_effect=lambda _args, report: captured.update(report),
            ):
                rc = run_commit(
                    _make_args(
                        message="feat: selected governed path",
                        paths=("tracked.txt",),
                    ),
                    repo_root=repo_root,
                    policy=_push_policy(),
                    executor=executor,
                    interaction_mode="local_terminal",
                    guard_runner=guard_runner,
                )

            pipeline = executor.load_pipeline()
            self.assertEqual(rc, 1)
            self.assertEqual(captured["reason"], "dirty_paths_outside_scope")
            self.assertIn("outside.txt", captured["warnings"])
            self.assertFalse(pipeline.pipeline_id)
            guard_runner.assert_not_called()

    def test_commit_paths_are_not_allowed_with_approve_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            executor = _executor(repo_root)
            captured: dict[str, object] = {}

            with patch(
                "dev.scripts.devctl.commands.vcs.commit._emit_report",
                side_effect=lambda _args, report: captured.update(report),
            ):
                rc = run_commit(
                    _make_args(approve_pending=True, paths=("tracked.txt",)),
                    repo_root=repo_root,
                    policy=_push_policy(),
                    executor=executor,
                    interaction_mode="local_terminal",
                    guard_runner=MagicMock(return_value=_mock_subprocess_result(0)),
                )

            self.assertEqual(rc, 1)
            self.assertEqual(
                captured["reason"],
                "paths_not_allowed_with_approve_pending",
            )

    def test_stage_reuse_index_blocks_snapshot_only_scope_with_dirty_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            executor = _executor(repo_root)
            snapshot_path = repo_root / "dev/audits/REVIEW_SNAPSHOT.md"
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot_path.write_text("stale snapshot\n", encoding="utf-8")
            _run_git(repo_root, "add", "dev/audits/REVIEW_SNAPSHOT.md")
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")

            stage_result = executor.execute(
                build_stage_action(
                    repo_pack_id=_push_policy().repo_pack_id,
                    commit_message_draft="feat: block snapshot-only commit",
                    push_requested=False,
                    guard_profile="quick",
                    work_intake_ref="devctl.commit",
                    reuse_staged_index=True,
                    requested_by="devctl.commit",
                )
            )

            pipeline = executor.load_pipeline()
            self.assertFalse(stage_result.ok)
            self.assertEqual(stage_result.reason, "staged_scope_missing_dirty_work")
            self.assertIn("tracked.txt", stage_result.warnings)
            self.assertIn(
                "Stage the intended paths first", stage_result.operator_guidance
            )
            self.assertFalse(pipeline.pipeline_id)

    def test_commit_blocks_dashboard_role_before_staging(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            _run_git(repo_root, "add", "tracked.txt")
            guard_runner = MagicMock(return_value=_mock_subprocess_result(0))
            captured: dict[str, object] = {}

            with patch(
                "dev.scripts.devctl.commands.vcs.commit._emit_report",
                side_effect=lambda _args, report: captured.update(report),
            ):
                rc = run_commit(
                    _make_args(
                        message="feat: blocked dashboard commit", role="dashboard"
                    ),
                    repo_root=repo_root,
                    policy=_push_policy(),
                    executor=_executor(repo_root),
                    interaction_mode="remote_control",
                    guard_runner=guard_runner,
                )

            pipeline = _executor(repo_root).load_pipeline()
            self.assertEqual(rc, 1)
            self.assertEqual(captured["reason"], "caller_role_blocked")
            self.assertEqual(captured["caller_role"], "dashboard")
            self.assertEqual(captured["caller_role_source"], "arg:role")
            self.assertFalse(pipeline.pipeline_id)
            guard_runner.assert_not_called()

    def test_commit_blocks_env_backed_reviewer_lane_before_staging(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            _run_git(repo_root, "add", "tracked.txt")
            guard_runner = MagicMock(return_value=_mock_subprocess_result(0))
            captured: dict[str, object] = {}

            with patch.dict(os.environ, {"DEVCTL_CALLER_ROLE": "reviewer"}):
                with patch(
                    "dev.scripts.devctl.commands.vcs.commit._emit_report",
                    side_effect=lambda _args, report: captured.update(report),
                ):
                    rc = run_commit(
                        _make_args(message="feat: blocked reviewer commit"),
                        repo_root=repo_root,
                        policy=_push_policy(),
                        executor=_executor(repo_root),
                        interaction_mode="dual_agent",
                        guard_runner=guard_runner,
                    )

            pipeline = _executor(repo_root).load_pipeline()
            self.assertEqual(rc, 1)
            self.assertEqual(captured["reason"], "caller_role_blocked")
            self.assertEqual(captured["caller_role"], "reviewer")
            self.assertEqual(captured["caller_role_source"], "env:DEVCTL_CALLER_ROLE")
            self.assertFalse(pipeline.pipeline_id)
            guard_runner.assert_not_called()

    def test_commit_allows_checkpoint_required_stage_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            _run_git(repo_root, "add", "tracked.txt")
            guard_runner = MagicMock(return_value=_mock_subprocess_result(0))

            def _startup_context_fn(*, repo_root: Path):
                del repo_root
                return SimpleNamespace(
                    implementation_permission="active",
                    observed_control_topology="single_implementer_single_reviewer",
                    reviewer_gate=SimpleNamespace(
                        implementation_blocked=True,
                        implementation_block_reason="checkpoint_required",
                        checkpoint_permitted=True,
                        review_gate_allows_push=False,
                    ),
                    governance=SimpleNamespace(
                        push_enforcement=SimpleNamespace(
                            checkpoint_required=True,
                            safe_to_continue_editing=True,
                        )
                    ),
                    push_decision=SimpleNamespace(
                        action="await_checkpoint",
                        reason="checkpoint_required",
                    ),
                )

            executor = GovernedVcsExecutor(
                repo_root=repo_root,
                review_channel_path=repo_root / "dev/active/review_channel.md",
                push_policy=_push_policy(),
                startup_context_fn=_startup_context_fn,
                refresh_projections=True,
            )

            rc = run_commit(
                _make_args(message="feat: governed checkpoint commit"),
                repo_root=repo_root,
                policy=_push_policy(),
                executor=executor,
                interaction_mode="local_terminal",
                guard_runner=guard_runner,
            )

            pipeline = executor.load_pipeline()
            self.assertEqual(rc, 0)
            self.assertEqual(pipeline.state, "commit_recorded")
            self.assertTrue(pipeline.commit_sha)

    def test_commit_allows_governed_checkpoint_when_new_implementation_is_blocked(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            _run_git(repo_root, "add", "tracked.txt")
            guard_runner = MagicMock(return_value=_mock_subprocess_result(0))

            def _startup_context_fn(*, repo_root: Path):
                del repo_root
                return SimpleNamespace(
                    implementation_permission="blocked",
                    observed_control_topology="no_live_agents",
                    advisory_action="checkpoint_allowed",
                    reviewer_gate=SimpleNamespace(
                        implementation_blocked=False,
                        implementation_block_reason="",
                        checkpoint_permitted=True,
                        review_gate_allows_push=True,
                    ),
                    governance=SimpleNamespace(
                        push_enforcement=SimpleNamespace(
                            checkpoint_required=False,
                            safe_to_continue_editing=True,
                        )
                    ),
                    push_decision=SimpleNamespace(
                        action="await_checkpoint",
                        reason="staged_index_present",
                    ),
                )

            executor = GovernedVcsExecutor(
                repo_root=repo_root,
                review_channel_path=repo_root / "dev/active/review_channel.md",
                push_policy=_push_policy(),
                startup_context_fn=_startup_context_fn,
                refresh_projections=True,
            )

            rc = run_commit(
                _make_args(message="feat: governed checkpoint commit"),
                repo_root=repo_root,
                policy=_push_policy(),
                executor=executor,
                interaction_mode="local_terminal",
                guard_runner=guard_runner,
            )

            pipeline = executor.load_pipeline()
            self.assertEqual(rc, 0)
            self.assertEqual(pipeline.state, "commit_recorded")
            self.assertTrue(pipeline.commit_sha)
            self.assertEqual(
                _run_git(repo_root, "log", "-1", "--pretty=%s"),
                "feat: governed checkpoint commit",
            )

    def test_commit_allows_governed_checkpoint_when_reviewer_runtime_is_suspended(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            _run_git(repo_root, "add", "tracked.txt")
            guard_runner = MagicMock(return_value=_mock_subprocess_result(0))

            def _startup_context_fn(*, repo_root: Path):
                del repo_root
                return SimpleNamespace(
                    implementation_permission="suspended",
                    observed_control_topology="implementer_without_reviewer",
                    advisory_action="checkpoint_before_continue",
                    reviewer_gate=SimpleNamespace(
                        implementation_blocked=True,
                        implementation_block_reason="runtime_missing",
                        checkpoint_permitted=True,
                        review_gate_allows_push=False,
                    ),
                    governance=SimpleNamespace(
                        push_enforcement=SimpleNamespace(
                            checkpoint_required=True,
                            safe_to_continue_editing=False,
                        )
                    ),
                    push_decision=SimpleNamespace(
                        action="await_checkpoint",
                        reason="staged_index_budget_exceeded",
                    ),
                )

            executor = GovernedVcsExecutor(
                repo_root=repo_root,
                review_channel_path=repo_root / "dev/active/review_channel.md",
                push_policy=_push_policy(),
                startup_context_fn=_startup_context_fn,
                refresh_projections=True,
            )
            executor._persist_pipeline(
                RemoteCommitPipelineContract(
                    pipeline_id="pipeline-old",
                    state="push_pending",
                    branch=_run_git(repo_root, "rev-parse", "--abbrev-ref", "HEAD"),
                    commit_sha="old-sha",
                )
            )

            rc = run_commit(
                _make_args(message="feat: recovery checkpoint commit"),
                repo_root=repo_root,
                policy=_push_policy(),
                executor=executor,
                interaction_mode="local_terminal",
                guard_runner=guard_runner,
            )

            pipeline = executor.load_pipeline()
            self.assertEqual(rc, 0)
            self.assertEqual(pipeline.state, "commit_recorded")
            self.assertTrue(pipeline.commit_sha)
            self.assertEqual(
                _run_git(repo_root, "log", "-1", "--pretty=%s"),
                "feat: recovery checkpoint commit",
            )

    def test_commit_blocks_when_implementation_permission_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            _run_git(repo_root, "add", "tracked.txt")
            guard_runner = MagicMock(return_value=_mock_subprocess_result(0))

            def _startup_context_fn(*, repo_root: Path):
                del repo_root
                return SimpleNamespace(
                    implementation_permission="blocked",
                    observed_control_topology="no_live_agents",
                    reviewer_gate=SimpleNamespace(
                        implementation_blocked=False,
                        implementation_block_reason="",
                        review_gate_allows_push=True,
                    ),
                    governance=SimpleNamespace(
                        push_enforcement=SimpleNamespace(
                            checkpoint_required=False,
                            safe_to_continue_editing=True,
                        )
                    ),
                )

            executor = GovernedVcsExecutor(
                repo_root=repo_root,
                review_channel_path=repo_root / "dev/active/review_channel.md",
                push_policy=_push_policy(),
                startup_context_fn=_startup_context_fn,
                refresh_projections=True,
            )

            rc = run_commit(
                _make_args(message="feat: blocked commit"),
                repo_root=repo_root,
                policy=_push_policy(),
                executor=executor,
                interaction_mode="local_terminal",
                guard_runner=guard_runner,
            )

            pipeline = executor.load_pipeline()
            self.assertEqual(rc, 1)
            self.assertFalse(pipeline.pipeline_id)
            guard_runner.assert_not_called()

    def test_commit_auto_approves_and_records_commit_in_local_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            _run_git(repo_root, "add", "tracked.txt")
            guard_runner = MagicMock(return_value=_mock_subprocess_result(0))

            rc = run_commit(
                _make_args(message="feat: governed local commit"),
                repo_root=repo_root,
                policy=_push_policy(),
                executor=_executor(repo_root),
                interaction_mode="local_terminal",
                guard_runner=guard_runner,
            )

            pipeline = _executor(repo_root).load_pipeline()
            self.assertEqual(rc, 0)
            self.assertEqual(pipeline.state, "commit_recorded")
            self.assertTrue(pipeline.commit_sha)
            self.assertEqual(
                _run_git(repo_root, "log", "-1", "--pretty=%s"),
                "feat: governed local commit",
            )

    def test_commit_remote_mode_auto_approves_for_active_operator_delegate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            _persist_remote_operator_attachment(repo_root)
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            _run_git(repo_root, "add", "tracked.txt")
            guard_runner = MagicMock(return_value=_mock_subprocess_result(0))

            rc = run_commit(
                _make_args(message="feat: delegated remote-control commit"),
                repo_root=repo_root,
                policy=_push_policy(),
                executor=_executor(repo_root),
                interaction_mode="remote_control",
                guard_runner=guard_runner,
            )

            executor = _executor(repo_root)
            pipeline = executor.load_pipeline()
            packets = {packet.packet_id: packet for packet in executor._event_packets()}
            self.assertEqual(rc, 0)
            self.assertEqual(pipeline.state, "commit_recorded")
            self.assertEqual(pipeline.approval_state, "approved")
            self.assertEqual(packets[pipeline.approval_packet_id].to_agent, "claude")
            self.assertEqual(packets[pipeline.decision_packet_id].from_agent, "claude")
            self.assertIn(
                "remote-control operator delegate `claude`",
                packets[pipeline.decision_packet_id].body,
            )
            self.assertEqual(
                _run_git(repo_root, "log", "-1", "--pretty=%s"),
                "feat: delegated remote-control commit",
            )

    def test_commit_remote_mode_without_operator_delegate_waits_for_typed_approval(
        self,
    ) -> None:
        """Remote-control stays fail-closed when typed operator delegation is absent.

        The governed commit path should only auto-satisfy approval when typed
        runtime evidence proves that the remote-control lane already delegates
        operator authority to a live agent. A bare ``interaction_mode`` string
        is not sufficient on its own.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            _run_git(repo_root, "add", "tracked.txt")
            guard_runner = MagicMock(return_value=_mock_subprocess_result(0))

            rc = run_commit(
                _make_args(message="feat: wait for remote approval"),
                repo_root=repo_root,
                policy=_push_policy(),
                executor=_executor(repo_root),
                interaction_mode="remote_control",
                guard_runner=guard_runner,
            )

            pipeline = _executor(repo_root).load_pipeline()
            self.assertEqual(rc, 1)
            self.assertEqual(pipeline.state, "operator_approval_pending")
            self.assertEqual(pipeline.approval_state, "pending")

    def test_commit_unresolved_mode_does_not_auto_approve(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            _run_git(repo_root, "add", "tracked.txt")
            guard_runner = MagicMock(return_value=_mock_subprocess_result(0))

            rc = run_commit(
                _make_args(message="feat: require typed approval"),
                repo_root=repo_root,
                policy=_push_policy(),
                executor=_executor(repo_root),
                interaction_mode="unresolved",
                guard_runner=guard_runner,
            )

            pipeline = _executor(repo_root).load_pipeline()
            self.assertEqual(rc, 1)
            self.assertEqual(pipeline.state, "operator_approval_pending")
            self.assertEqual(pipeline.approval_state, "pending")

    def test_commit_stops_before_commit_phase_while_remote_approval_is_pending(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            executor = _executor(repo_root)
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            _run_git(repo_root, "add", "tracked.txt")

            stage_result = executor.execute(
                build_stage_action(
                    repo_pack_id=_push_policy().repo_pack_id,
                    commit_message_draft="feat: wait for remote approval",
                    push_requested=False,
                    guard_profile="quick",
                    work_intake_ref="devctl.commit",
                    reuse_staged_index=True,
                    requested_by="devctl.commit",
                )
            )
            self.assertTrue(stage_result.ok)
            guarded_pipeline = executor.record_guard_result(guard_result(0))
            pending_packet = ReviewPacketState(
                packet_id="rev_pkt_request",
                kind=APPROVAL_PACKET_KIND,
                from_agent="system",
                to_agent="operator",
                summary="Approve governed commit pipeline",
                body="Operator approval is required before the governed executor may commit.",
                status="pending",
                policy_hint="operator_approval_required",
                requested_action="approve_commit_pipeline",
                approval_required=True,
                posted_at="2026-04-15T17:45:00Z",
                target_kind="runtime",
                target_ref=pipeline_target_ref(guarded_pipeline),
                target_revision=guarded_pipeline.generation_id,
                pipeline_generation=guarded_pipeline.generation_id,
                staged_snapshot_hash=guarded_pipeline.intent.staged_tree_hash,
            )
            executor._persist_pipeline(
                replace(
                    guarded_pipeline,
                    approval_packet_id=pending_packet.packet_id,
                    approval_state="pending",
                    blocked_reason="",
                )
            )

            with (
                patch.object(
                    GovernedVcsExecutor,
                    "_event_packets",
                    return_value=(pending_packet,),
                ),
                patch(
                    "dev.scripts.devctl.commands.vcs.commit.build_commit_action",
                    side_effect=AssertionError(
                        "commit action should not be built before approval"
                    ),
                ),
            ):
                rc = run_commit(
                    _make_args(message="feat: wait for remote approval"),
                    repo_root=repo_root,
                    policy=_push_policy(),
                    executor=executor,
                    interaction_mode="unresolved",
                    guard_runner=MagicMock(return_value=_mock_subprocess_result(0)),
                )

            pipeline = executor.load_pipeline()
            self.assertEqual(rc, 1)
            self.assertEqual(pipeline.state, "operator_approval_pending")
            self.assertEqual(pipeline.approval_state, "pending")

    def test_commit_reuses_approved_pipeline_without_rerunning_guards(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            executor = _executor(repo_root)
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            _run_git(repo_root, "add", "tracked.txt")
            first_guard = MagicMock(return_value=_mock_subprocess_result(0))

            first_rc = run_commit(
                _make_args(message="feat: request remote approval"),
                repo_root=repo_root,
                policy=_push_policy(),
                executor=executor,
                interaction_mode="unresolved",
                guard_runner=first_guard,
            )
            self.assertEqual(first_rc, 1)
            pipeline = executor.load_pipeline()
            artifact_paths = resolve_artifact_paths(repo_root=repo_root)
            _, decision_event = post_packet(
                repo_root=repo_root,
                review_channel_path=repo_root / "dev/active/review_channel.md",
                artifact_paths=artifact_paths,
                request=build_commit_approval_decision(
                    pipeline,
                    summary="Remote operator approved the governed commit.",
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
                    guard_attestation=build_commit_approval_attestation(
                        decision_event["packet_id"],
                        pipeline,
                    ),
                ),
            )

            second_guard = MagicMock(return_value=_mock_subprocess_result(0))
            second_rc = run_commit(
                _make_args(message="feat: request remote approval"),
                repo_root=repo_root,
                policy=_push_policy(),
                executor=executor,
                interaction_mode="unresolved",
                guard_runner=second_guard,
            )

            committed_pipeline = executor.load_pipeline()
            self.assertEqual(second_rc, 0)
            self.assertEqual(committed_pipeline.state, "commit_recorded")
            second_guard.assert_not_called()

    def test_commit_approve_pending_resumes_remote_pipeline_without_manual_packets(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            executor = _executor(repo_root)
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            _run_git(repo_root, "add", "tracked.txt")

            first_guard = MagicMock(return_value=_mock_subprocess_result(0))
            first_rc = run_commit(
                _make_args(message="feat: explicit operator approval"),
                repo_root=repo_root,
                policy=_push_policy(),
                executor=executor,
                interaction_mode="remote_control",
                guard_runner=first_guard,
            )
            self.assertEqual(first_rc, 1)

            second_guard = MagicMock(return_value=_mock_subprocess_result(0))
            second_rc = run_commit(
                _make_args(message=None, approve_pending=True),
                repo_root=repo_root,
                policy=_push_policy(),
                executor=executor,
                interaction_mode="remote_control",
                guard_runner=second_guard,
            )

            committed_pipeline = executor.load_pipeline()
            self.assertEqual(second_rc, 0)
            self.assertEqual(committed_pipeline.state, "commit_recorded")
            self.assertEqual(committed_pipeline.approval_state, "approved")
            self.assertTrue(committed_pipeline.decision_packet_id)
            self.assertEqual(
                _run_git(repo_root, "log", "-1", "--pretty=%s"),
                "feat: explicit operator approval",
            )
            second_guard.assert_not_called()

    def test_commit_remote_mode_reports_explicit_pending_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            executor = _executor(repo_root)
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            _run_git(repo_root, "add", "tracked.txt")
            captured: dict[str, object] = {}

            with patch(
                "dev.scripts.devctl.commands.vcs.commit._emit_report",
                side_effect=lambda _args, report: captured.update(report),
            ):
                rc = run_commit(
                    _make_args(message="feat: explicit operator approval"),
                    repo_root=repo_root,
                    policy=_push_policy(),
                    executor=executor,
                    interaction_mode="remote_control",
                    guard_runner=MagicMock(return_value=_mock_subprocess_result(0)),
                )

            self.assertEqual(rc, 1)
            self.assertEqual(captured["reason"], "operator_approval_missing")
            self.assertEqual(captured["commit_phase"], "awaiting_operator_approval")
            self.assertEqual(
                captured["commit_progress"],
                "guarded_pipeline_waiting_for_operator_approval",
            )
            self.assertEqual(captured["requested_action"], "approve_commit_pipeline")
            self.assertEqual(
                captured["next_command"],
                "python3 dev/scripts/devctl.py review-channel --action operator-inbox "
                "--status pending --terminal none --format json",
            )
            self.assertTrue(captured["approval_request_packet_id"])
            self.assertTrue(captured["pipeline_pending"])

    def test_commit_permission_report_projects_typed_next_command(self) -> None:
        decision = CommitPermissionDecision(
            commit_permission="blocked",
            blockers=("review_authority_stale",),
            next_command=(
                "python3 dev/scripts/devctl.py review-channel --action status "
                "--terminal none --format json"
            ),
            allowed_actions=("startup-context.summary",),
            blocked_actions=("vcs.stage", "vcs.commit"),
            recovery_action="refresh_startup_or_review_status",
            escalation_action="operator_resync_required",
        )

        with patch(
            "dev.scripts.devctl.commands.vcs.commit.build_commit_permission_decision_for_executor",
            return_value=(decision, ""),
        ):
            report = _commit_permission_report(MagicMock())

        assert report is not None
        self.assertEqual(report["reason"], "commit_permission_blocked")
        self.assertEqual(report["next_command"], decision.next_command)
        self.assertEqual(
            report["operator_guidance"],
            f"Run `{decision.next_command}` before staging or committing.",
        )
        self.assertEqual(report["recovery_action"], "refresh_startup_or_review_status")
        self.assertEqual(report["escalation_action"], "operator_resync_required")

    def test_apply_explicit_operator_approval_persists_synced_pipeline_state(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            executor = _executor(repo_root)
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            _run_git(repo_root, "add", "tracked.txt")

            first_rc = run_commit(
                _make_args(message="feat: explicit operator approval"),
                repo_root=repo_root,
                policy=_push_policy(),
                executor=executor,
                interaction_mode="remote_control",
                guard_runner=MagicMock(return_value=_mock_subprocess_result(0)),
            )
            self.assertEqual(first_rc, 1)

            pipeline = executor.load_pipeline()
            artifact_paths = resolve_artifact_paths(repo_root=repo_root)
            _, decision_event = post_packet(
                repo_root=repo_root,
                review_channel_path=repo_root / "dev/active/review_channel.md",
                artifact_paths=artifact_paths,
                request=build_commit_approval_decision(
                    pipeline,
                    summary="Remote operator approved the governed commit.",
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
                    guard_attestation=build_commit_approval_attestation(
                        decision_event["packet_id"],
                        pipeline,
                    ),
                ),
            )

            approved_pipeline, report = apply_explicit_operator_approval(
                vcs_executor=executor,
                pipeline=executor.load_pipeline(),
                approval_authority=build_commit_approval_authority(
                    interaction_mode="remote_control",
                ),
                stage_warnings=[],
            )

            self.assertIsNone(report)
            self.assertEqual(approved_pipeline.approval_state, "approved")
            persisted = executor.load_pipeline()
            self.assertEqual(persisted.approval_state, "approved")
            self.assertEqual(persisted.decision_packet_id, decision_event["packet_id"])

    def test_explicit_operator_approval_records_guard_attestation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            executor = _executor(repo_root)
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            _run_git(repo_root, "add", "tracked.txt")

            first_rc = run_commit(
                _make_args(message="feat: explicit operator approval"),
                repo_root=repo_root,
                policy=_push_policy(),
                executor=executor,
                interaction_mode="remote_control",
                guard_runner=MagicMock(return_value=_mock_subprocess_result(0)),
            )
            self.assertEqual(first_rc, 1)

            pipeline = executor.load_pipeline()
            approved_pipeline, report = apply_explicit_operator_approval(
                vcs_executor=executor,
                pipeline=pipeline,
                approval_authority=build_commit_approval_authority(
                    interaction_mode="remote_control",
                ),
                stage_warnings=[],
            )

            self.assertIsNone(report)
            self.assertEqual(approved_pipeline.approval_state, "approved")
            persisted = executor.load_pipeline()
            self.assertEqual(persisted.approval_state, "approved")
            self.assertTrue(persisted.decision_packet_id)

            artifact_paths = resolve_artifact_paths(repo_root=repo_root)
            events = load_events(Path(artifact_paths.event_log_path))
            apply_events = [
                event
                for event in events
                if event.get("event_type") == "packet_applied"
                and event.get("kind") == APPROVAL_PACKET_KIND
                and event.get("trace_id") == pipeline.pipeline_id
            ]
            self.assertEqual(len(apply_events), 2)
            for event in apply_events:
                metadata = event.get("metadata")
                if not isinstance(metadata, dict):
                    self.fail("packet_applied metadata must be a dict")
                attestation = metadata.get("guard_attestation")
                self.assertIsInstance(attestation, dict)
                self.assertEqual(attestation["contract_id"], "PacketGuardAttestation")
                self.assertEqual(attestation["packet_id"], event["packet_id"])
                self.assertEqual(
                    attestation["pipeline_generation"],
                    pipeline.generation_id,
                )
                self.assertEqual(
                    attestation["staged_snapshot_hash"],
                    pipeline.intent.staged_tree_hash,
                )
                self.assertEqual(attestation["attested_by"], metadata["actor"])
                self.assertTrue(attestation["run_record_ids"])
                self.assertTrue(attestation["operator_signature"])

    def test_explicit_operator_approval_reuses_existing_decision_packet(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            executor = _executor(repo_root)
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            _run_git(repo_root, "add", "tracked.txt")

            first_rc = run_commit(
                _make_args(message="feat: explicit operator approval"),
                repo_root=repo_root,
                policy=_push_policy(),
                executor=executor,
                interaction_mode="remote_control",
                guard_runner=MagicMock(return_value=_mock_subprocess_result(0)),
            )
            self.assertEqual(first_rc, 1)

            pipeline = executor.load_pipeline()
            artifact_paths = resolve_artifact_paths(repo_root=repo_root)
            _, decision_event = post_packet(
                repo_root=repo_root,
                review_channel_path=repo_root / "dev/active/review_channel.md",
                artifact_paths=artifact_paths,
                request=build_commit_approval_decision(
                    pipeline,
                    summary=(
                        "Remote-control operator approved governed commit "
                        f"pipeline `{pipeline.pipeline_id}`"
                    ),
                    body=(
                        "The remote-control operator explicitly approved the "
                        "current guarded staged snapshot for governed commit "
                        "execution."
                    ),
                ),
            )

            approved_pipeline, report = apply_explicit_operator_approval(
                vcs_executor=executor,
                pipeline=pipeline,
                approval_authority=build_commit_approval_authority(
                    interaction_mode="remote_control",
                ),
                stage_warnings=[],
            )

            self.assertIsNone(report)
            self.assertEqual(approved_pipeline.approval_state, "approved")
            persisted = executor.load_pipeline()
            self.assertEqual(persisted.decision_packet_id, decision_event["packet_id"])

            events = load_events(Path(artifact_paths.event_log_path))
            decision_posts = [
                event
                for event in events
                if event.get("event_type") == "packet_posted"
                and event.get("kind") == APPROVAL_PACKET_KIND
                and event.get("trace_id") == pipeline.pipeline_id
                and not event.get("approval_required")
            ]
            self.assertEqual(len(decision_posts), 1)

    def test_commit_approve_pending_is_idempotent_for_commit_pending_pipeline(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            executor = _executor(repo_root)
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            _run_git(repo_root, "add", "tracked.txt")

            first_rc = run_commit(
                _make_args(message="feat: explicit operator approval"),
                repo_root=repo_root,
                policy=_push_policy(),
                executor=executor,
                interaction_mode="remote_control",
                guard_runner=MagicMock(return_value=_mock_subprocess_result(0)),
            )
            self.assertEqual(first_rc, 1)

            pipeline = executor.load_pipeline()
            artifact_paths = resolve_artifact_paths(repo_root=repo_root)
            _, decision_event = post_packet(
                repo_root=repo_root,
                review_channel_path=repo_root / "dev/active/review_channel.md",
                artifact_paths=artifact_paths,
                request=build_commit_approval_decision(
                    pipeline,
                    summary="Remote operator approved the governed commit.",
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
                    guard_attestation=build_commit_approval_attestation(
                        decision_event["packet_id"],
                        pipeline,
                    ),
                ),
            )
            executor._persist_pipeline(
                replace(
                    executor.load_pipeline(),
                    state="commit_pending",
                    approval_state="approved",
                    decision_packet_id=str(decision_event["packet_id"]),
                )
            )

            second_rc = run_commit(
                _make_args(message=None, approve_pending=True),
                repo_root=repo_root,
                policy=_push_policy(),
                executor=executor,
                interaction_mode="remote_control",
                guard_runner=MagicMock(return_value=_mock_subprocess_result(0)),
            )

            committed_pipeline = executor.load_pipeline()
            self.assertEqual(second_rc, 0)
            self.assertEqual(committed_pipeline.state, "commit_recorded")
            self.assertEqual(committed_pipeline.approval_state, "approved")

    def test_commit_approve_pending_requires_existing_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            executor = _executor(repo_root)

            rc = run_commit(
                _make_args(message=None, approve_pending=True),
                repo_root=repo_root,
                policy=_push_policy(),
                executor=executor,
                interaction_mode="remote_control",
                guard_runner=MagicMock(return_value=_mock_subprocess_result(0)),
            )

            pipeline = executor.load_pipeline()
            self.assertEqual(rc, 1)
            self.assertFalse(pipeline.pipeline_id)

    def test_commit_replays_guards_when_approved_pipeline_loses_validation_receipt(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            executor = _executor(repo_root)
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            _run_git(repo_root, "add", "tracked.txt")
            stage_result = executor.execute(
                build_stage_action(
                    repo_pack_id=_push_policy().repo_pack_id,
                    commit_message_draft="feat: replay missing validation receipt",
                    push_requested=False,
                    guard_profile="quick",
                    work_intake_ref="devctl.commit",
                    reuse_staged_index=True,
                    requested_by="devctl.commit",
                )
            )
            self.assertTrue(stage_result.ok)
            staged_pipeline = executor.record_guard_result(guard_result(0))
            request_packet = ReviewPacketState(
                packet_id="rev_pkt_request",
                kind=APPROVAL_PACKET_KIND,
                from_agent="system",
                to_agent="operator",
                summary="Approve governed commit pipeline",
                body="Operator approval is required before the governed executor may commit.",
                status="pending",
                policy_hint="operator_approval_required",
                requested_action="approve_commit_pipeline",
                approval_required=True,
                posted_at="2026-04-15T16:40:00Z",
                target_kind="runtime",
                target_ref=pipeline_target_ref(staged_pipeline),
                target_revision=staged_pipeline.generation_id,
                pipeline_generation=staged_pipeline.generation_id,
                staged_snapshot_hash=staged_pipeline.intent.staged_tree_hash,
            )
            decision_packet = ReviewPacketState(
                packet_id="rev_pkt_decision",
                kind=APPROVAL_PACKET_KIND,
                from_agent="operator",
                to_agent="system",
                summary="Remote operator approved the governed commit.",
                body="Operator approved the guarded staged snapshot.",
                status="applied",
                policy_hint="operator_approval_required",
                requested_action="approve_commit_pipeline",
                approval_required=False,
                posted_at="2026-04-15T16:41:00Z",
                target_kind="runtime",
                target_ref=pipeline_target_ref(staged_pipeline),
                target_revision=staged_pipeline.generation_id,
                pipeline_generation=staged_pipeline.generation_id,
                staged_snapshot_hash=staged_pipeline.intent.staged_tree_hash,
                applied_at_utc="2026-04-15T16:41:30Z",
            )
            executor._persist_pipeline(
                replace(
                    staged_pipeline,
                    state="approved",
                    approval_state="approved",
                    approval_packet_id=request_packet.packet_id,
                    decision_packet_id=decision_packet.packet_id,
                    validation_receipt=None,
                    blocked_reason="",
                    attention_revision_lease="",
                )
            )

            replay_guard = MagicMock(return_value=_mock_subprocess_result(0))
            with (
                patch.object(
                    GovernedVcsExecutor,
                    "_event_packets",
                    return_value=(request_packet, decision_packet),
                ),
                patch(
                    "dev.scripts.devctl.commands.vcs.governed_executor_commit_phase.check_commit_packet_gate",
                    return_value=None,
                ),
            ):
                second_rc = run_commit(
                    _make_args(message="feat: replay missing validation receipt"),
                    repo_root=repo_root,
                    policy=_push_policy(),
                    executor=executor,
                    interaction_mode="unresolved",
                    guard_runner=replay_guard,
                )

            committed_pipeline = executor.load_pipeline()
            self.assertEqual(second_rc, 0)
            self.assertEqual(committed_pipeline.state, "commit_recorded")
            self.assertIsNotNone(committed_pipeline.validation_receipt)
            replay_guard.assert_called_once()

    def test_commit_refreshes_snapshot_before_remote_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = _init_repo(Path(tmpdir) / "repo")
            executor = _executor(repo_root)
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            _run_git(repo_root, "add", "tracked.txt")
            first_guard = MagicMock(return_value=_mock_subprocess_result(0))

            def _refresh_before_stage(
                *,
                repo_root: Path,
                previous_head_sha: str = "",
            ) -> list[str]:
                del previous_head_sha
                snapshot_path = repo_root / "dev/audits/REVIEW_SNAPSHOT.md"
                snapshot_path.parent.mkdir(parents=True, exist_ok=True)
                snapshot_path.write_text(
                    "refreshed before approval\n",
                    encoding="utf-8",
                )
                _run_git(repo_root, "add", str(snapshot_path.relative_to(repo_root)))
                return []

            with patch(
                "dev.scripts.devctl.commands.vcs.governed_executor_phases.refresh_and_stage_review_snapshot",
                side_effect=_refresh_before_stage,
            ):
                first_rc = run_commit(
                    _make_args(message="feat: request remote approval"),
                    repo_root=repo_root,
                    policy=_push_policy(),
                    executor=executor,
                    interaction_mode="unresolved",
                    guard_runner=first_guard,
                )

            self.assertEqual(first_rc, 1)
            pipeline = executor.load_pipeline()
            self.assertEqual(
                pipeline.intent.staged_tree_hash,
                _run_git(repo_root, "write-tree"),
            )
            artifact_paths = resolve_artifact_paths(repo_root=repo_root)
            _, decision_event = post_packet(
                repo_root=repo_root,
                review_channel_path=repo_root / "dev/active/review_channel.md",
                artifact_paths=artifact_paths,
                request=build_commit_approval_decision(
                    pipeline,
                    summary="Remote operator approved the governed commit.",
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
                    guard_attestation=build_commit_approval_attestation(
                        decision_event["packet_id"],
                        pipeline,
                    ),
                ),
            )

            second_rc = run_commit(
                _make_args(message="feat: request remote approval"),
                repo_root=repo_root,
                policy=_push_policy(),
                executor=executor,
                interaction_mode="unresolved",
                guard_runner=MagicMock(return_value=_mock_subprocess_result(0)),
            )

            committed_pipeline = executor.load_pipeline()
            self.assertEqual(second_rc, 0)
            self.assertEqual(committed_pipeline.state, "commit_recorded")
            self.assertTrue(committed_pipeline.commit_sha)


class TestCommitParserEndToEnd(unittest.TestCase):
    def test_parser_accepts_role(self) -> None:
        import argparse

        from dev.scripts.devctl.sync_parser import add_commit_parser

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        add_commit_parser(sub)
        args = parser.parse_args(["commit", "--role", "dashboard", "-m", "test"])
        self.assertEqual(args.role, "dashboard")

    def test_parser_accepts_option_passthrough_with_separator(self) -> None:
        import argparse

        from dev.scripts.devctl.sync_parser import add_commit_parser

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        add_commit_parser(sub)
        args = parser.parse_args(["commit", "-m", "test", "--", "--allow-empty"])
        self.assertEqual(args.message, "test")
        self.assertIn("--allow-empty", args.passthrough)

    def test_parser_accepts_plain_passthrough(self) -> None:
        import argparse

        from dev.scripts.devctl.sync_parser import add_commit_parser

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        add_commit_parser(sub)
        args = parser.parse_args(["commit", "-m", "test", "--", "file.py"])
        self.assertEqual(args.message, "test")
        self.assertIn("file.py", args.passthrough)


if __name__ == "__main__":
    unittest.main()
