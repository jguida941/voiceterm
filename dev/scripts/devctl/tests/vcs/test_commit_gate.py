"""Tests for the governed commit gate and typed commit pipeline."""

from __future__ import annotations

import importlib
import os
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands.governance import startup_context as startup_context_command
from dev.scripts.devctl.commands.vcs.commit import (
    _build_git_commit_cmd,
    _pipeline_has_checkpoint_snapshot,
    _pipeline_has_validation_plan,
    _resolve_interaction_mode,
    _run_guard_bundle,
    run_commit,
)
from dev.scripts.devctl.commands.vcs.governed_executor import GovernedVcsExecutor
from dev.scripts.devctl.commands.vcs.governed_executor_packets import (
    build_commit_approval_decision,
)
from dev.scripts.devctl.config import REPO_ROOT
from dev.scripts.devctl.governance.push_policy import (
    PushBypassPolicy,
    PushCheckpointPolicy,
    PushPolicy,
    PushPostPushPolicy,
    PushPreflightPolicy,
    PushPublicationPolicy,
)
from dev.scripts.devctl.tests.vcs._git_helpers import _run_git
from dev.scripts.devctl.review_channel.events import (
    post_packet,
    resolve_artifact_paths,
    transition_packet,
)
from dev.scripts.devctl.review_channel.packet_contract import PacketTransitionRequest
from dev.scripts.devctl.platform.coordination_snapshot_models import (
    CoordinationActorRecord,
    CoordinationSnapshot,
)
from dev.scripts.devctl.runtime.startup_context import ReviewerGateState, StartupContext
from dev.scripts.devctl.runtime.validation_contracts import ValidationPlan
from dev.scripts.devctl.runtime.work_intake_models import (
    WorkIntakeCoordinationState,
    WorkIntakePacket,
)


def _make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "message": "test commit",
        "amend": False,
        "role": None,
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
            compatibility_projection_paths=("dev/reports/push/latest.json",)
        ),
        publication=PushPublicationPolicy(),
    )


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


def _capture_startup_context_payload(
    ctx: StartupContext,
    argv: list[str],
) -> tuple[int, dict[str, object]]:
    args = build_parser().parse_args(argv)
    captured: dict[str, object] = {}

    def _fake_emit(*_args, **kwargs):
        captured.update(kwargs["json_payload"])
        return 0

    with patch.object(
        startup_context_command,
        "build_startup_context",
        return_value=ctx,
    ), patch.object(
        startup_context_command,
        "build_startup_authority_report",
        return_value={
            "ok": True,
            "checks_run": 10,
            "checks_passed": 10,
            "errors": [],
            "warnings": [],
        },
    ), patch.object(
        startup_context_command,
        "write_startup_receipt",
        return_value=Path("/tmp/startup-receipt.json"),
    ), patch.object(
        startup_context_command,
        "emit_machine_artifact_output",
        side_effect=_fake_emit,
    ):
        rc = startup_context_command.run(args)

    return rc, captured


class TestStartupActionRouting(unittest.TestCase):
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
        self.assertIn("vcs.stage", captured["blocked_actions"])
        self.assertIn("vcs.commit", captured["blocked_actions"])
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


class TestPreCommitHookTemplate(unittest.TestCase):
    HOOK_PATH = REPO_ROOT / "dev/config/templates/portable_governance_pre_commit_hook.sh"

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
        self.assertEqual(_build_git_commit_cmd(args), ["git", "commit", "-m", "fix: resolve bug"])

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
        self.assertFalse(_pipeline_has_validation_plan(SimpleNamespace(intent=SimpleNamespace(validation_plan=None))))

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
        with patch(
            "dev.scripts.devctl.commands.vcs.commit.scan_repo_governance_safely",
            return_value=governance,
        ) as scan_mock, patch(
            "dev.scripts.devctl.commands.vcs.commit.build_control_plane_read_model",
            return_value=SimpleNamespace(operator_interaction_mode="single_agent"),
        ) as build_model_mock:
            self.assertEqual(_resolve_interaction_mode(repo_root), "single_agent")

        scan_mock.assert_called_once_with(repo_root)
        build_model_mock.assert_called_once_with(repo_root, governance=governance)


class TestGovernedCommitPipeline(unittest.TestCase):
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
                    _make_args(message="feat: blocked dashboard commit", role="dashboard"),
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

    def test_commit_remote_mode_waits_for_typed_approval(self) -> None:
        """F1 regression: remote_control must not self-approve.

        When the operator is on remote control the local terminal cannot
        authoritatively speak for them, so the governed commit path must
        leave the pipeline in ``operator_approval_pending`` until a typed
        approval or action-request packet is applied by the off-box
        operator. Only ``local_terminal`` and ``single_agent`` self-
        approve. Collapsing this boundary was F1 in the Codex review.
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
        from dev.scripts.devctl.sync_parser import add_commit_parser
        import argparse

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        add_commit_parser(sub)
        args = parser.parse_args(["commit", "--role", "dashboard", "-m", "test"])
        self.assertEqual(args.role, "dashboard")

    def test_parser_accepts_option_passthrough_with_separator(self) -> None:
        from dev.scripts.devctl.sync_parser import add_commit_parser
        import argparse

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        add_commit_parser(sub)
        args = parser.parse_args(["commit", "-m", "test", "--", "--allow-empty"])
        self.assertEqual(args.message, "test")
        self.assertIn("--allow-empty", args.passthrough)

    def test_parser_accepts_plain_passthrough(self) -> None:
        from dev.scripts.devctl.sync_parser import add_commit_parser
        import argparse

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        add_commit_parser(sub)
        args = parser.parse_args(["commit", "-m", "test", "--", "file.py"])
        self.assertEqual(args.message, "test")
        self.assertIn("file.py", args.passthrough)


if __name__ == "__main__":
    unittest.main()
