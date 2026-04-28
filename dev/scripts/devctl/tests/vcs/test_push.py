"""Tests for the policy-driven devctl push command."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands.vcs import (
    push,
    push_preflight_commit,
    push_preflight_projection,
    push_projection_receipt,
    push_projection_runtime_refresh,
    push_recovery_loop_handoff,
    push_recovery_loop_repair,
    push_render_surface_sync,
)
from dev.scripts.devctl.commands.vcs.governed_executor_push_result import (
    project_push_report,
)
from dev.scripts.devctl.commands.vcs.push_pipeline_state_sync import (
    sync_commit_pipeline_with_push_report,
)
from dev.scripts.devctl.governance.push_policy import (
    PushBypassPolicy,
    PushCheckpointPolicy,
    PushPolicy,
    PushPostPushPolicy,
    PushPreflightPolicy,
    PushPublicationPolicy,
    build_post_push_commands,
    detect_push_enforcement_state,
    load_push_policy,
)
from dev.scripts.checks.startup_authority_contract.runtime_checks import (
    collect_reviewer_loop_block_errors,
)
from dev.scripts.devctl.review_channel.event_store import resolve_artifact_paths
from dev.scripts.devctl.review_channel.events import post_packet
from dev.scripts.devctl.review_channel.packet_contract import (
    PacketGuardBundleEvidenceFields,
    PacketPostRequest,
    PacketTargetFields,
)
from dev.scripts.devctl.review_channel.remote_commit_pipeline_artifact import (
    load_remote_commit_pipeline_contract,
    persist_remote_commit_pipeline_contract,
)
from dev.scripts.devctl.runtime.remote_commit_pipeline_models import (
    RemoteCommitPipelineContract,
)
from dev.scripts.devctl.runtime.remote_commit_pipeline_state import (
    PUSH_FAILURE_CLASSIFICATION_DESTRUCTIVE,
    PUSH_FAILURE_CLASSIFICATION_NON_DESTRUCTIVE,
    STATE_DELIVERED_LOCALLY_PENDING_PUBLISH,
)
from dev.scripts.devctl.tests.test_review_channel_context_refs import (
    _review_channel_text,
)
from dev.scripts.devctl.tests.vcs._git_helpers import _run_git


def make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "remote": None,
        "quality_policy": None,
        "execute": False,
        "skip_preflight": False,
        "skip_post_push": False,
        "format": "json",
        "output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_policy(**overrides) -> PushPolicy:
    values = {
        "policy_path": "dev/config/devctl_repo_policy.json",
        "repo_pack_id": "voiceterm",
        "warnings": (),
        "default_remote": "origin",
        "development_branch": "develop",
        "release_branch": "master",
        "protected_branches": ("develop", "master"),
        "allowed_branch_prefixes": ("feature/", "fix/"),
        "preflight": PushPreflightPolicy(),
        "post_push": PushPostPushPolicy(),
        "bypass": PushBypassPolicy(),
        "checkpoint": PushCheckpointPolicy(),
        "publication": PushPublicationPolicy(),
    }
    values.update(overrides)
    return PushPolicy(
        policy_path=values["policy_path"],
        repo_pack_id=values["repo_pack_id"],
        warnings=values["warnings"],
        default_remote=values["default_remote"],
        development_branch=values["development_branch"],
        release_branch=values["release_branch"],
        protected_branches=values["protected_branches"],
        allowed_branch_prefixes=values["allowed_branch_prefixes"],
        preflight=values["preflight"],
        post_push=values["post_push"],
        bypass=values["bypass"],
        checkpoint=values["checkpoint"],
        publication=values["publication"],
    )


def _bridge_text_for_push_heartbeat(
    *,
    last_codex_poll: str,
    reviewer_mode: str = "active_dual_agent",
) -> str:
    return "\n".join(
        [
            "- Last Codex poll: `" + last_codex_poll + "`",
            "- Last Codex poll (Local America/New_York): " "`2026-04-27 14:00:00 EDT`",
            "- Last non-audit worktree hash: `reviewed-hash`",
            "- Reviewer mode: `" + reviewer_mode + "`",
            "- Current instruction revision: `rev-1`",
            "",
            "## Poll Status",
            "- reviewer-checkpoint reason=review-pass",
            "",
            "## Current Instruction For Claude",
            "- continue the governed push path",
            "",
            "## Claude Status",
            "- implemented the slice",
            "",
            "## Claude Ack",
            "- ack rev-1",
            "",
            "## Last Reviewed Scope",
            "- dev/scripts/devctl/commands/vcs/push_projection_runtime_refresh.py",
            "",
        ]
    )


def _publication_authorization(
    *,
    authorized: bool = True,
    reason: str = "push_authorization_current",
    summary: str = "Publication is authorized for the current HEAD.",
    approved_target_identity: str = "tree-receipt-20260403T010000Z:tree-123",
    authorization_id: str = "push-auth-20260403T010000Z",
    approval_mode: str = "commit_pipeline_approval",
    approved_at_utc: str = "",
) -> SimpleNamespace:
    resolved_approved_at_utc = approved_at_utc or datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")
    return SimpleNamespace(
        authorized=authorized,
        reason=reason,
        summary=summary,
        push_authorization=(
            SimpleNamespace(
                approved_target_identity=approved_target_identity,
                authorization_id=authorization_id,
                approval_mode=approval_mode,
                approved_at_utc=resolved_approved_at_utc,
            )
            if authorized
            else None
        ),
    )


class PushParserTests(unittest.TestCase):
    def test_cli_accepts_push_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "push",
                "--remote",
                "upstream",
                "--execute",
                "--skip-post-push",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "push")
        self.assertEqual(args.remote, "upstream")
        self.assertTrue(args.execute)
        self.assertTrue(args.skip_post_push)

    def test_repo_policy_disallows_skip_preflight_by_default(self) -> None:
        policy = load_push_policy()

        self.assertFalse(policy.bypass.allow_skip_preflight)
        self.assertFalse(policy.bypass.allow_skip_post_push)


class PushCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self._sync_bridge_patcher = patch(
            "dev.scripts.devctl.commands.vcs.push._sync_bridge_projection_before_preflight"
        )
        self.sync_bridge_mock = self._sync_bridge_patcher.start()
        self.addCleanup(self._sync_bridge_patcher.stop)
        self._preflight_status_patcher = patch(
            "dev.scripts.devctl.commands.vcs.push_preflight_commit.collect_git_status",
            return_value={"changes": []},
        )
        self.preflight_status_mock = self._preflight_status_patcher.start()
        self.addCleanup(self._preflight_status_patcher.stop)
        self._projection_receipt_patcher = patch(
            "dev.scripts.devctl.commands.vcs.push_preflight_projection.auto_commit_managed_projection_receipt"
        )
        self.projection_receipt_mock = self._projection_receipt_patcher.start()
        self.addCleanup(self._projection_receipt_patcher.stop)
        self._review_snapshot_refresh_patcher = patch(
            "dev.scripts.devctl.commands.vcs.push.refresh_managed_projections_before_preflight"
        )
        self.review_snapshot_refresh_mock = (
            self._review_snapshot_refresh_patcher.start()
        )
        self.addCleanup(self._review_snapshot_refresh_patcher.stop)
        self._progress_snapshot_patcher = patch(
            "dev.scripts.devctl.commands.vcs.push.persist_push_progress_snapshot",
            return_value="dev/reports/push/latest.json",
        )
        self.progress_snapshot_mock = self._progress_snapshot_patcher.start()
        self.addCleanup(self._progress_snapshot_patcher.stop)
        self._published_snapshot_patcher = patch(
            "dev.scripts.devctl.commands.vcs.push.persist_published_remote_snapshot",
            return_value="dev/reports/push/latest.json",
        )
        self.published_snapshot_mock = self._published_snapshot_patcher.start()
        self.addCleanup(self._published_snapshot_patcher.stop)
        self._head_commit_patcher = patch(
            "dev.scripts.devctl.commands.vcs.push.current_head_commit_sha",
            return_value="abc123",
        )
        self.head_commit_mock = self._head_commit_patcher.start()
        self.addCleanup(self._head_commit_patcher.stop)
        self._live_branch_patcher = patch(
            "dev.scripts.devctl.commands.vcs.push._live_current_branch",
            return_value="",
        )
        self.live_branch_mock = self._live_branch_patcher.start()
        self.addCleanup(self._live_branch_patcher.stop)
        self._push_flow_head_patcher = patch(
            "dev.scripts.devctl.commands.vcs.push_flow.current_head_commit_sha",
            return_value="abc123",
        )
        self.push_flow_head_mock = self._push_flow_head_patcher.start()
        self.addCleanup(self._push_flow_head_patcher.stop)
        self._push_flow_remote_head_patcher = patch(
            "dev.scripts.devctl.commands.vcs.push_flow._remote_head_sha",
            return_value="abc123",
        )
        self.push_flow_remote_head_mock = self._push_flow_remote_head_patcher.start()
        self.addCleanup(self._push_flow_remote_head_patcher.stop)

    @patch("dev.scripts.devctl.commands.vcs.push_executor_routing.emit_output")
    @patch(
        "dev.scripts.devctl.commands.vcs.push_executor_routing.load_latest_push_report"
    )
    @patch("dev.scripts.devctl.commands.vcs.push.remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    @patch("dev.scripts.devctl.commands.vcs.push.load_push_policy")
    @patch("dev.scripts.devctl.commands.vcs.governed_executor.GovernedVcsExecutor")
    def test_run_routes_pushable_pipeline_through_governed_executor(
        self,
        executor_cls_mock,
        load_push_policy_mock,
        collect_git_status_mock,
        _remote_exists_mock,
        load_latest_report_mock,
        emit_output_mock,
    ) -> None:
        fake_executor = MagicMock()
        fake_executor.load_pipeline.return_value = SimpleNamespace(
            pipeline_id="pipeline-123",
            state="commit_recorded",
            commit_sha="abc123",
            branch="feature/demo",
        )
        fake_executor.execute.return_value = SimpleNamespace(ok=True)
        executor_cls_mock.return_value = fake_executor
        load_push_policy_mock.return_value = make_policy()
        collect_git_status_mock.return_value = {"branch": "feature/demo", "changes": []}
        fresh_report = {
            "ok": True,
            "branch": "feature/demo",
            "head_commit": "abc123",
            "push_stages": {
                "published_remote": True,
                "post_push_green": True,
                "validation_ready": True,
            },
        }
        fake_executor.last_push_report = fresh_report
        load_latest_report_mock.return_value = fresh_report
        emit_output_mock.return_value = 0

        rc = push.run(make_args(execute=True, format="json"))

        self.assertEqual(rc, 0)
        fake_executor.execute.assert_called_once()
        emit_output_mock.assert_called_once()

    @patch(
        "dev.scripts.devctl.commands.vcs.push_pipeline_recovery.apply_refresh_authorization"
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push_pipeline_recovery.current_head_commit_sha",
        return_value="abc123",
    )
    @patch("dev.scripts.devctl.commands.vcs.push_executor_routing.emit_output")
    @patch(
        "dev.scripts.devctl.commands.vcs.push_executor_routing.load_latest_push_report"
    )
    @patch("dev.scripts.devctl.commands.vcs.push.remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    @patch("dev.scripts.devctl.commands.vcs.push.load_push_policy")
    @patch("dev.scripts.devctl.commands.vcs.governed_executor.GovernedVcsExecutor")
    def test_run_auto_refreshes_expired_same_head_pipeline_authorization(
        self,
        executor_cls_mock,
        load_push_policy_mock,
        collect_git_status_mock,
        _remote_exists_mock,
        load_latest_report_mock,
        emit_output_mock,
        _current_head_mock,
        apply_refresh_authorization_mock,
    ) -> None:
        expired_auth = SimpleNamespace(
            expires_at_utc="2000-01-01T00:00:00Z",
            authorized_head_sha="abc123",
        )
        refreshed_auth = SimpleNamespace(
            expires_at_utc="2999-01-01T00:00:00Z",
            authorized_head_sha="abc123",
        )
        fake_executor = MagicMock()
        fake_executor.load_pipeline.side_effect = [
            SimpleNamespace(
                pipeline_id="pipeline-123",
                state="push_blocked",
                commit_sha="abc123",
                branch="feature/demo",
                approved_target_identity="tree-receipt-20260403T010000Z:tree-123",
                push_authorization=expired_auth,
            ),
            SimpleNamespace(
                pipeline_id="pipeline-123",
                state="push_blocked",
                commit_sha="abc123",
                branch="feature/demo",
                approved_target_identity="tree-receipt-20260403T010000Z:tree-123",
                push_authorization=refreshed_auth,
            ),
        ]
        fake_executor.execute.return_value = SimpleNamespace(ok=True)
        executor_cls_mock.return_value = fake_executor
        load_push_policy_mock.return_value = make_policy()
        collect_git_status_mock.return_value = {"branch": "feature/demo", "changes": []}
        fresh_report = {
            "ok": True,
            "branch": "feature/demo",
            "head_commit": "abc123",
            "push_stages": {
                "published_remote": True,
                "post_push_green": True,
                "validation_ready": True,
            },
        }
        fake_executor.last_push_report = fresh_report
        load_latest_report_mock.return_value = fresh_report
        emit_output_mock.return_value = 0
        apply_refresh_authorization_mock.return_value = {"ok": True}

        rc = push.run(make_args(execute=True, format="json"))

        self.assertEqual(rc, 0)
        apply_refresh_authorization_mock.assert_called_once()
        fake_executor.execute.assert_called_once()

    @patch(
        "dev.scripts.devctl.commands.vcs.push_executor_routing.emit_output",
        return_value=7,
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push_executor_routing.load_latest_push_report"
    )
    @patch("dev.scripts.devctl.commands.vcs.push.remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    @patch("dev.scripts.devctl.commands.vcs.push.load_push_policy")
    @patch("dev.scripts.devctl.commands.vcs.governed_executor.GovernedVcsExecutor")
    def test_run_returns_emit_output_failure_for_executor_routed_push(
        self,
        executor_cls_mock,
        load_push_policy_mock,
        collect_git_status_mock,
        _remote_exists_mock,
        load_latest_report_mock,
        _emit_output_mock,
    ) -> None:
        fake_executor = MagicMock()
        fake_executor.load_pipeline.return_value = SimpleNamespace(
            pipeline_id="pipeline-123",
            state="commit_recorded",
            commit_sha="abc123",
            branch="feature/demo",
            approved_target_identity="tree-receipt-20260403T010000Z:tree-123",
        )
        fake_executor.execute.return_value = SimpleNamespace(ok=True)
        executor_cls_mock.return_value = fake_executor
        load_push_policy_mock.return_value = make_policy()
        collect_git_status_mock.return_value = {"branch": "feature/demo", "changes": []}
        fresh_report = {
            "ok": True,
            "branch": "feature/demo",
            "head_commit": "abc123",
            "push_stages": {
                "published_remote": True,
                "post_push_green": True,
                "validation_ready": True,
            },
        }
        fake_executor.last_push_report = fresh_report
        load_latest_report_mock.return_value = fresh_report

        rc = push.run(make_args(execute=True, format="json"))

        self.assertEqual(rc, 7)

    @patch("dev.scripts.devctl.commands.vcs.push_executor_routing.emit_output")
    @patch(
        "dev.scripts.devctl.commands.vcs.push_executor_routing.load_latest_push_report"
    )
    @patch("dev.scripts.devctl.commands.vcs.push.remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    @patch("dev.scripts.devctl.commands.vcs.push.load_push_policy")
    @patch("dev.scripts.devctl.commands.vcs.governed_executor.GovernedVcsExecutor")
    def test_run_uses_policy_remote_for_executor_routed_push(
        self,
        executor_cls_mock,
        load_push_policy_mock,
        collect_git_status_mock,
        _remote_exists_mock,
        load_latest_report_mock,
        _emit_output_mock,
    ) -> None:
        fake_executor = MagicMock()
        fake_executor.load_pipeline.return_value = SimpleNamespace(
            pipeline_id="pipeline-123",
            state="commit_recorded",
            commit_sha="abc123",
            branch="feature/demo",
            approved_target_identity="tree-receipt-20260403T010000Z:tree-123",
        )
        fake_executor.execute.return_value = SimpleNamespace(ok=True)
        executor_cls_mock.return_value = fake_executor
        load_push_policy_mock.return_value = make_policy(default_remote="upstream")
        collect_git_status_mock.return_value = {"branch": "feature/demo", "changes": []}
        fresh_report = {
            "ok": True,
            "branch": "feature/demo",
            "head_commit": "abc123",
            "push_stages": {
                "published_remote": True,
                "post_push_green": True,
                "validation_ready": True,
            },
        }
        fake_executor.last_push_report = fresh_report
        load_latest_report_mock.return_value = fresh_report
        _emit_output_mock.return_value = 0

        rc = push.run(make_args(execute=True, format="json"))

        self.assertEqual(rc, 0)
        action = fake_executor.execute.call_args.args[0]
        self.assertEqual(action.parameters["remote"], "upstream")
        self.assertEqual(
            action.parameters["approved_target_identity"],
            "tree-receipt-20260403T010000Z:tree-123",
        )

    @patch(
        "dev.scripts.devctl.commands.vcs.push_executor_routing.current_head_commit_sha",
        return_value="current-head",
    )
    @patch("dev.scripts.devctl.commands.vcs.push_executor_routing.emit_output")
    @patch(
        "dev.scripts.devctl.commands.vcs.push_executor_routing.load_latest_push_report"
    )
    @patch("dev.scripts.devctl.commands.vcs.push.remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    @patch("dev.scripts.devctl.commands.vcs.push.load_push_policy")
    @patch("dev.scripts.devctl.commands.vcs.governed_executor.GovernedVcsExecutor")
    def test_run_does_not_emit_stale_latest_report_for_executor_routed_push(
        self,
        executor_cls_mock,
        load_push_policy_mock,
        collect_git_status_mock,
        _remote_exists_mock,
        load_latest_report_mock,
        emit_output_mock,
        _current_head_mock,
    ) -> None:
        fake_executor = MagicMock()
        fake_executor.load_pipeline.return_value = SimpleNamespace(
            pipeline_id="pipeline-123",
            state="push_blocked",
            commit_sha="current-head",
            branch="feature/current",
        )
        fake_executor.execute.return_value = SimpleNamespace(ok=False)
        fake_executor.last_push_report = None
        executor_cls_mock.return_value = fake_executor
        load_push_policy_mock.return_value = make_policy()
        collect_git_status_mock.return_value = {
            "branch": "feature/current",
            "changes": [],
        }
        self.live_branch_mock.return_value = "feature/current"
        load_latest_report_mock.return_value = {
            "ok": False,
            "branch": "feature/demo",
            "head_commit": "current-head",
            "typed_action": {
                "parameters": {
                    "branch": "feature/demo",
                    "approved_target_identity": (
                        "tree-receipt-20260403T010000Z:tree-123"
                    ),
                }
            },
        }

        rc = push.run(make_args(execute=True, format="json"))

        self.assertEqual(rc, 1)
        fake_executor.execute.assert_called_once()
        load_latest_report_mock.assert_called_once()
        emit_output_mock.assert_not_called()

    @patch("dev.scripts.devctl.commands.vcs.push.run_push_action")
    @patch("dev.scripts.devctl.commands.vcs.push.remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    @patch("dev.scripts.devctl.commands.vcs.push.load_push_policy")
    @patch("dev.scripts.devctl.commands.vcs.governed_executor.GovernedVcsExecutor")
    def test_run_does_not_reuse_completed_pipeline_for_new_push(
        self,
        executor_cls_mock,
        load_push_policy_mock,
        collect_git_status_mock,
        _remote_exists_mock,
        run_push_action_mock,
    ) -> None:
        fake_executor = MagicMock()
        fake_executor.load_pipeline.return_value = SimpleNamespace(
            pipeline_id="pipeline-123",
            state="push_completed",
            commit_sha="old-head",
            branch="feature/demo",
            approved_target_identity="tree-receipt-20260403T010000Z:tree-123",
        )
        fake_executor.execute.return_value = SimpleNamespace(ok=True)
        executor_cls_mock.return_value = fake_executor
        load_push_policy_mock.return_value = make_policy()
        collect_git_status_mock.return_value = {"branch": "feature/demo", "changes": []}
        run_push_action_mock.return_value = (0, {"ok": True})

        rc = push.run(make_args(execute=True, format="json"))

        self.assertEqual(rc, 0)
        fake_executor.execute.assert_not_called()
        run_push_action_mock.assert_called_once()

    @patch(
        "dev.scripts.devctl.governance.push_state.lookup_push_receipt",
        return_value=None,
    )
    @patch(
        "dev.scripts.devctl.governance.push_state._git_stdout",
        side_effect=[
            "",
            "feature/demo",
            "abc123",
            "origin/feature/demo",
            "0",
            " M alpha.py\n M beta.py\n M gamma.py\n?? delta.py\n",
        ],
    )
    def test_detect_push_enforcement_requires_checkpoint_when_budget_exceeded(
        self,
        _git_stdout_mock,
        _lookup_receipt_mock,
    ) -> None:
        policy = make_policy(
            checkpoint=PushCheckpointPolicy(
                max_dirty_paths_before_checkpoint=3,
                max_untracked_paths_before_checkpoint=2,
            )
        )

        state = detect_push_enforcement_state(policy)

        self.assertTrue(state["checkpoint_required"])
        self.assertFalse(state["safe_to_continue_editing"])
        self.assertEqual(state["recommended_action"], "checkpoint_before_continue")
        self.assertEqual(state["checkpoint_reason"], "dirty_path_budget_exceeded")
        self.assertEqual(state["publication_backlog_state"], "none")

    @patch(
        "dev.scripts.devctl.governance.push_state.lookup_push_receipt",
        return_value=None,
    )
    @patch(
        "dev.scripts.devctl.governance.push_state._git_stdout",
        side_effect=[
            "",
            "feature/demo",
            "abc123",
            "origin/feature/demo",
            "0",
            " M alpha.py\n?? delta.py\n",
        ],
    )
    def test_detect_push_enforcement_allows_editing_within_budget(
        self,
        _git_stdout_mock,
        _lookup_receipt_mock,
    ) -> None:
        policy = make_policy(
            checkpoint=PushCheckpointPolicy(
                max_dirty_paths_before_checkpoint=5,
                max_untracked_paths_before_checkpoint=3,
            )
        )

        state = detect_push_enforcement_state(policy)

        self.assertFalse(state["checkpoint_required"])
        self.assertTrue(state["safe_to_continue_editing"])
        self.assertEqual(state["recommended_action"], "commit_before_push")
        self.assertEqual(state["checkpoint_reason"], "within_dirty_budget")
        self.assertEqual(state["publication_backlog_state"], "none")

    def test_detect_push_enforcement_matches_authorized_receipt_chain(self) -> None:
        def _fake_git_stdout(_repo_root, *cmd):
            values = {
                ("rev-parse", "--git-path", "hooks/pre-push"): "",
                ("rev-parse", "--abbrev-ref", "HEAD"): "feature/demo",
                ("rev-parse", "HEAD"): "receipt-2",
                (
                    "rev-parse",
                    "--abbrev-ref",
                    "--symbolic-full-name",
                    "@{u}",
                ): "origin/feature/demo",
                ("rev-list", "--count", "origin/feature/demo..HEAD"): "1",
                ("status", "--porcelain", "--untracked-files=all"): "",
            }
            return values.get(cmd, "")

        pipeline = SimpleNamespace(
            approved_target_identity="tree-receipt-20260403T010000Z:tree-123",
            worktree_identity="",
            push_authorization=SimpleNamespace(
                authorization_id="push-auth-20260403T010000Z",
                approval_mode="commit_pipeline_approval",
                authorized_head_sha="head-old",
                expires_at_utc="",
                approved_target_identity="tree-receipt-20260403T010000Z:tree-123",
                worktree_identity="",
                guard_status="pass",
            ),
        )

        with (
            patch(
                "dev.scripts.devctl.governance.push_state.lookup_push_receipt",
                return_value=None,
            ),
            patch(
                "dev.scripts.devctl.governance.push_state.load_latest_push_report",
                return_value=None,
            ),
            patch(
                "dev.scripts.devctl.governance.push_state.load_remote_commit_pipeline_contract",
                return_value=pipeline,
            ),
            patch(
                "dev.scripts.devctl.governance.push_state.managed_receipt_ancestor_shas",
                return_value=("receipt-1", "head-old"),
            ),
            patch(
                "dev.scripts.devctl.governance.push_state._git_stdout",
                side_effect=_fake_git_stdout,
            ),
        ):
            state = detect_push_enforcement_state(make_policy())

        self.assertTrue(state["current_push_authorization_matches_current_head"])

    @patch(
        "dev.scripts.devctl.governance.push_state.lookup_push_receipt",
        return_value=None,
    )
    @patch(
        "dev.scripts.devctl.governance.push_state._git_stdout",
        side_effect=[
            "",
            "feature/demo",
            "abc123",
            "origin/feature/demo",
            "0",
            "M  alpha.py\n M beta.py\n?? delta.py\n",
        ],
    )
    def test_detect_push_enforcement_tracks_staged_and_unstaged_paths(
        self,
        _git_stdout_mock,
        _lookup_receipt_mock,
    ) -> None:
        policy = make_policy(
            checkpoint=PushCheckpointPolicy(
                max_dirty_paths_before_checkpoint=5,
                max_untracked_paths_before_checkpoint=3,
            )
        )

        state = detect_push_enforcement_state(policy)

        self.assertEqual(state["dirty_path_count"], 3)
        self.assertEqual(state["untracked_path_count"], 1)
        self.assertEqual(state["staged_path_count"], 1)
        self.assertEqual(state["unstaged_path_count"], 1)
        self.assertEqual(
            state["checkpoint_reason"], "staged_and_unstaged_worktree_present"
        )
        self.assertEqual(state["recommended_action"], "commit_before_push")

    @patch(
        "dev.scripts.devctl.governance.push_state.lookup_push_receipt",
        return_value=None,
    )
    @patch(
        "dev.scripts.devctl.governance.push_state._git_stdout",
        side_effect=[
            "",
            "feature/demo",
            "abc123",
            "origin/feature/demo",
            "0",
            "M  alpha.py\nM  beta.py\n",
        ],
    )
    def test_detect_push_enforcement_prefers_staged_budget_reason(
        self,
        _git_stdout_mock,
        _lookup_receipt_mock,
    ) -> None:
        policy = make_policy(
            checkpoint=PushCheckpointPolicy(
                max_dirty_paths_before_checkpoint=2,
                max_untracked_paths_before_checkpoint=3,
            )
        )

        state = detect_push_enforcement_state(policy)

        self.assertTrue(state["checkpoint_required"])
        self.assertEqual(state["staged_path_count"], 2)
        self.assertEqual(state["unstaged_path_count"], 0)
        self.assertEqual(state["checkpoint_reason"], "staged_index_budget_exceeded")

    @patch(
        "dev.scripts.devctl.governance.push_state.lookup_push_receipt",
        return_value=None,
    )
    @patch(
        "dev.scripts.devctl.governance.push_state._git_stdout",
        side_effect=[
            "",
            "feature/demo",
            "abc123",
            "origin/feature/demo",
            "2",
            "?? convo.md\n",
        ],
    )
    def test_detect_push_enforcement_ignores_advisory_context_paths(
        self,
        _git_stdout_mock,
        _lookup_receipt_mock,
    ) -> None:
        policy = make_policy(
            checkpoint=PushCheckpointPolicy(
                advisory_context_paths=("convo.md",),
            )
        )

        state = detect_push_enforcement_state(policy)

        self.assertFalse(state["worktree_dirty"])
        self.assertTrue(state["worktree_clean"])
        self.assertEqual(state["dirty_path_count"], 0)
        self.assertEqual(state["untracked_path_count"], 0)
        self.assertEqual(state["recommended_action"], "use_devctl_push")
        self.assertEqual(state["publication_backlog_state"], "recommended")
        self.assertEqual(state["pending_publication_commits"], 2)

    @patch(
        "dev.scripts.devctl.governance.push_state.lookup_push_receipt",
        return_value=None,
    )
    @patch(
        "dev.scripts.devctl.governance.push_state._git_stdout",
        side_effect=[
            "",
            "feature/demo",
            "abc123",
            "origin/feature/demo",
            "0",
            " M bridge.md\n",
        ],
    )
    def test_detect_push_enforcement_reports_managed_projection_drift(
        self,
        _git_stdout_mock,
        _lookup_receipt_mock,
    ) -> None:
        policy = make_policy(
            checkpoint=PushCheckpointPolicy(
                compatibility_projection_paths=("bridge.md",),
            )
        )

        state = detect_push_enforcement_state(policy)

        self.assertFalse(state["worktree_dirty"])
        self.assertTrue(state["worktree_clean"])
        self.assertEqual(state["dirty_path_count"], 0)
        self.assertEqual(state["excluded_path_count"], 1)
        self.assertTrue(state["managed_projection_drift"])
        self.assertEqual(state["managed_projection_dirty_paths"], ("bridge.md",))
        self.assertEqual(state["recommended_action"], "no_push_needed")
        self.assertEqual(state["checkpoint_reason"], "clean_worktree")

    @patch(
        "dev.scripts.devctl.governance.push_state.lookup_push_receipt",
        return_value=None,
    )
    @patch(
        "dev.scripts.devctl.governance.push_state._git_stdout",
        side_effect=[
            "",
            "feature/demo",
            "abc123",
            "origin/feature/demo",
            "2",
            " M dev/audits/REVIEW_SNAPSHOT.md\n",
        ],
    )
    def test_detect_push_enforcement_treats_review_snapshot_as_managed_projection(
        self,
        _git_stdout_mock,
        _lookup_receipt_mock,
    ) -> None:
        state = detect_push_enforcement_state(make_policy())

        self.assertFalse(state["worktree_dirty"])
        self.assertTrue(state["worktree_clean"])
        self.assertEqual(state["dirty_path_count"], 0)
        self.assertEqual(state["excluded_path_count"], 1)
        self.assertEqual(
            state["managed_projection_dirty_paths"],
            ("dev/audits/REVIEW_SNAPSHOT.md",),
        )
        self.assertEqual(state["recommended_action"], "use_devctl_push")

    @patch(
        "dev.scripts.devctl.governance.push_state_receipts.is_managed_receipt_commit",
        side_effect=lambda *, repo_root, current_head: current_head
        in {"receipt-1", "receipt-2"},
    )
    @patch(
        "dev.scripts.devctl.governance.push_state.lookup_push_receipt",
        return_value=None,
    )
    @patch("dev.scripts.devctl.governance.push_state._git_stdout")
    def test_detect_push_enforcement_classifies_ahead_receipts_separately(
        self,
        git_stdout_mock,
        _lookup_receipt_mock,
        _receipt_classifier_mock,
    ) -> None:
        def _fake_git_stdout(_repo_root, *cmd):
            values = {
                ("rev-parse", "--git-path", "hooks/pre-push"): "",
                ("rev-parse", "--abbrev-ref", "HEAD"): "feature/demo",
                ("rev-parse", "HEAD"): "source-2",
                (
                    "rev-parse",
                    "--abbrev-ref",
                    "--symbolic-full-name",
                    "@{u}",
                ): "origin/feature/demo",
                ("rev-list", "--count", "origin/feature/demo..HEAD"): "4",
                ("status", "--porcelain", "--untracked-files=all"): "",
                ("rev-list", "--reverse", "origin/feature/demo..HEAD"): (
                    "source-1\nreceipt-1\nreceipt-2\nsource-2\n"
                ),
            }
            return values.get(cmd, "")

        git_stdout_mock.side_effect = _fake_git_stdout

        state = detect_push_enforcement_state(make_policy())

        self.assertEqual(state["ahead_of_upstream_commits"], 4)
        self.assertEqual(state["ahead_of_upstream_source_commits"], 2)
        self.assertEqual(state["ahead_of_upstream_managed_receipt_commits"], 2)
        self.assertEqual(state["ahead_of_upstream_unclassified_commits"], 0)

    @patch(
        "dev.scripts.devctl.governance.push_state.lookup_push_receipt",
        return_value=None,
    )
    @patch(
        "dev.scripts.devctl.governance.push_state.latest_push_report_relpath",
        return_value="dev/reports/push/latest.json",
    )
    @patch(
        "dev.scripts.devctl.governance.push_state.load_remote_commit_pipeline_contract",
        return_value=SimpleNamespace(
            approved_target_identity="tree-receipt-20260403T010000Z:tree-123"
        ),
    )
    @patch(
        "dev.scripts.devctl.governance.push_state.load_latest_push_report",
        return_value={
            "branch": "feature/demo",
            "remote": "origin",
            "head_commit": "abc123",
            "approved_target_identity": "tree-receipt-20260403T010000Z:tree-123",
            "push_stages": {
                "validation_ready": True,
                "published_remote": True,
                "post_push_green": False,
            },
        },
    )
    @patch("dev.scripts.devctl.governance.push_state._git_stdout")
    def test_detect_push_enforcement_trusts_persisted_current_head_publish(
        self,
        git_stdout_mock,
        _load_latest_push_report_mock,
        _load_remote_commit_pipeline_contract_mock,
        _latest_push_report_relpath_mock,
        _lookup_receipt_mock,
    ) -> None:
        def _fake_git_stdout(_repo_root, *cmd):
            values = {
                ("rev-parse", "--git-path", "hooks/pre-push"): "",
                ("rev-parse", "--abbrev-ref", "HEAD"): "feature/demo",
                ("rev-parse", "HEAD"): "abc123",
                (
                    "rev-parse",
                    "--abbrev-ref",
                    "--symbolic-full-name",
                    "@{u}",
                ): "origin/feature/demo",
                ("rev-list", "--count", "origin/feature/demo..HEAD"): "1",
                ("status", "--porcelain", "--untracked-files=all"): "",
            }
            return values.get(cmd, "")

        git_stdout_mock.side_effect = _fake_git_stdout

        state = detect_push_enforcement_state(make_policy())

        self.assertEqual(state["recommended_action"], "no_push_needed")
        self.assertEqual(state["publication_backlog_state"], "none")
        self.assertTrue(state["latest_push_report_matches_current_approved_target"])
        self.assertTrue(state["latest_push_report_matches_current_head"])
        self.assertTrue(state["latest_push_report_matches_current_branch"])

    @patch(
        "dev.scripts.devctl.governance.push_state.lookup_push_receipt",
        return_value=None,
    )
    @patch(
        "dev.scripts.devctl.governance.push_state.latest_push_report_relpath",
        return_value="dev/reports/push/latest.json",
    )
    @patch(
        "dev.scripts.devctl.governance.push_state.load_remote_commit_pipeline_contract",
        return_value=SimpleNamespace(
            approved_target_identity="tree-receipt-20260403T010000Z:tree-123"
        ),
    )
    @patch(
        "dev.scripts.devctl.governance.push_state.load_latest_push_report",
        return_value={
            "branch": "feature/demo",
            "remote": "origin",
            "head_commit": "old-head",
            "approved_target_identity": "tree-receipt-20260403T010000Z:tree-123",
            "push_stages": {
                "validation_ready": True,
                "published_remote": True,
                "post_push_green": False,
            },
        },
    )
    @patch("dev.scripts.devctl.governance.push_state._git_stdout")
    def test_detect_push_enforcement_rejects_stale_head_publish_receipt(
        self,
        git_stdout_mock,
        _load_latest_push_report_mock,
        _load_remote_commit_pipeline_contract_mock,
        _latest_push_report_relpath_mock,
        _lookup_receipt_mock,
    ) -> None:
        def _fake_git_stdout(_repo_root, *cmd):
            values = {
                ("rev-parse", "--git-path", "hooks/pre-push"): "",
                ("rev-parse", "--abbrev-ref", "HEAD"): "feature/demo",
                ("rev-parse", "HEAD"): "new-head",
                (
                    "rev-parse",
                    "--abbrev-ref",
                    "--symbolic-full-name",
                    "@{u}",
                ): "origin/feature/demo",
                ("rev-list", "--count", "origin/feature/demo..HEAD"): "1",
                ("status", "--porcelain", "--untracked-files=all"): "",
            }
            return values.get(cmd, "")

        git_stdout_mock.side_effect = _fake_git_stdout

        state = detect_push_enforcement_state(make_policy())

        self.assertEqual(state["recommended_action"], "use_devctl_push")
        self.assertEqual(state["pending_publication_commits"], 1)
        self.assertFalse(state["latest_push_report_matches_current_head"])
        self.assertTrue(state["latest_push_report_matches_current_branch"])
        self.assertTrue(state["latest_push_report_matches_current_approved_target"])

    @patch(
        "dev.scripts.devctl.governance.push_state.lookup_push_receipt",
        return_value=None,
    )
    @patch(
        "dev.scripts.devctl.governance.push_state.latest_push_report_relpath",
        return_value="dev/reports/push/latest.json",
    )
    @patch(
        "dev.scripts.devctl.governance.push_state.load_remote_commit_pipeline_contract",
        return_value=SimpleNamespace(
            approved_target_identity="tree-receipt-20260403T010000Z:tree-123"
        ),
    )
    @patch(
        "dev.scripts.devctl.governance.push_state.load_latest_push_report",
        return_value={
            "branch": "feature/demo",
            "remote": "origin",
            "head_commit": "abc123",
            "approved_target_identity": "tree-receipt-20260403T010000Z:tree-123",
            "push_stages": {
                "validation_ready": True,
                "published_remote": True,
                "post_push_green": False,
            },
        },
    )
    @patch("dev.scripts.devctl.governance.push_state._git_stdout")
    def test_detect_push_enforcement_rejects_publish_receipt_for_different_remote(
        self,
        git_stdout_mock,
        _load_latest_push_report_mock,
        _load_remote_commit_pipeline_contract_mock,
        _latest_push_report_relpath_mock,
        _lookup_receipt_mock,
    ) -> None:
        def _fake_git_stdout(_repo_root, *cmd):
            values = {
                ("rev-parse", "--git-path", "hooks/pre-push"): "",
                ("rev-parse", "--abbrev-ref", "HEAD"): "feature/demo",
                ("rev-parse", "HEAD"): "abc123",
                (
                    "rev-parse",
                    "--abbrev-ref",
                    "--symbolic-full-name",
                    "@{u}",
                ): "upstream/feature/demo",
                ("rev-list", "--count", "upstream/feature/demo..HEAD"): "1",
                ("status", "--porcelain", "--untracked-files=all"): "",
            }
            return values.get(cmd, "")

        git_stdout_mock.side_effect = _fake_git_stdout

        state = detect_push_enforcement_state(make_policy())

        self.assertEqual(state["recommended_action"], "use_devctl_push")
        self.assertEqual(state["pending_publication_commits"], 1)
        self.assertTrue(state["latest_push_report_matches_current_head"])
        self.assertTrue(state["latest_push_report_matches_current_branch"])
        self.assertTrue(state["latest_push_report_matches_current_approved_target"])

    @patch(
        "dev.scripts.devctl.governance.push_state.lookup_push_receipt",
        return_value=None,
    )
    @patch(
        "dev.scripts.devctl.governance.push_state.latest_push_report_relpath",
        return_value="dev/reports/push/latest.json",
    )
    @patch(
        "dev.scripts.devctl.governance.push_state.load_remote_commit_pipeline_contract",
        return_value=SimpleNamespace(approved_target_identity=""),
    )
    @patch(
        "dev.scripts.devctl.governance.push_state.load_latest_push_report",
        return_value={
            "branch": "feature/demo",
            "remote": "origin",
            "head_commit": "abc123",
            "approved_target_identity": "",
            "push_stages": {
                "validation_ready": True,
                "published_remote": True,
                "post_push_green": False,
            },
        },
    )
    @patch("dev.scripts.devctl.governance.push_state._git_stdout")
    def test_detect_push_enforcement_trusts_blank_target_identity_publish_receipt(
        self,
        git_stdout_mock,
        _load_latest_push_report_mock,
        _load_remote_commit_pipeline_contract_mock,
        _latest_push_report_relpath_mock,
        _lookup_receipt_mock,
    ) -> None:
        def _fake_git_stdout(_repo_root, *cmd):
            values = {
                ("rev-parse", "--git-path", "hooks/pre-push"): "",
                ("rev-parse", "--abbrev-ref", "HEAD"): "feature/demo",
                ("rev-parse", "HEAD"): "abc123",
                (
                    "rev-parse",
                    "--abbrev-ref",
                    "--symbolic-full-name",
                    "@{u}",
                ): "origin/feature/demo",
                ("rev-list", "--count", "origin/feature/demo..HEAD"): "1",
                ("status", "--porcelain", "--untracked-files=all"): "",
            }
            return values.get(cmd, "")

        git_stdout_mock.side_effect = _fake_git_stdout

        state = detect_push_enforcement_state(make_policy())

        self.assertEqual(state["recommended_action"], "no_push_needed")
        self.assertEqual(state["publication_backlog_state"], "none")
        self.assertTrue(state["latest_push_report_matches_current_approved_target"])

    @patch("dev.scripts.devctl.commands.vcs.push.remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    @patch("dev.scripts.devctl.commands.vcs.push.publication_authorization_decision")
    def test_push_loader_ignores_advisory_context_paths(
        self,
        publication_authorization_mock,
        collect_git_status_mock,
        _remote_exists_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "branch": "feature/demo",
            "changes": [{"path": "convo.md"}],
        }
        publication_authorization_mock.return_value = _publication_authorization()
        policy = make_policy(
            checkpoint=PushCheckpointPolicy(
                advisory_context_paths=("convo.md",),
            )
        )

        state = push._load_run_state(policy, make_args())

        self.assertEqual(state.dirty_paths, [])
        self.assertEqual(state.errors, [])

    @patch("dev.scripts.devctl.commands.vcs.push.remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    @patch("dev.scripts.devctl.commands.vcs.push.publication_authorization_decision")
    def test_push_loader_allows_staged_only_paths(
        self,
        publication_authorization_mock,
        collect_git_status_mock,
        _remote_exists_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "branch": "feature/demo",
            "changes": [
                {
                    "path": "next_commit.py",
                    "status": "M",
                    "raw_status": "M ",
                    "index_status": "M",
                    "worktree_status": " ",
                }
            ],
        }
        publication_authorization_mock.return_value = _publication_authorization()

        state = push._load_run_state(make_policy(), make_args())

        self.assertEqual(state.dirty_paths, [])
        self.assertEqual(state.errors, [])

    @patch("dev.scripts.devctl.commands.vcs.push.write_output")
    @patch("dev.scripts.devctl.commands.vcs.push.load_push_policy")
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    def test_push_blocks_protected_branch(
        self,
        collect_git_status_mock,
        load_policy_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {"branch": "develop", "changes": []}
        self.live_branch_mock.return_value = "develop"
        load_policy_mock.return_value = make_policy()

        rc = push.run(make_args())

        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["status"], "blocked")
        self.assertIn("protected branch", payload["errors"][0])

    @patch("dev.scripts.devctl.commands.vcs.push.write_output")
    @patch("dev.scripts.devctl.commands.vcs.push.run_cmd")
    @patch(
        "dev.scripts.devctl.commands.vcs.push.current_upstream_ref",
        return_value="origin/feature/demo",
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.build_preflight_shell_command",
        return_value="python3 dev/scripts/devctl.py check-router --since-ref origin/feature/demo --execute",
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.branch_divergence",
        return_value={"behind": 0, "ahead": 2, "error": None},
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.remote_branch_exists", return_value=True
    )
    @patch("dev.scripts.devctl.commands.vcs.push.remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.load_push_policy")
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    @patch("dev.scripts.devctl.commands.vcs.push.publication_authorization_decision")
    def test_push_default_run_validates_and_stops_before_git_push(
        self,
        publication_authorization_mock,
        collect_git_status_mock,
        load_policy_mock,
        _remote_exists_mock,
        _remote_branch_exists_mock,
        _branch_divergence_mock,
        _current_upstream_ref_mock,
        _preflight_command_mock,
        run_cmd_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {"branch": "feature/demo", "changes": []}
        load_policy_mock.return_value = make_policy()
        publication_authorization_mock.return_value = _publication_authorization()
        run_cmd_mock.side_effect = [
            {
                "name": "git-fetch",
                "cmd": ["git", "fetch", "origin"],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            },
            {
                "name": "push-refresh-render-surfaces",
                "cmd": [
                    "python3",
                    "dev/scripts/devctl.py",
                    "render-surfaces",
                    "--write",
                    "--format",
                    "json",
                ],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            },
            {
                "name": "push-preflight",
                "cmd": [
                    "bash",
                    "-lc",
                    "python3 dev/scripts/devctl.py check-router --since-ref origin/feature/demo --execute",
                ],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            },
        ]

        rc = push.run(make_args())

        self.assertEqual(rc, 0)
        self.sync_bridge_mock.assert_called_once()
        executed = [call.args[1] for call in run_cmd_mock.call_args_list]
        self.assertEqual(
            executed,
            [
                ["git", "fetch", "origin"],
                [
                    "bash",
                    "-lc",
                    "python3 dev/scripts/devctl.py check-router --since-ref origin/feature/demo --execute",
                ],
            ],
        )
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["status"], "validation_ready")
        self.assertEqual(
            payload["artifacts"]["latest_json"], "dev/reports/push/latest.json"
        )
        self.assertEqual(
            payload["push_authorization_id"],
            "push-auth-20260403T010000Z",
        )
        self.assertEqual(
            payload["push_authorization_mode"],
            "commit_pipeline_approval",
        )
        self.assertEqual(
            payload["approved_target_identity"],
            "tree-receipt-20260403T010000Z:tree-123",
        )
        self.assertEqual(
            payload["action_result"]["artifact_paths"],
            ["dev/reports/push/latest.json"],
        )
        self.assertEqual(
            payload["push_stages"],
            {
                "validation_ready": True,
                "published_remote": False,
                "post_push_green": False,
            },
        )
        self.assertEqual(payload["typed_action"]["action_id"], "vcs.push")

    @patch("dev.scripts.devctl.commands.vcs.push.write_output")
    @patch("dev.scripts.devctl.commands.vcs.push.run_cmd")
    @patch(
        "dev.scripts.devctl.commands.vcs.push.branch_divergence",
        return_value={"behind": 0, "ahead": 0, "error": None},
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.remote_branch_exists", return_value=True
    )
    @patch("dev.scripts.devctl.commands.vcs.push.remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.load_push_policy")
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    @patch("dev.scripts.devctl.commands.vcs.push.publication_authorization_decision")
    def test_push_skips_preflight_when_branch_is_already_published(
        self,
        publication_authorization_mock,
        collect_git_status_mock,
        load_policy_mock,
        _remote_exists_mock,
        _remote_branch_exists_mock,
        _branch_divergence_mock,
        run_cmd_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {"branch": "feature/demo", "changes": []}
        load_policy_mock.return_value = make_policy()
        publication_authorization_mock.return_value = _publication_authorization()
        run_cmd_mock.side_effect = [
            {
                "name": "git-fetch",
                "cmd": ["git", "fetch", "origin"],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            }
        ]

        rc = push.run(make_args())

        self.assertEqual(rc, 0)
        self.assertEqual(
            [call.args[1] for call in run_cmd_mock.call_args_list],
            [["git", "fetch", "origin"]],
        )
        self.sync_bridge_mock.assert_not_called()
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["status"], "validation_ready")
        self.assertEqual(payload["reason"], "branch_already_pushed")
        self.assertIsNone(payload["preflight_step"])
        self.assertIsNone(payload["push_step"])
        self.assertEqual(
            payload["push_stages"],
            {
                "validation_ready": True,
                "published_remote": False,
                "post_push_green": False,
            },
        )

    @patch("dev.scripts.devctl.commands.vcs.push.write_output")
    @patch("dev.scripts.devctl.commands.vcs.push.run_cmd")
    @patch(
        "dev.scripts.devctl.commands.vcs.push.branch_divergence",
        return_value={"behind": 0, "ahead": 0, "error": None},
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.remote_branch_exists", return_value=True
    )
    @patch("dev.scripts.devctl.commands.vcs.push.remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.load_push_policy")
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    @patch("dev.scripts.devctl.commands.vcs.push.publication_authorization_decision")
    def test_push_execute_noops_when_branch_is_already_published(
        self,
        publication_authorization_mock,
        collect_git_status_mock,
        load_policy_mock,
        _remote_exists_mock,
        _remote_branch_exists_mock,
        _branch_divergence_mock,
        run_cmd_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {"branch": "feature/demo", "changes": []}
        load_policy_mock.return_value = make_policy()
        publication_authorization_mock.return_value = _publication_authorization()
        run_cmd_mock.side_effect = [
            {
                "name": "git-fetch",
                "cmd": ["git", "fetch", "origin"],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            }
        ]

        with (
            patch.object(
                push_preflight_projection,
                "auto_commit_managed_projection_receipt",
                return_value={"ok": True, "committed": False, "paths": ()},
            ),
            patch.object(
                push_preflight_projection,
                "refresh_stale_reviewer_heartbeat_before_publication",
                return_value={
                    "step": "reviewer_heartbeat_refresh",
                    "status": "skipped",
                    "reason": "unit_test",
                },
            ),
        ):
            rc = push.run(make_args(execute=True))

        self.assertEqual(rc, 0)
        self.assertEqual(
            [call.args[1] for call in run_cmd_mock.call_args_list],
            [["git", "fetch", "origin"]],
        )
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["status"], "validation_ready")
        self.assertEqual(payload["reason"], "branch_already_pushed")
        self.assertIsNone(payload["preflight_step"])
        self.assertIsNone(payload["push_step"])

    @patch("dev.scripts.devctl.commands.vcs.push.write_output")
    @patch(
        "dev.scripts.devctl.commands.vcs.push.build_post_push_commands",
        return_value=["git status", "git log --oneline --decorate -n 10"],
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.current_upstream_ref",
        return_value="",
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.build_preflight_shell_command",
        return_value="python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute",
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.remote_branch_exists", return_value=False
    )
    @patch("dev.scripts.devctl.commands.vcs.push.remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.load_push_policy")
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    @patch("dev.scripts.devctl.commands.vcs.push.run_cmd")
    @patch("dev.scripts.devctl.commands.vcs.push.publication_authorization_decision")
    def test_push_execute_sets_upstream_and_runs_post_push_bundle(
        self,
        publication_authorization_mock,
        run_cmd_mock,
        collect_git_status_mock,
        load_policy_mock,
        _remote_exists_mock,
        _remote_branch_exists_mock,
        _current_upstream_ref_mock,
        _preflight_command_mock,
        _post_push_commands_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {"branch": "feature/demo", "changes": []}
        load_policy_mock.return_value = make_policy()
        publication_authorization_mock.return_value = _publication_authorization()
        run_cmd_mock.side_effect = [
            {
                "name": "git-fetch",
                "cmd": ["git", "fetch", "origin"],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            },
            {
                "name": "push-refresh-render-surfaces",
                "cmd": [
                    "python3",
                    "dev/scripts/devctl.py",
                    "render-surfaces",
                    "--write",
                    "--format",
                    "json",
                ],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            },
            {
                "name": "push-preflight",
                "cmd": [
                    "bash",
                    "-lc",
                    "python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute",
                ],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            },
            {
                "name": "git-push",
                "cmd": ["git", "push", "--set-upstream", "origin", "feature/demo"],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            },
            {
                "name": "push-post-01",
                "cmd": ["bash", "-lc", "git status"],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            },
            {
                "name": "push-post-02",
                "cmd": ["bash", "-lc", "git log --oneline --decorate -n 10"],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            },
        ]

        rc = push.run(make_args(execute=True))

        self.assertEqual(rc, 0)
        executed = [call.args[1] for call in run_cmd_mock.call_args_list]
        self.assertIn(
            [
                "git",
                "-c",
                "devctl.governed-push=true",
                "push",
                "--set-upstream",
                "origin",
                "feature/demo",
            ],
            executed,
        )
        _post_push_commands_mock.assert_called_once_with(
            load_policy_mock.return_value,
            quality_policy_path=None,
            since_ref="origin/develop",
        )
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["status"], "post_push_green")
        self.assertEqual(
            payload["artifacts"]["latest_json"], "dev/reports/push/latest.json"
        )
        self.assertEqual(
            payload["push_authorization_mode"],
            "commit_pipeline_approval",
        )
        self.assertEqual(
            payload["action_result"]["artifact_paths"],
            ["dev/reports/push/latest.json"],
        )
        self.assertEqual(
            payload["push_stages"],
            {
                "validation_ready": True,
                "published_remote": True,
                "post_push_green": True,
            },
        )

    def test_execute_push_flow_sets_internal_git_config_for_governed_push(self) -> None:
        state = push.PushRunState(branch="feature/demo", remote="origin")
        policy = make_policy()
        args = make_args(execute=True, skip_post_push=True)
        git_push_cmds: list[list[str]] = []

        def _runner(name, cmd, cwd=None, env=None):
            if name == "git-push":
                git_push_cmds.append(list(cmd))
            return {
                "name": name,
                "cmd": cmd,
                "cwd": str(cwd or "."),
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            }

        outcome = push.execute_push_flow_with_dependencies(
            state,
            policy,
            args,
            push.PushFlowDependencies(
                run_cmd_fn=_runner,
                build_post_push_commands_fn=lambda _policy, quality_policy_path=None, since_ref=None: [],
            ),
        )

        self.assertTrue(outcome.ok)
        self.assertEqual(len(git_push_cmds), 1)
        self.assertEqual(
            git_push_cmds[0][:4],
            ["git", "-c", "devctl.governed-push=true", "push"],
        )

    @patch("dev.scripts.devctl.commands.vcs.push.write_output")
    @patch("dev.scripts.devctl.commands.vcs.push.run_cmd")
    @patch(
        "dev.scripts.devctl.commands.vcs.push.current_upstream_ref",
        return_value="origin/feature/demo",
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.build_preflight_shell_command",
        return_value="python3 dev/scripts/devctl.py check-router --since-ref origin/feature/demo --execute",
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.branch_divergence",
        return_value={"behind": 0, "ahead": 1, "error": None},
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.remote_branch_exists", return_value=True
    )
    @patch("dev.scripts.devctl.commands.vcs.push.remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.load_push_policy")
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    @patch("dev.scripts.devctl.commands.vcs.push.publication_authorization_decision")
    def test_push_blocks_when_publication_authorization_is_missing(
        self,
        publication_authorization_mock,
        collect_git_status_mock,
        load_policy_mock,
        _remote_exists_mock,
        _remote_branch_exists_mock,
        _branch_divergence_mock,
        _build_preflight_mock,
        _current_upstream_ref_mock,
        run_cmd_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {"branch": "feature/demo", "changes": []}
        load_policy_mock.return_value = make_policy()
        run_cmd_mock.side_effect = [
            {
                "name": "git-fetch",
                "cmd": ["git", "fetch", "origin"],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            },
            {
                "name": "push-refresh-render-surfaces",
                "cmd": [
                    "python3",
                    "dev/scripts/devctl.py",
                    "render-surfaces",
                    "--write",
                    "--format",
                    "json",
                ],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            },
            {
                "name": "push-preflight",
                "cmd": [
                    "bash",
                    "-lc",
                    "python3 dev/scripts/devctl.py check-router --since-ref origin/feature/demo --execute",
                ],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            },
        ]
        publication_authorization_mock.return_value = _publication_authorization(
            authorized=False,
            reason="push_authorization_missing",
            summary=(
                "Publication requires a typed `PushAuthorizationRecord` for the "
                "current HEAD."
            ),
        )

        rc = push.run(make_args(execute=True))

        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["status"], "blocked")
        self.assertIn("Publication authorization blocks", payload["errors"][0])


class PushBridgeSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self._preflight_status_patcher = patch(
            "dev.scripts.devctl.commands.vcs.push_preflight_commit.collect_git_status",
            return_value={"changes": []},
        )
        self.preflight_status_mock = self._preflight_status_patcher.start()
        self.addCleanup(self._preflight_status_patcher.stop)
        self._head_commit_patcher = patch(
            "dev.scripts.devctl.commands.vcs.push.current_head_commit_sha",
            return_value="abc123",
        )
        self.head_commit_mock = self._head_commit_patcher.start()
        self.addCleanup(self._head_commit_patcher.stop)
        self._progress_snapshot_patcher = patch(
            "dev.scripts.devctl.commands.vcs.push.persist_push_progress_snapshot",
            return_value="dev/reports/push/latest.json",
        )
        self.progress_snapshot_mock = self._progress_snapshot_patcher.start()
        self.addCleanup(self._progress_snapshot_patcher.stop)
        self._published_snapshot_patcher = patch(
            "dev.scripts.devctl.commands.vcs.push.persist_published_remote_snapshot",
            return_value="dev/reports/push/latest.json",
        )
        self.published_snapshot_mock = self._published_snapshot_patcher.start()
        self.addCleanup(self._published_snapshot_patcher.stop)
        self._live_branch_patcher = patch(
            "dev.scripts.devctl.commands.vcs.push._live_current_branch",
            return_value="",
        )
        self.live_branch_mock = self._live_branch_patcher.start()
        self.addCleanup(self._live_branch_patcher.stop)
        self._push_flow_head_patcher = patch(
            "dev.scripts.devctl.commands.vcs.push_flow.current_head_commit_sha",
            return_value="abc123",
        )
        self.push_flow_head_mock = self._push_flow_head_patcher.start()
        self.addCleanup(self._push_flow_head_patcher.stop)
        self._push_flow_remote_head_patcher = patch(
            "dev.scripts.devctl.commands.vcs.push_flow._remote_head_sha",
            return_value="abc123",
        )
        self.push_flow_remote_head_mock = self._push_flow_remote_head_patcher.start()
        self.addCleanup(self._push_flow_remote_head_patcher.stop)

    def _runtime_missing_recovery_record(self) -> dict[str, object]:
        return {
            "required": True,
            "reason": "runtime_missing",
            "attention_status": "runtime_missing",
            "implementation_permission": "blocked",
            "observed_control_topology": "no_live_agents",
            "recovery_action": "relaunch_allowed",
            "recovery_basis": "process_dead",
            "next_command": (
                "python3 dev/scripts/devctl.py review-channel --action ensure "
                "--follow --terminal none"
            ),
        }

    def _post_stage_commit_pipeline_handoff(
        self,
        *,
        repo_root: Path,
        token: str,
        write_metadata: bool = True,
        target_revision: str = "abc123",
        from_agent: str = "codex",
        to_agent: str = "claude",
    ):
        review_channel_path = repo_root / "dev/active/review_channel.md"
        review_channel_path.parent.mkdir(parents=True, exist_ok=True)
        review_channel_path.write_text(_review_channel_text(), encoding="utf-8")
        artifact_paths = resolve_artifact_paths(repo_root=repo_root)
        if write_metadata:
            self._write_codex_session_metadata(
                repo_root=repo_root,
                artifact_paths=artifact_paths,
                token=token,
            )
        post_packet(
            repo_root=repo_root,
            review_channel_path=review_channel_path,
            artifact_paths=artifact_paths,
            request=PacketPostRequest(
                from_agent=from_agent,
                to_agent=to_agent,
                kind="action_request",
                summary="Stage verified commit pipeline",
                body="Full guard profile passed.",
                requested_action="stage_commit_pipeline",
                policy_hint="safe_auto_apply",
                approval_required=False,
                target=PacketTargetFields.from_values(
                    target_kind="runtime",
                    target_ref=f"devctl_commit:{target_revision}",
                    target_revision=target_revision,
                ),
                guard_bundle_evidence=PacketGuardBundleEvidenceFields.from_values(
                    full_guard_bundle_evidence="--profile ci",
                ),
            ),
        )
        return artifact_paths

    def _write_codex_session_metadata(
        self,
        *,
        repo_root: Path,
        artifact_paths,
        token: str,
        provider: str = "codex",
    ) -> None:
        session_dir = Path(artifact_paths.projections_root) / "sessions"
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / f"{provider}-conductor.json").write_text(
            json.dumps(
                {
                    "provider": provider,
                    "role": "review_agent",
                    "session_name": f"{provider}-conductor",
                    "prepared_at": "2026-04-27T20:00:00Z",
                    "prepared_session_token": token,
                    "prepared_head_sha": "abc123",
                    "prepared_instruction_revision": "rev-1",
                    "repo_root": str(repo_root),
                    "workspace_root": str(repo_root),
                }
            ),
            encoding="utf-8",
        )

    def test_run_fetch_and_preflight_consults_orphan_snapshot_advisory(self) -> None:
        state = push.PushRunState(branch="feature/demo", remote="origin")
        policy = make_policy()
        args = make_args(skip_preflight=True)

        def _runner(name, cmd, cwd=None, env=None):
            return {
                "name": name,
                "cmd": cmd,
                "cwd": str(cwd or "."),
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            }

        def _append_advisory(warnings, *, repo_root, scan_trigger):
            self.assertEqual(scan_trigger, "push_preflight")
            warnings.append("orphan_snapshot_advisory snapshot_hash=sha256:push")
            return None

        with (
            patch(
                "dev.scripts.devctl.commands.vcs.push.remote_branch_exists",
                return_value=True,
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.push.current_upstream_ref",
                return_value="origin/feature/demo",
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.push.branch_divergence",
                return_value={"behind": 0, "ahead": 1, "error": None},
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.push.append_orphan_snapshot_advisory",
                side_effect=_append_advisory,
            ) as advisory_mock,
        ):
            push._run_fetch_and_preflight(
                state,
                policy,
                args,
                repo_root=Path("/tmp/repo"),
                run_cmd_fn=_runner,
            )

        self.assertEqual(state.errors, [])
        self.assertIn(
            "orphan_snapshot_advisory snapshot_hash=sha256:push",
            state.warnings,
        )
        advisory_mock.assert_called_once()

    def test_run_fetch_and_preflight_refreshes_projection_before_preflight(
        self,
    ) -> None:
        state = push.PushRunState(branch="feature/demo", remote="origin")
        policy = make_policy()
        args = make_args()
        calls: list[str] = []

        def _runner(name, cmd, cwd=None, env=None):
            calls.append(name)
            return {
                "name": name,
                "cmd": cmd,
                "cwd": str(cwd or "."),
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            }

        def _append_advisory(warnings, *, repo_root, scan_trigger):
            del warnings, repo_root, scan_trigger
            calls.append("orphan-advisory")

        def _sync_bridge(_state, *, repo_root):
            del _state, repo_root
            calls.append("bridge-sync")

        def _refresh_projections(
            _state,
            _policy,
            *,
            repo_root,
            command_runner=None,
            quality_policy_path=None,
        ):
            del _state, _policy, repo_root, command_runner, quality_policy_path
            calls.append("managed-projection-refresh")

        with (
            patch(
                "dev.scripts.devctl.commands.vcs.push.remote_branch_exists",
                return_value=True,
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.push.current_upstream_ref",
                return_value="origin/feature/demo",
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.push.branch_divergence",
                return_value={"behind": 0, "ahead": 1, "error": None},
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.push.append_orphan_snapshot_advisory",
                side_effect=_append_advisory,
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.push._sync_bridge_projection_before_preflight",
                side_effect=_sync_bridge,
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.push.refresh_managed_projections_before_preflight",
                side_effect=_refresh_projections,
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.push.build_preflight_shell_command",
                return_value="python3 dev/scripts/devctl.py check-router --execute",
            ),
        ):
            push._run_fetch_and_preflight(
                state,
                policy,
                args,
                repo_root=Path("/tmp/repo"),
                run_cmd_fn=_runner,
            )

        self.assertEqual(state.errors, [])
        self.assertEqual(
            calls,
            [
                "git-fetch",
                "orphan-advisory",
                "bridge-sync",
                "managed-projection-refresh",
                "push-preflight",
            ],
        )

    @patch("dev.scripts.devctl.commands.vcs.push.remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    def test_managed_projection_dirty_paths_reach_prevalidation_sync(
        self,
        collect_git_status_mock,
        _remote_exists_mock,
    ) -> None:
        policy = make_policy(
            checkpoint=PushCheckpointPolicy(
                compatibility_projection_paths=("bridge.md",),
            )
        )
        collect_git_status_mock.return_value = {
            "branch": "feature/demo",
            "changes": [
                {
                    "path": "bridge.md",
                    "raw_status": " M",
                    "index_status": " ",
                    "worktree_status": "M",
                },
                {
                    "path": "dev/audits/REVIEW_SNAPSHOT.md",
                    "raw_status": " M",
                    "index_status": " ",
                    "worktree_status": "M",
                },
            ],
        }
        state = push._load_run_state(policy, make_args())
        calls: list[str] = []

        def _runner(name, cmd, cwd=None, env=None):
            calls.append(name)
            return {
                "name": name,
                "cmd": cmd,
                "cwd": str(cwd or "."),
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            }

        def _refresh_projections(
            _state,
            _policy,
            *,
            repo_root,
            command_runner=None,
            quality_policy_path=None,
        ):
            del _policy, repo_root, command_runner, quality_policy_path
            calls.append("pre-validation-managed-projection-sync")
            _state.pre_validation_managed_projection_sync = {
                "phase": "pre_validation_managed_projection_sync",
                "status": "completed",
                "allowed": True,
                "receipt_committed": True,
                "paths": ("bridge.md", "dev/audits/REVIEW_SNAPSHOT.md"),
            }

        with (
            patch(
                "dev.scripts.devctl.commands.vcs.push.remote_branch_exists",
                return_value=True,
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.push.current_upstream_ref",
                return_value="origin/feature/demo",
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.push.branch_divergence",
                return_value={"behind": 0, "ahead": 1, "error": None},
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.push.append_orphan_snapshot_advisory"
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.push.refresh_managed_projections_before_preflight",
                side_effect=_refresh_projections,
            ),
            patch(
                "dev.scripts.devctl.commands.vcs.push.build_preflight_shell_command",
                return_value="python3 dev/scripts/devctl.py check-router --execute",
            ),
        ):
            push._run_fetch_and_preflight(
                state,
                policy,
                make_args(),
                repo_root=push.REPO_ROOT,
                run_cmd_fn=_runner,
            )

        self.assertEqual(state.errors, [])
        self.assertEqual(state.dirty_paths, [])
        self.assertEqual(
            calls,
            [
                "git-fetch",
                "pre-validation-managed-projection-sync",
                "push-preflight",
            ],
        )
        self.assertEqual(
            state.pre_validation_managed_projection_sync["paths"],
            ("bridge.md", "dev/audits/REVIEW_SNAPSHOT.md"),
        )

    def test_refresh_managed_projections_refreshes_snapshot_then_receipt(self) -> None:
        state = push.PushRunState(branch="feature/demo", remote="origin")
        policy = make_policy()
        calls: list[str] = []

        def _refresh_snapshot(*, repo_root):
            del repo_root
            calls.append("review-snapshot-refresh")
            return ["snapshot warning"]

        def _projection_receipt(_state, _policy, *, repo_root):
            del _state, _policy, repo_root
            calls.append("projection-receipt")
            return {"ok": True, "committed": False, "paths": ()}

        with (
            patch.object(
                push_preflight_projection,
                "refresh_review_snapshot_file",
                side_effect=_refresh_snapshot,
            ),
            patch.object(
                push_preflight_projection,
                "auto_commit_managed_projection_receipt",
                side_effect=_projection_receipt,
            ),
        ):
            result = (
                push_preflight_projection.refresh_managed_projections_before_preflight(
                    state,
                    policy,
                    repo_root=Path("/tmp/repo"),
                )
            )

        self.assertEqual(calls, ["review-snapshot-refresh", "projection-receipt"])
        self.assertEqual(state.warnings, ["snapshot warning"])
        self.assertEqual(
            result,
            {
                "phase": "pre_validation_managed_projection_sync",
                "allowed": True,
                "render_surface_sync": {
                    "phase": "policy_render_surface_sync",
                    "status": "skipped",
                    "committed": False,
                    "commit_sha": "",
                    "paths": (),
                    "reason": "no_tracked_surfaces",
                },
                "render_surface_receipt_committed": False,
                "render_surface_receipt_commit_sha": "",
                "render_surface_paths": (),
                "status": "completed",
                "ok": True,
                "receipt_committed": False,
                "paths": (),
                "snapshot_warning_count": 1,
            },
        )
        self.assertEqual(
            state.pre_validation_managed_projection_sync["phase"],
            "pre_validation_managed_projection_sync",
        )

    def test_refresh_managed_projections_runs_render_surfaces_before_preflight(
        self,
    ) -> None:
        state = push.PushRunState(branch="feature/demo", remote="origin")
        policy = make_policy()
        calls: list[str] = []

        def _runner(name, cmd, cwd=None, env=None):
            del cmd, cwd, env
            calls.append(name)
            return {
                "name": name,
                "cmd": [],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            }

        with (
            patch.object(
                push_render_surface_sync,
                "_tracked_policy_owned_surface_paths",
                return_value=("dev/guides/SYSTEM_MAP.md",),
            ),
            patch.object(
                push_render_surface_sync,
                "auto_commit_selected_preflight_generated_changes",
                return_value={
                    "ok": True,
                    "committed": True,
                    "commit_sha": "surface-receipt",
                    "paths": ("dev/guides/SYSTEM_MAP.md",),
                },
            ),
            patch.object(
                push_preflight_projection,
                "refresh_review_snapshot_file",
                return_value=[],
            ),
            patch.object(
                push_preflight_projection,
                "auto_commit_managed_projection_receipt",
                return_value={"ok": True, "committed": False, "paths": ()},
            ),
        ):
            result = (
                push_preflight_projection.refresh_managed_projections_before_preflight(
                    state,
                    policy,
                    repo_root=Path("/tmp/repo"),
                    command_runner=_runner,
                )
            )

        self.assertEqual(
            calls,
            [
                "push-refresh-render-surfaces",
                "push-refresh-startup-context",
                "push-refresh-context-graph",
            ],
        )
        self.assertTrue(result["render_surface_receipt_committed"])
        self.assertEqual(
            result["render_surface_paths"],
            ("dev/guides/SYSTEM_MAP.md",),
        )
        self.assertIn(
            "Committed policy-owned generated surface receipt surface-rece "
            "for dev/guides/SYSTEM_MAP.md before push.",
            state.warnings,
        )

    def test_render_surface_failure_blocks_before_snapshot_refresh(self) -> None:
        state = push.PushRunState(branch="feature/demo", remote="origin")
        policy = make_policy()

        def _runner(name, cmd, cwd=None, env=None):
            del name, cmd, cwd, env
            return {
                "returncode": 1,
                "failure_output": "surface drift could not be written",
            }

        with (
            patch.object(
                push_render_surface_sync,
                "_tracked_policy_owned_surface_paths",
                return_value=("dev/guides/SYSTEM_MAP.md",),
            ),
            patch.object(
                push_preflight_projection,
                "refresh_review_snapshot_file",
            ) as refresh_snapshot_mock,
        ):
            result = (
                push_preflight_projection.refresh_managed_projections_before_preflight(
                    state,
                    policy,
                    repo_root=Path("/tmp/repo"),
                    command_runner=_runner,
                )
            )

        refresh_snapshot_mock.assert_not_called()
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "blocked")
        self.assertIn(
            "render-surfaces refresh failed before push preflight",
            state.errors[0],
        )

    def test_refresh_managed_projections_refreshes_system_picture_after_receipt(
        self,
    ) -> None:
        state = push.PushRunState(branch="feature/demo", remote="origin")
        policy = make_policy()
        calls: list[str] = []

        def _runner(name, cmd, cwd=None, env=None):
            del cmd, cwd, env
            calls.append(name)
            return {
                "name": name,
                "cmd": [],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            }

        with (
            patch.object(
                push_preflight_projection,
                "refresh_review_snapshot_file",
                return_value=[],
            ),
            patch.object(
                push_preflight_projection,
                "auto_commit_managed_projection_receipt",
                return_value={"ok": True, "committed": True, "paths": ("bridge.md",)},
            ),
        ):
            result = (
                push_preflight_projection.refresh_managed_projections_before_preflight(
                    state,
                    policy,
                    repo_root=Path("/tmp/repo"),
                    command_runner=_runner,
                )
            )

        self.assertEqual(result["receipt_committed"], True)
        self.assertEqual(
            calls,
            [
                "push-refresh-startup-context",
                "push-refresh-context-graph",
                "push-refresh-review-snapshot-receipt",
            ],
        )
        self.assertIn(
            "Refreshed startup-context and context-graph after managed projection "
            "receipt before push preflight.",
            state.warnings,
        )

    def test_refresh_managed_projections_auto_refreshes_stale_reviewer_heartbeat(
        self,
    ) -> None:
        state = push.PushRunState(branch="feature/demo", remote="origin")
        policy = make_policy()
        calls: list[tuple[str, list[str]]] = []

        def _runner(name, cmd, cwd=None, env=None):
            del cwd, env
            calls.append((name, list(cmd)))
            return {
                "name": name,
                "cmd": list(cmd),
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            }

        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            bridge_path = repo_root / "bridge.md"
            bridge_path.write_text(
                _bridge_text_for_push_heartbeat(last_codex_poll="2000-01-01T00:00:00Z"),
                encoding="utf-8",
            )

            with (
                patch.object(
                    push_projection_runtime_refresh,
                    "active_path_config",
                    return_value=SimpleNamespace(
                        bridge_rel="bridge.md",
                        review_channel_rel="dev/active/review_channel.md",
                        review_status_dir_rel="dev/reports/review_channel/latest",
                    ),
                ),
                patch.object(
                    push_preflight_projection,
                    "refresh_review_snapshot_file",
                    return_value=[],
                ),
                patch.object(
                    push_preflight_projection,
                    "auto_commit_managed_projection_receipt",
                    return_value={
                        "ok": True,
                        "committed": True,
                        "paths": ("bridge.md",),
                    },
                ),
            ):
                refresh = (
                    push_preflight_projection.refresh_managed_projections_before_preflight
                )
                result = refresh(
                    state,
                    policy,
                    repo_root=repo_root,
                    command_runner=_runner,
                )

        self.assertEqual(
            [name for name, _cmd in calls],
            [
                "push-refresh-reviewer-heartbeat",
                "push-refresh-startup-context",
                "push-refresh-context-graph",
                "push-refresh-review-snapshot-receipt",
            ],
        )
        heartbeat_cmd = calls[0][1]
        self.assertIn("reviewer-heartbeat", heartbeat_cmd)
        self.assertIn("auto-refresh-during-publication", heartbeat_cmd)
        self.assertEqual(
            result["reviewer_heartbeat_refresh"]["status"],
            "refreshed",
        )
        self.assertEqual(
            result["reviewer_heartbeat_refresh"]["reason"],
            "reviewer_heartbeat_stale",
        )
        self.assertIn(
            "Auto-refreshed stale reviewer heartbeat during push pre-validation "
            "before push preflight.",
            state.warnings,
        )

    def test_refresh_managed_projections_runs_snapshot_receipt_after_head_movement(
        self,
    ) -> None:
        state = push.PushRunState(branch="feature/demo", remote="origin")
        policy = make_policy()
        calls: list[str] = []

        def _runner(name, cmd, cwd=None, env=None):
            del cmd, cwd, env
            calls.append(name)
            return {
                "name": name,
                "cmd": [],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            }

        with (
            patch.object(
                push_preflight_projection,
                "refresh_review_snapshot_file",
                return_value=[],
            ),
            patch.object(
                push_preflight_projection,
                "auto_commit_managed_projection_receipt",
                return_value={"ok": True, "committed": True, "paths": ("bridge.md",)},
            ),
            patch.object(
                push_preflight_projection,
                "_current_head_sha",
                side_effect=["receipt-before", "snapshot-receipt"],
            ),
        ):
            result = (
                push_preflight_projection.refresh_managed_projections_before_preflight(
                    state,
                    policy,
                    repo_root=Path("/tmp/repo"),
                    command_runner=_runner,
                )
            )

        self.assertEqual(result["snapshot_receipt_committed"], True)
        self.assertEqual(result["snapshot_receipt_commit_sha"], "snapshot-receipt")
        self.assertEqual(
            calls,
            [
                "push-refresh-startup-context",
                "push-refresh-context-graph",
                "push-refresh-review-snapshot-receipt",
                "push-refresh-startup-context",
                "push-refresh-context-graph",
            ],
        )
        self.assertIn(
            "Committed ReviewSnapshot freshness receipt snapshot-rec before push preflight.",
            state.warnings,
        )

    def test_generated_preflight_commit_gets_snapshot_receipt_before_authorization(
        self,
    ) -> None:
        state = push.PushRunState(branch="feature/demo", remote="origin")
        policy = make_policy()
        calls: list[str] = []

        def _runner(name, cmd, cwd=None, env=None):
            del cmd, cwd, env
            calls.append(name)
            return {
                "name": name,
                "cmd": [],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            }

        with (
            patch.object(
                push_preflight_projection,
                "auto_commit_preflight_generated_changes",
            ),
            patch.object(
                push_preflight_projection,
                "auto_commit_managed_projection_receipt",
                return_value={"ok": True, "committed": False, "paths": ()},
            ),
            patch.object(
                push_preflight_projection,
                "_current_head_sha",
                side_effect=[
                    "before-generated",
                    "after-generated",
                    "after-generated",
                    "snapshot-receipt",
                ],
            ),
        ):
            push_preflight_projection.refresh_preflight_generated_changes_before_authorization(
                state,
                policy,
                repo_root=Path("/tmp/repo"),
                command_runner=_runner,
            )

        self.assertEqual(calls, ["push-refresh-review-snapshot-receipt"])
        self.assertIn(
            "Committed ReviewSnapshot freshness receipt snapshot-rec before "
            "publication authorization.",
            state.warnings,
        )

    def test_post_validation_auto_commit_repair_forbidden_after_validation_failure(
        self,
    ) -> None:
        state = push.PushRunState(
            branch="feature/demo",
            remote="origin",
            errors=["Configured push preflight failed."],
        )
        policy = make_policy()

        with patch.object(
            push_preflight_projection,
            "refresh_preflight_generated_changes_before_authorization",
        ) as repair_mock:
            result = push_preflight_commit.run_post_validation_auto_commit_repair_phase(
                state,
                policy,
                repo_root=Path("/tmp/repo"),
                validation_passed=False,
            )

        repair_mock.assert_not_called()
        self.assertEqual(
            result,
            {
                "phase": "post_validation_auto_commit_repair",
                "allowed": False,
                "status": "forbidden",
                "reason": "validation_failed",
            },
        )
        self.assertEqual(state.post_validation_auto_commit_repair, result)

    def test_receipt_refresh_updates_event_bundle_before_system_picture(self) -> None:
        state = push.PushRunState(branch="feature/demo", remote="origin")
        calls: list[str] = []

        def _runner(name, cmd, cwd=None, env=None):
            del cmd, cwd, env
            calls.append(name)
            return {
                "name": name,
                "cmd": [],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            }

        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            review_channel_path = repo_root / "dev/active/review_channel.md"
            event_log_path = (
                repo_root / "dev/reports/review_channel/events/trace.ndjson"
            )
            state_path = repo_root / "dev/reports/review_channel/state/latest.json"
            projections_root = (
                repo_root / "dev/reports/review_channel/projections/latest"
            )
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            event_log_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text("# Review Channel\n", encoding="utf-8")
            event_log_path.write_text("", encoding="utf-8")

            def _load_or_refresh_event_bundle(**kwargs):
                self.assertEqual(kwargs["repo_root"], repo_root)
                calls.append("event-bundle")
                return SimpleNamespace()

            with (
                patch.object(
                    push_projection_runtime_refresh,
                    "active_path_config",
                    return_value=SimpleNamespace(
                        review_channel_rel="dev/active/review_channel.md",
                        bridge_rel="bridge.md",
                        review_status_dir_rel="dev/reports/review_channel/latest",
                    ),
                ),
                patch.object(
                    push_projection_runtime_refresh,
                    "resolve_artifact_paths",
                    return_value=SimpleNamespace(
                        event_log_path=str(event_log_path),
                        state_path=str(state_path),
                        projections_root=str(projections_root),
                    ),
                ),
                patch.object(
                    push_projection_runtime_refresh,
                    "load_or_refresh_event_bundle",
                    side_effect=_load_or_refresh_event_bundle,
                ),
            ):
                push_preflight_projection.refresh_runtime_surfaces_after_projection_receipt(
                    state,
                    command_runner=_runner,
                    repo_root=repo_root,
                    next_step_label="push preflight",
                )

        self.assertEqual(
            calls,
            [
                "event-bundle",
                "push-refresh-startup-context",
                "push-refresh-context-graph",
            ],
        )
        self.assertIn(
            "Refreshed review-channel projections after managed projection receipt "
            "before push preflight.",
            state.warnings,
        )

    def test_refresh_managed_projections_blocks_when_system_picture_refresh_fails(
        self,
    ) -> None:
        state = push.PushRunState(branch="feature/demo", remote="origin")
        policy = make_policy()
        calls: list[str] = []

        def _runner(name, cmd, cwd=None, env=None):
            del cmd, cwd, env
            calls.append(name)
            return {
                "name": name,
                "cmd": [],
                "cwd": ".",
                "returncode": (
                    1
                    if name
                    in {
                        "push-refresh-startup-context",
                        "push-refresh-startup-context-retry",
                    }
                    else 0
                ),
                "duration_s": 0.1,
                "skipped": False,
            }

        with (
            patch.object(
                push_preflight_projection,
                "refresh_review_snapshot_file",
                return_value=[],
            ),
            patch.object(
                push_preflight_projection,
                "auto_commit_managed_projection_receipt",
                return_value={"ok": True, "committed": True, "paths": ("bridge.md",)},
            ),
        ):
            push_preflight_projection.refresh_managed_projections_before_preflight(
                state,
                policy,
                repo_root=Path("/tmp/repo"),
                command_runner=_runner,
            )

        self.assertEqual(
            calls,
            [
                "push-refresh-startup-context",
                "push-refresh-review-channel-ensure-follow",
                "push-refresh-startup-context-retry",
            ],
        )
        self.assertEqual(
            state.errors,
            [
                "Managed projection receipt moved HEAD, but startup-context "
                "refresh failed before push preflight."
            ],
        )

    def test_refresh_managed_projections_recovers_plain_startup_refresh_failure_once(
        self,
    ) -> None:
        state = push.PushRunState(branch="feature/demo", remote="origin")
        policy = make_policy()
        calls: list[tuple[str, list[str]]] = []

        def _runner(name, cmd, cwd=None, env=None):
            del cwd, env
            calls.append((name, list(cmd)))
            result = {
                "name": name,
                "cmd": list(cmd),
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            }
            if name == "push-refresh-startup-context":
                result["returncode"] = 1
                result["failure_output"] = "startup-context refresh failed"
            return result

        with (
            patch.object(
                push_preflight_projection,
                "refresh_review_snapshot_file",
                return_value=[],
            ),
            patch.object(
                push_preflight_projection,
                "auto_commit_managed_projection_receipt",
                return_value={"ok": True, "committed": True, "paths": ("bridge.md",)},
            ),
            patch.object(
                push_preflight_projection,
                "auto_commit_review_snapshot_freshness_receipt",
                return_value={"committed": False},
            ),
        ):
            result = (
                push_preflight_projection.refresh_managed_projections_before_preflight(
                    state,
                    policy,
                    repo_root=Path("/tmp/repo"),
                    command_runner=_runner,
                )
            )

        self.assertTrue(result["ok"])
        self.assertEqual(state.errors, [])
        self.assertEqual(
            [name for name, _cmd in calls],
            [
                "push-refresh-startup-context",
                "push-refresh-review-channel-ensure-follow",
                "push-refresh-startup-context-retry",
                "push-refresh-context-graph",
            ],
        )
        self.assertIn("review-channel", calls[1][1])
        self.assertIn("ensure", calls[1][1])
        self.assertIn("--follow", calls[1][1])
        self.assertIn("none", calls[1][1])
        self.assertIn(
            "Startup-context refresh failed after managed projection receipt; ran "
            "review-channel ensure --follow and retried once before push preflight.",
            state.warnings,
        )
        self.assertEqual(
            state.pre_validation_recovery_loop_repair["status"],
            "not_needed",
        )

    def test_sync_managed_projection_recovers_dead_reviewer_worker(
        self,
    ) -> None:
        state = push.PushRunState(branch="feature/demo", remote="origin")
        policy = make_policy()
        calls: list[tuple[str, list[str]]] = []
        failed_startup_context = "\n".join(
            [
                "action=repair_reviewer_loop",
                "reason=runtime_missing",
                "blockers=startup_authority,runtime_missing",
                "next=python3 dev/scripts/devctl.py review-channel --action launch",
                "observed_control_topology=no_live_agents",
                "implementation_permission=blocked",
                "attention_status=runtime_missing",
                "recovery_action=relaunch_allowed",
                "recovery_basis=process_dead",
                "recovery_scope=entire_lane",
            ]
        )

        def _runner(name, cmd, cwd=None, env=None):
            del cwd, env
            calls.append((name, list(cmd)))
            result = {
                "name": name,
                "cmd": list(cmd),
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            }
            if name == "push-refresh-startup-context":
                result["returncode"] = 1
                result["failure_output"] = failed_startup_context
            return result

        with (
            patch.object(
                push_preflight_projection,
                "refresh_review_snapshot_file",
                return_value=[],
            ),
            patch.object(
                push_preflight_projection,
                "auto_commit_managed_projection_receipt",
                return_value={"ok": True, "committed": True, "paths": ("bridge.md",)},
            ),
            patch.object(
                push_preflight_projection,
                "auto_commit_review_snapshot_freshness_receipt",
                return_value={"committed": False},
            ),
        ):
            push_preflight_projection.refresh_managed_projections_before_preflight(
                state,
                policy,
                repo_root=Path("/tmp/repo"),
                command_runner=_runner,
            )

        self.assertEqual(
            [name for name, _cmd in calls],
            [
                "push-refresh-startup-context",
                "push-refresh-context-graph",
                "push-recovery-startup-context-1",
            ],
        )
        self.assertEqual(state.errors, [])
        self.assertTrue(state.pre_validation_recovery_loop_repair_required)
        self.assertTrue(
            any(
                "deferring to pre_validation_recovery_loop_repair" in warning
                for warning in state.warnings
            )
        )

    def test_prevalidation_recovery_loop_runs_bounded_next_chain(self) -> None:
        state = push.PushRunState(
            branch="feature/demo",
            remote="origin",
            pre_validation_recovery_loop_repair_required=True,
        )
        policy = make_policy()
        calls: list[tuple[str, list[str]]] = []
        startup_attempts = 0

        def _runner(name, cmd, cwd=None, env=None):
            del cwd, env
            nonlocal startup_attempts
            calls.append((name, list(cmd)))
            result = {
                "name": name,
                "cmd": list(cmd),
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            }
            if name.startswith("push-recovery-startup-context"):
                startup_attempts += 1
                if startup_attempts == 1:
                    result["returncode"] = 1
                    result["failure_output"] = "\n".join(
                        [
                            "action=repair_reviewer_loop",
                            "reason=runtime_missing",
                            "next=python3 dev/scripts/devctl.py review-channel --action ensure --follow",
                            "implementation_permission=blocked",
                            "attention_status=runtime_missing",
                            "recovery_action=relaunch_allowed",
                        ]
                    )
                elif startup_attempts == 2:
                    result["returncode"] = 1
                    result["failure_output"] = "\n".join(
                        [
                            "action=repair_reviewer_loop",
                            "reason=runtime_missing",
                            "next=python3 dev/scripts/devctl.py review-channel --action launch",
                            "implementation_permission=blocked",
                            "attention_status=runtime_missing",
                            "recovery_action=relaunch_allowed",
                        ]
                    )
                else:
                    result["failure_output"] = "\n".join(
                        [
                            "action=push_allowed",
                            "reason=push_preconditions_satisfied",
                            "next=python3 dev/scripts/devctl.py push --execute",
                            "implementation_permission=active",
                        ]
                    )
            return result

        result = (
            push_recovery_loop_repair.run_pre_validation_recovery_loop_repair_phase(
                state,
                policy,
                repo_root=Path("/tmp/repo"),
                command_runner=_runner,
            )
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(
            [name for name, _cmd in calls],
            [
                "push-recovery-startup-context-1",
                "push-recovery-review-channel-ensure-1",
                "push-recovery-startup-context-2",
                "push-recovery-review-channel-launch-2",
                "push-recovery-startup-context-3",
            ],
        )
        self.assertIn("--follow", calls[1][1])
        self.assertIn("--terminal", calls[3][1])
        self.assertIn("none", calls[3][1])
        self.assertEqual(
            result["typed_action"]["action_id"],
            "vcs.recovery_loop_repair",
        )
        self.assertEqual(
            result["action_result"]["artifact_paths"],
            [],
        )
        self.assertLessEqual(result["step_count"], 5)
        self.assertEqual(state.errors, [])

    def test_prevalidation_recovery_loop_accepts_current_completed_handoff(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._post_stage_commit_pipeline_handoff(
                repo_root=repo_root,
                token="session-token-1",
            )
            state = push.PushRunState(
                branch="feature/demo",
                remote="origin",
                pre_validation_recovery_loop_repair_required=True,
            )
            state.pre_validation_recovery_loop_repair_startup = (
                self._runtime_missing_recovery_record()
            )
            policy = make_policy()
            calls: list[str] = []

            def _runner(name, cmd, cwd=None, env=None):
                del cmd, cwd, env
                calls.append(name)
                return {
                    "name": name,
                    "cmd": [],
                    "cwd": str(repo_root),
                    "returncode": 0,
                    "duration_s": 0.1,
                    "skipped": False,
                }

            result = (
                push_recovery_loop_repair.run_pre_validation_recovery_loop_repair_phase(
                    state,
                    policy,
                    repo_root=repo_root,
                    command_runner=_runner,
                )
            )

        self.assertEqual(calls, [])
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["reason"], "agent_session_completed_handoff")
        self.assertEqual(result["time_budget_seconds"], 180)
        self.assertEqual(
            result["agent_session_outcome"]["outcome"],
            "completed_handoff",
        )
        self.assertEqual(state.errors, [])

    def test_prevalidation_recovery_loop_accepts_head_bound_handoff_without_session_metadata(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            artifact_paths = self._post_stage_commit_pipeline_handoff(
                repo_root=repo_root,
                token="",
                write_metadata=False,
            )
            self._write_codex_session_metadata(
                repo_root=repo_root,
                artifact_paths=artifact_paths,
                token="unrelated-provider-token",
                provider="claude",
            )
            state = push.PushRunState(
                branch="feature/demo",
                remote="origin",
                pre_validation_recovery_loop_repair_required=True,
            )
            state.pre_validation_recovery_loop_repair_startup = (
                self._runtime_missing_recovery_record()
            )
            policy = make_policy()
            calls: list[str] = []

            def _runner(name, cmd, cwd=None, env=None):
                del cmd, cwd, env
                calls.append(name)
                return {
                    "name": name,
                    "cmd": [],
                    "cwd": str(repo_root),
                    "returncode": 0,
                    "duration_s": 0.1,
                    "skipped": False,
                }

            with patch.object(
                push_recovery_loop_handoff,
                "_handoff_target_revisions",
                return_value=("abc123",),
            ):
                result = push_recovery_loop_repair.run_pre_validation_recovery_loop_repair_phase(
                    state,
                    policy,
                    repo_root=repo_root,
                    command_runner=_runner,
                )

        self.assertEqual(calls, [])
        self.assertTrue(result["ok"])
        self.assertEqual(result["reason"], "agent_session_completed_handoff")
        self.assertEqual(
            result["agent_session_outcome"]["target_revision"],
            "abc123",
        )
        self.assertEqual(state.errors, [])

    def test_prevalidation_recovery_loop_rejects_wrong_head_handoff_without_metadata(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._post_stage_commit_pipeline_handoff(
                repo_root=repo_root,
                token="",
                write_metadata=False,
                target_revision="old123",
            )
            state = push.PushRunState(
                branch="feature/demo",
                remote="origin",
                pre_validation_recovery_loop_repair_required=True,
            )
            state.pre_validation_recovery_loop_repair_startup = (
                self._runtime_missing_recovery_record()
            )
            policy = make_policy()
            calls: list[str] = []

            def _runner(name, cmd, cwd=None, env=None):
                del cmd, cwd, env
                calls.append(name)
                return {
                    "name": name,
                    "cmd": [],
                    "cwd": str(repo_root),
                    "returncode": 0,
                    "duration_s": 0.1,
                    "skipped": False,
                }

            with patch.object(
                push_recovery_loop_handoff,
                "_handoff_target_revisions",
                return_value=("abc123",),
            ):
                result = push_recovery_loop_repair.run_pre_validation_recovery_loop_repair_phase(
                    state,
                    policy,
                    repo_root=repo_root,
                    command_runner=_runner,
                )

        self.assertEqual(calls, ["push-recovery-startup-context-1"])
        self.assertTrue(result["ok"])
        self.assertEqual(result["reason"], "startup_context_ready")
        self.assertNotIn("agent_session_outcome", result)
        self.assertEqual(state.errors, [])

    def test_handoff_target_revisions_include_managed_receipt_source_parent(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _run_git(repo_root, "init")
            _run_git(repo_root, "config", "user.email", "test@example.com")
            _run_git(repo_root, "config", "user.name", "Test User")

            (repo_root / "source.txt").write_text("base\n", encoding="utf-8")
            _run_git(repo_root, "add", "source.txt")
            _run_git(repo_root, "commit", "-m", "base")
            base_head = _run_git(repo_root, "rev-parse", "HEAD")

            (repo_root / "source.txt").write_text("source\n", encoding="utf-8")
            _run_git(repo_root, "add", "source.txt")
            _run_git(repo_root, "commit", "-m", "source")
            source_head = _run_git(repo_root, "rev-parse", "HEAD")

            snapshot_path = repo_root / "dev/audits/REVIEW_SNAPSHOT.md"
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot_path.write_text("receipt\n", encoding="utf-8")
            _run_git(repo_root, "add", "dev/audits/REVIEW_SNAPSHOT.md")
            _run_git(
                repo_root,
                "commit",
                "-m",
                f"Refresh external review snapshot for {source_head}",
            )
            receipt_head = _run_git(repo_root, "rev-parse", "HEAD")

            artifact_paths = resolve_artifact_paths(repo_root=repo_root)
            pipeline_path = (
                Path(artifact_paths.projections_root) / "commit_pipeline.json"
            )
            pipeline_path.parent.mkdir(parents=True, exist_ok=True)
            pipeline_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "contract_id": "RemoteCommitPipelineContract",
                        "pipeline_id": "pipeline-test",
                        "commit_sha": source_head,
                        "commit_result": {
                            "schema_version": 1,
                            "contract_id": "ActionResult",
                            "action_id": "vcs.commit",
                            "ok": True,
                            "status": "pass",
                            "reason": "commit_recorded",
                        },
                    }
                ),
                encoding="utf-8",
            )

            revisions = push_recovery_loop_handoff._handoff_target_revisions(repo_root)

        self.assertEqual(revisions, (receipt_head, source_head, base_head))

    def test_prevalidation_recovery_loop_accepts_completed_handoff_at_five_receipt_chain_root(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _run_git(repo_root, "init")
            _run_git(repo_root, "config", "user.email", "test@example.com")
            _run_git(repo_root, "config", "user.name", "Test User")

            (repo_root / "source.txt").write_text("handoff root\n", encoding="utf-8")
            _run_git(repo_root, "add", "source.txt")
            _run_git(repo_root, "commit", "-m", "handoff root")
            handoff_root = _run_git(repo_root, "rev-parse", "HEAD")
            artifact_paths = self._post_stage_commit_pipeline_handoff(
                repo_root=repo_root,
                token="",
                write_metadata=False,
                target_revision=handoff_root,
            )

            (repo_root / "source.txt").write_text("content\n", encoding="utf-8")
            _run_git(repo_root, "add", "source.txt")
            _run_git(repo_root, "commit", "-m", "content")

            snapshot_path = repo_root / "dev/audits/REVIEW_SNAPSHOT.md"
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_commits: list[str] = []
            for index in range(5):
                parent = _run_git(repo_root, "rev-parse", "HEAD")
                snapshot_path.write_text(f"receipt {index}\n", encoding="utf-8")
                _run_git(repo_root, "add", "dev/audits/REVIEW_SNAPSHOT.md")
                _run_git(
                    repo_root,
                    "commit",
                    "-m",
                    f"Refresh external review snapshot for {parent[:8]}",
                )
                receipt_commits.append(_run_git(repo_root, "rev-parse", "HEAD"))

            pipeline_path = (
                Path(artifact_paths.projections_root) / "commit_pipeline.json"
            )
            pipeline_path.parent.mkdir(parents=True, exist_ok=True)
            pipeline_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "contract_id": "RemoteCommitPipelineContract",
                        "pipeline_id": "pipeline-test",
                        "commit_sha": receipt_commits[2],
                        "commit_result": {
                            "schema_version": 1,
                            "contract_id": "ActionResult",
                            "action_id": "vcs.commit",
                            "ok": True,
                            "status": "pass",
                            "reason": "commit_recorded",
                        },
                    }
                ),
                encoding="utf-8",
            )
            state = push.PushRunState(
                branch="feature/demo",
                remote="origin",
                pre_validation_recovery_loop_repair_required=True,
            )
            state.pre_validation_recovery_loop_repair_startup = (
                self._runtime_missing_recovery_record()
            )
            policy = make_policy()
            calls: list[str] = []

            def _runner(name, cmd, cwd=None, env=None):
                del cmd, cwd, env
                calls.append(name)
                return {
                    "name": name,
                    "cmd": [],
                    "cwd": str(repo_root),
                    "returncode": 0,
                    "duration_s": 0.1,
                    "skipped": False,
                }

            result = (
                push_recovery_loop_repair.run_pre_validation_recovery_loop_repair_phase(
                    state,
                    policy,
                    repo_root=repo_root,
                    command_runner=_runner,
                )
            )

        self.assertEqual(calls, [])
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["reason"], "agent_session_completed_handoff")
        self.assertEqual(
            result["agent_session_outcome"]["target_revision"],
            handoff_root,
        )
        self.assertEqual(state.errors, [])

    def test_startup_authority_allows_completed_handoff_at_five_receipt_chain_root(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _run_git(repo_root, "init")
            _run_git(repo_root, "config", "user.email", "test@example.com")
            _run_git(repo_root, "config", "user.name", "Test User")

            (repo_root / "source.txt").write_text("handoff root\n", encoding="utf-8")
            _run_git(repo_root, "add", "source.txt")
            _run_git(repo_root, "commit", "-m", "handoff root")
            handoff_root = _run_git(repo_root, "rev-parse", "HEAD")
            artifact_paths = self._post_stage_commit_pipeline_handoff(
                repo_root=repo_root,
                token="",
                write_metadata=False,
                target_revision=handoff_root,
            )

            (repo_root / "source.txt").write_text("content\n", encoding="utf-8")
            _run_git(repo_root, "add", "source.txt")
            _run_git(repo_root, "commit", "-m", "content")

            snapshot_path = repo_root / "dev/audits/REVIEW_SNAPSHOT.md"
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_commits: list[str] = []
            for index in range(5):
                parent = _run_git(repo_root, "rev-parse", "HEAD")
                snapshot_path.write_text(f"receipt {index}\n", encoding="utf-8")
                _run_git(repo_root, "add", "dev/audits/REVIEW_SNAPSHOT.md")
                _run_git(
                    repo_root,
                    "commit",
                    "-m",
                    f"Refresh external review snapshot for {parent[:8]}",
                )
                receipt_commits.append(_run_git(repo_root, "rev-parse", "HEAD"))

            pipeline_path = (
                Path(artifact_paths.projections_root) / "commit_pipeline.json"
            )
            pipeline_path.parent.mkdir(parents=True, exist_ok=True)
            pipeline_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "contract_id": "RemoteCommitPipelineContract",
                        "pipeline_id": "pipeline-test",
                        "commit_sha": receipt_commits[2],
                        "commit_result": {
                            "schema_version": 1,
                            "contract_id": "ActionResult",
                            "action_id": "vcs.commit",
                            "ok": True,
                            "status": "pass",
                            "reason": "commit_recorded",
                        },
                    }
                ),
                encoding="utf-8",
            )
            reviewer_gate = SimpleNamespace(
                implementation_blocked=True,
                review_gate_allows_push=False,
                implementation_block_reason="runtime_missing",
                reviewer_mode="active_dual_agent",
                effective_reviewer_mode="tools_only",
                review_accepted=False,
            )

            errors = collect_reviewer_loop_block_errors(
                repo_root,
                SimpleNamespace(),
                reviewer_gate=reviewer_gate,
            )

        self.assertEqual(errors, [])

    def test_startup_authority_rejects_wrong_provider_completed_handoff(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _run_git(repo_root, "init")
            _run_git(repo_root, "config", "user.email", "test@example.com")
            _run_git(repo_root, "config", "user.name", "Test User")

            (repo_root / "source.txt").write_text("handoff root\n", encoding="utf-8")
            _run_git(repo_root, "add", "source.txt")
            _run_git(repo_root, "commit", "-m", "handoff root")
            handoff_root = _run_git(repo_root, "rev-parse", "HEAD")
            self._post_stage_commit_pipeline_handoff(
                repo_root=repo_root,
                token="",
                write_metadata=False,
                target_revision=handoff_root,
                from_agent="claude",
                to_agent="codex",
            )
            reviewer_gate = SimpleNamespace(
                implementation_blocked=True,
                review_gate_allows_push=False,
                implementation_block_reason="runtime_missing",
                reviewer_mode="active_dual_agent",
                effective_reviewer_mode="tools_only",
                review_accepted=False,
            )

            errors = collect_reviewer_loop_block_errors(
                repo_root,
                SimpleNamespace(),
                reviewer_gate=reviewer_gate,
            )

        self.assertEqual(len(errors), 1)
        self.assertIn("Reviewer loop blocks", errors[0])

    def test_prevalidation_recovery_loop_rejects_stale_completed_handoff(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            artifact_paths = self._post_stage_commit_pipeline_handoff(
                repo_root=repo_root,
                token="old-session-token",
            )
            self._write_codex_session_metadata(
                repo_root=repo_root,
                artifact_paths=artifact_paths,
                token="new-session-token",
            )
            state = push.PushRunState(
                branch="feature/demo",
                remote="origin",
                pre_validation_recovery_loop_repair_required=True,
            )
            state.pre_validation_recovery_loop_repair_startup = (
                self._runtime_missing_recovery_record()
            )
            policy = make_policy()
            calls: list[str] = []

            def _runner(name, cmd, cwd=None, env=None):
                del cmd, cwd, env
                calls.append(name)
                return {
                    "name": name,
                    "cmd": [],
                    "cwd": str(repo_root),
                    "returncode": 0,
                    "duration_s": 0.1,
                    "skipped": False,
                }

            result = (
                push_recovery_loop_repair.run_pre_validation_recovery_loop_repair_phase(
                    state,
                    policy,
                    repo_root=repo_root,
                    command_runner=_runner,
                )
            )

        self.assertEqual(calls, ["push-recovery-startup-context-1"])
        self.assertTrue(result["ok"])
        self.assertEqual(result["reason"], "startup_context_ready")
        self.assertNotIn("agent_session_outcome", result)
        self.assertEqual(state.errors, [])

    def test_sync_bridge_projection_before_preflight_reprojects_active_bridge(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            bridge_path = repo_root / "bridge.md"
            review_channel_path = repo_root / "dev" / "active" / "review_channel.md"
            review_state_path = (
                repo_root
                / "dev"
                / "reports"
                / "review_channel"
                / "latest"
                / "review_state.json"
            )
            bridge_path.write_text("# Review Bridge\n", encoding="utf-8")
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text(
                "# active review channel\n", encoding="utf-8"
            )
            review_state_path.parent.mkdir(parents=True, exist_ok=True)
            review_state_path.write_text("{}", encoding="utf-8")
            state = push.PushRunState()

            with (
                patch(
                    "dev.scripts.devctl.commands.vcs.push.active_path_config",
                    return_value=SimpleNamespace(
                        bridge_rel="bridge.md",
                        review_channel_rel="dev/active/review_channel.md",
                        review_status_dir_rel="dev/reports/review_channel/latest",
                    ),
                ),
                patch(
                    "dev.scripts.devctl.commands.vcs.push.bridge_is_active",
                    return_value=True,
                ),
                patch(
                    "dev.scripts.devctl.commands.vcs.push.refresh_status_snapshot",
                    return_value=SimpleNamespace(
                        warnings=[],
                        projection_paths=SimpleNamespace(
                            review_state_path=str(review_state_path)
                        ),
                    ),
                ),
                patch(
                    "dev.scripts.devctl.commands.vcs.push._sync_bridge_from_typed_projection_if_needed",
                    return_value=(True, ""),
                ) as sync_mock,
            ):
                push._sync_bridge_projection_before_preflight(
                    state,
                    repo_root=repo_root,
                )

        sync_mock.assert_called_once()
        self.assertIn(
            "Synchronized `bridge.md` from typed review-state before push preflight.",
            state.warnings,
        )

    @patch("dev.scripts.devctl.commands.vcs.push.write_output")
    @patch("dev.scripts.devctl.commands.vcs.push.remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.load_push_policy")
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    @patch("dev.scripts.devctl.commands.vcs.push.publication_authorization_decision")
    def test_push_rejects_skip_preflight_when_policy_disallows_bypass(
        self,
        publication_authorization_mock,
        collect_git_status_mock,
        load_policy_mock,
        _remote_exists_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {"branch": "feature/demo", "changes": []}
        load_policy_mock.return_value = make_policy()
        publication_authorization_mock.return_value = _publication_authorization()

        rc = push.run(make_args(skip_preflight=True))

        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["status"], "blocked")
        self.assertIn("Repo policy blocks `--skip-preflight`", payload["errors"][0])

    @patch("dev.scripts.devctl.commands.vcs.push.write_output")
    @patch("dev.scripts.devctl.commands.vcs.push.remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.load_push_policy")
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    @patch("dev.scripts.devctl.commands.vcs.push.publication_authorization_decision")
    def test_push_rejects_skip_post_push_when_policy_disallows_bypass(
        self,
        publication_authorization_mock,
        collect_git_status_mock,
        load_policy_mock,
        _remote_exists_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {"branch": "feature/demo", "changes": []}
        load_policy_mock.return_value = make_policy()
        publication_authorization_mock.return_value = _publication_authorization()

        rc = push.run(make_args(skip_post_push=True))

        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["status"], "blocked")
        self.assertIn("Repo policy blocks `--skip-post-push`", payload["errors"][0])

    @patch("dev.scripts.devctl.commands.vcs.push.write_output")
    @patch(
        "dev.scripts.devctl.commands.vcs.push.repair_preflight_generated_changes_for_push"
    )
    @patch("dev.scripts.devctl.commands.vcs.push.remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.load_push_policy")
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    @patch("dev.scripts.devctl.commands.vcs.push.publication_authorization_decision")
    def test_push_blocks_dirty_tree_even_with_publication_authorization(
        self,
        publication_authorization_mock,
        collect_git_status_mock,
        load_policy_mock,
        _remote_exists_mock,
        refresh_generated_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "branch": "feature/demo",
            "changes": [{"path": "tracked.py"}],
        }
        load_policy_mock.return_value = make_policy()
        publication_authorization_mock.return_value = _publication_authorization()

        rc = push.run(make_args(execute=True))

        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["status"], "blocked")
        self.assertIn("Working tree has uncommitted changes", payload["errors"][0])
        refresh_generated_mock.assert_not_called()

    @patch("dev.scripts.devctl.commands.vcs.push_preflight_commit.run_git_capture")
    @patch("dev.scripts.devctl.commands.vcs.push_preflight_commit.collect_git_status")
    def test_preflight_autocommit_collects_git_status_from_target_repo(
        self,
        collect_git_status_mock,
        run_git_capture_mock,
    ) -> None:
        repo_root = Path("/tmp/target-repo")
        collect_git_status_mock.return_value = {
            "changes": [
                {
                    "path": "generated.py",
                    "status": "M",
                    "raw_status": " M",
                    "index_status": " ",
                    "worktree_status": "M",
                }
            ]
        }
        run_git_capture_mock.side_effect = [
            (0, "", ""),
            (0, "", ""),
        ]
        state = SimpleNamespace(errors=[])

        push_preflight_commit.auto_commit_preflight_generated_changes(
            state,
            make_policy(),
            repo_root=repo_root,
        )

        collect_git_status_mock.assert_called_once_with(repo_root=repo_root)
        self.assertEqual(state.errors, [])

    @patch("dev.scripts.devctl.commands.vcs.push_preflight_commit.run_git_capture")
    @patch("dev.scripts.devctl.commands.vcs.push_preflight_commit.collect_git_status")
    def test_preflight_autocommit_ignores_staged_only_paths(
        self,
        collect_git_status_mock,
        run_git_capture_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [
                {
                    "path": "next_commit.py",
                    "status": "M",
                    "raw_status": "M ",
                    "index_status": "M",
                    "worktree_status": " ",
                }
            ]
        }
        state = SimpleNamespace(errors=[])

        push_preflight_commit.auto_commit_preflight_generated_changes(
            state,
            make_policy(),
        )

        run_git_capture_mock.assert_not_called()
        self.assertEqual(state.errors, [])

    @patch("dev.scripts.devctl.commands.vcs.push_preflight_commit.run_git_capture")
    @patch("dev.scripts.devctl.commands.vcs.push_preflight_commit.collect_git_status")
    def test_selected_generated_surface_commit_preserves_staged_only_paths(
        self,
        collect_git_status_mock,
        run_git_capture_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [
                {
                    "path": "dev/guides/SYSTEM_MAP.md",
                    "status": "M",
                    "raw_status": " M",
                    "index_status": " ",
                    "worktree_status": "M",
                },
                {
                    "path": "next_commit.py",
                    "status": "M",
                    "raw_status": "M ",
                    "index_status": "M",
                    "worktree_status": " ",
                },
            ]
        }
        run_git_capture_mock.side_effect = [
            (0, "abc1234", ""),
            (0, "", ""),
            (0, "", ""),
            (0, "surface-receipt", ""),
        ]
        state = SimpleNamespace(errors=[])

        result = push_preflight_commit.auto_commit_selected_preflight_generated_changes(
            state,
            make_policy(),
            allowed_paths=("dev/guides/SYSTEM_MAP.md",),
        )

        self.assertTrue(result["committed"])
        self.assertEqual(
            run_git_capture_mock.call_args_list[2].args[0],
            [
                "commit",
                "-m",
                "Refresh policy-owned generated surfaces for abc1234",
                "--",
                "dev/guides/SYSTEM_MAP.md",
            ],
        )
        self.assertEqual(state.errors, [])

    @patch("dev.scripts.devctl.commands.vcs.push_preflight_commit.run_git_capture")
    @patch("dev.scripts.devctl.commands.vcs.push_preflight_commit.collect_git_status")
    def test_preflight_autocommit_uses_git_subcommands_without_double_prefix(
        self,
        collect_git_status_mock,
        run_git_capture_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [
                {
                    "path": "generated.py",
                    "status": "M",
                    "raw_status": " M",
                    "index_status": " ",
                    "worktree_status": "M",
                }
            ]
        }
        run_git_capture_mock.side_effect = [
            (0, "", ""),
            (0, "", ""),
        ]
        state = SimpleNamespace(errors=[])

        push_preflight_commit.auto_commit_preflight_generated_changes(
            state,
            make_policy(),
        )

        self.assertEqual(
            run_git_capture_mock.call_args_list[0].args[0],
            ["add", "--", "generated.py"],
        )
        self.assertEqual(
            run_git_capture_mock.call_args_list[1].args[0],
            [
                "commit",
                "-m",
                "chore(push): auto-commit preflight-generated changes",
                "--",
                "generated.py",
            ],
        )
        self.assertEqual(state.errors, [])

    @patch("dev.scripts.devctl.commands.vcs.push_preflight_commit.run_git_capture")
    @patch("dev.scripts.devctl.commands.vcs.push_preflight_commit.collect_git_status")
    def test_preflight_autocommit_surfaces_git_add_failures(
        self,
        collect_git_status_mock,
        run_git_capture_mock,
    ) -> None:
        collect_git_status_mock.return_value = {
            "changes": [
                {
                    "path": "generated.py",
                    "status": "M",
                    "raw_status": " M",
                    "index_status": " ",
                    "worktree_status": "M",
                }
            ]
        }
        run_git_capture_mock.return_value = (128, "", "fatal: bad add")
        state = SimpleNamespace(errors=[])

        push_preflight_commit.auto_commit_preflight_generated_changes(
            state,
            make_policy(),
        )

        self.assertEqual(
            state.errors,
            [
                "Preflight generated 1 dirty path(s) but git add failed for generated.py: fatal: bad add"
            ],
        )

    @patch("dev.scripts.devctl.commands.vcs.push_projection_receipt.run_git_capture")
    @patch(
        "dev.scripts.devctl.commands.vcs.push_projection_receipt.scan_repo_governance_safely",
        return_value=None,
    )
    def test_projection_receipt_commits_managed_bridge_drift_before_push(
        self,
        _scan_governance_mock,
        run_git_capture_mock,
    ) -> None:
        run_git_capture_mock.side_effect = [
            (0, " M bridge.md", ""),
            (0, "", ""),
            (0, "", ""),
            (0, "bridge.md", ""),
            (0, "abc1234", ""),
            (0, "", ""),
            (0, "receipt-sha", ""),
        ]
        state = SimpleNamespace(errors=[], warnings=[])

        push_projection_receipt.auto_commit_managed_projection_receipt(
            state,
            make_policy(
                checkpoint=PushCheckpointPolicy(
                    compatibility_projection_paths=("bridge.md",),
                )
            ),
        )

        self.assertEqual(state.errors, [])
        self.assertEqual(
            state.warnings,
            [
                "Committed managed projection receipt receipt-sha for bridge.md before push."
            ],
        )
        self.assertEqual(
            run_git_capture_mock.call_args_list[2].args[0],
            ["add", "--", "bridge.md"],
        )
        self.assertEqual(
            run_git_capture_mock.call_args_list[5].args[0],
            [
                "commit",
                "-m",
                "Refresh external review snapshot for abc1234",
                "--",
                "bridge.md",
            ],
        )

    @patch("dev.scripts.devctl.commands.vcs.push_projection_receipt.run_git_capture")
    @patch(
        "dev.scripts.devctl.commands.vcs.push_projection_receipt.scan_repo_governance_safely",
        return_value=None,
    )
    def test_projection_receipt_commits_bridge_and_review_snapshot_drift(
        self,
        _scan_governance_mock,
        run_git_capture_mock,
    ) -> None:
        run_git_capture_mock.side_effect = [
            (0, " M bridge.md\n M dev/audits/REVIEW_SNAPSHOT.md", ""),
            (0, "", ""),
            (0, "", ""),
            (0, "bridge.md\ndev/audits/REVIEW_SNAPSHOT.md", ""),
            (0, "abc1234", ""),
            (0, "", ""),
            (0, "receipt-sha", ""),
        ]
        state = SimpleNamespace(errors=[], warnings=[])

        push_projection_receipt.auto_commit_managed_projection_receipt(
            state,
            make_policy(
                checkpoint=PushCheckpointPolicy(
                    compatibility_projection_paths=("bridge.md",),
                )
            ),
        )

        self.assertEqual(state.errors, [])
        self.assertEqual(
            run_git_capture_mock.call_args_list[2].args[0],
            ["add", "--", "bridge.md", "dev/audits/REVIEW_SNAPSHOT.md"],
        )
        self.assertEqual(
            state.warnings,
            [
                "Committed managed projection receipt receipt-sha for "
                "bridge.md, dev/audits/REVIEW_SNAPSHOT.md before push."
            ],
        )

    @patch("dev.scripts.devctl.commands.vcs.push_projection_receipt.run_git_capture")
    @patch(
        "dev.scripts.devctl.commands.vcs.push_projection_receipt.scan_repo_governance_safely",
        return_value=None,
    )
    def test_projection_receipt_ignores_mixed_source_dirty_state(
        self,
        _scan_governance_mock,
        run_git_capture_mock,
    ) -> None:
        run_git_capture_mock.side_effect = [
            (0, " M bridge.md\n M source.py", ""),
        ]
        state = SimpleNamespace(errors=[], warnings=[])

        push_projection_receipt.auto_commit_managed_projection_receipt(
            state,
            make_policy(
                checkpoint=PushCheckpointPolicy(
                    compatibility_projection_paths=("bridge.md",),
                )
            ),
        )

        self.assertEqual(state.errors, [])
        self.assertEqual(state.warnings, [])
        self.assertEqual(run_git_capture_mock.call_count, 1)

    @patch("dev.scripts.devctl.commands.vcs.push_projection_receipt.run_git_capture")
    @patch(
        "dev.scripts.devctl.commands.vcs.push_projection_receipt.scan_repo_governance_safely",
        return_value=None,
    )
    def test_projection_receipt_preserves_staged_only_next_commit_intent(
        self,
        _scan_governance_mock,
        run_git_capture_mock,
    ) -> None:
        run_git_capture_mock.side_effect = [
            (0, " M bridge.md\nM  next_commit.py", ""),
            (0, "next_commit.py", ""),
            (0, "", ""),
            (0, "bridge.md\nnext_commit.py", ""),
            (0, "abc1234", ""),
            (0, "", ""),
            (0, "receipt-sha", ""),
        ]
        state = SimpleNamespace(errors=[], warnings=[])

        push_projection_receipt.auto_commit_managed_projection_receipt(
            state,
            make_policy(
                checkpoint=PushCheckpointPolicy(
                    compatibility_projection_paths=("bridge.md",),
                )
            ),
        )

        self.assertEqual(state.errors, [])
        self.assertEqual(
            run_git_capture_mock.call_args_list[5].args[0],
            [
                "commit",
                "-m",
                "Refresh external review snapshot for abc1234",
                "--",
                "bridge.md",
            ],
        )
        self.assertEqual(
            state.warnings,
            [
                "Committed managed projection receipt receipt-sha for bridge.md before push."
            ],
        )

    @patch("dev.scripts.devctl.commands.vcs.push.write_output")
    @patch(
        "dev.scripts.devctl.commands.vcs.push.current_upstream_ref",
        return_value="",
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.build_preflight_shell_command",
        return_value="python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute",
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.remote_branch_exists", return_value=False
    )
    @patch("dev.scripts.devctl.commands.vcs.push.remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.load_push_policy")
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    @patch("dev.scripts.devctl.commands.vcs.push.run_cmd")
    @patch("dev.scripts.devctl.commands.vcs.push.publication_authorization_decision")
    def test_push_policy_gated_skip_post_push_reports_remote_publication(
        self,
        publication_authorization_mock,
        run_cmd_mock,
        collect_git_status_mock,
        load_policy_mock,
        _remote_exists_mock,
        _remote_branch_exists_mock,
        _preflight_command_mock,
        _current_upstream_ref_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {"branch": "feature/demo", "changes": []}
        load_policy_mock.return_value = make_policy(
            bypass=PushBypassPolicy(allow_skip_post_push=True),
        )
        publication_authorization_mock.return_value = _publication_authorization()

        def _run_cmd(name, cmd, cwd=None, env=None):
            del env
            return {
                "name": name,
                "cmd": list(cmd),
                "cwd": str(cwd or "."),
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            }

        run_cmd_mock.side_effect = _run_cmd

        with patch.object(
            push_preflight_projection,
            "auto_commit_managed_projection_receipt",
            return_value={"ok": True, "committed": False, "paths": ()},
        ):
            rc = push.run(make_args(execute=True, skip_post_push=True))

        self.assertEqual(rc, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["status"], "published_remote")
        self.assertEqual(payload["reason"], "post_push_skipped_by_policy")
        self.assertTrue(payload["action_result"]["partial_progress"])
        self.assertEqual(
            payload["action_result"]["artifact_paths"],
            ["dev/reports/push/latest.json"],
        )
        self.assertEqual(
            payload["push_stages"],
            {
                "validation_ready": True,
                "published_remote": True,
                "post_push_green": False,
            },
        )

    @patch("dev.scripts.devctl.commands.vcs.push.write_output")
    @patch(
        "dev.scripts.devctl.commands.vcs.push.build_post_push_commands",
        return_value=["git status"],
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.current_upstream_ref",
        return_value="",
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.build_preflight_shell_command",
        return_value="python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute",
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.remote_branch_exists", return_value=False
    )
    @patch("dev.scripts.devctl.commands.vcs.push.remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.load_push_policy")
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    @patch("dev.scripts.devctl.commands.vcs.push.run_cmd")
    @patch("dev.scripts.devctl.commands.vcs.push.publication_authorization_decision")
    def test_push_post_push_failure_reports_remote_published_not_green(
        self,
        publication_authorization_mock,
        run_cmd_mock,
        collect_git_status_mock,
        load_policy_mock,
        _remote_exists_mock,
        _remote_branch_exists_mock,
        _preflight_command_mock,
        _current_upstream_ref_mock,
        _post_push_commands_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {"branch": "feature/demo", "changes": []}
        load_policy_mock.return_value = make_policy()
        publication_authorization_mock.return_value = _publication_authorization()

        def _run_cmd(name, cmd, cwd=None, env=None):
            del env
            return {
                "name": name,
                "cmd": list(cmd),
                "cwd": str(cwd or "."),
                "returncode": 1 if name == "push-post-01" else 0,
                "duration_s": 0.1,
                "skipped": False,
            }

        run_cmd_mock.side_effect = _run_cmd

        with (
            patch.object(
                push_preflight_projection,
                "auto_commit_managed_projection_receipt",
                return_value={"ok": True, "committed": False, "paths": ()},
            ),
            patch.object(
                push_preflight_projection,
                "refresh_stale_reviewer_heartbeat_before_publication",
                return_value={
                    "step": "reviewer_heartbeat_refresh",
                    "status": "skipped",
                    "reason": "unit_test",
                },
            ),
        ):
            rc = push.run(make_args(execute=True))

        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["status"], "published_remote")
        self.assertEqual(payload["reason"], "post_push_bundle_failed")
        self.assertTrue(payload["action_result"]["partial_progress"])
        self.assertEqual(
            payload["action_result"]["artifact_paths"],
            ["dev/reports/push/latest.json"],
        )
        self.assertEqual(
            payload["push_stages"],
            {
                "validation_ready": True,
                "published_remote": True,
                "post_push_green": False,
            },
        )

    @patch("dev.scripts.devctl.commands.vcs.push.persist_published_remote_snapshot")
    @patch("dev.scripts.devctl.commands.vcs.push.persist_push_progress_snapshot")
    @patch(
        "dev.scripts.devctl.commands.vcs.push.current_head_commit_sha",
        return_value="abc123",
    )
    @patch("dev.scripts.devctl.commands.vcs.push.write_output")
    @patch(
        "dev.scripts.devctl.commands.vcs.push.build_post_push_commands",
        return_value=["git status"],
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.current_upstream_ref",
        return_value="",
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.build_preflight_shell_command",
        return_value="python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute",
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.remote_branch_exists", return_value=False
    )
    @patch("dev.scripts.devctl.commands.vcs.push.remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.load_push_policy")
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    @patch("dev.scripts.devctl.commands.vcs.push.run_cmd")
    @patch("dev.scripts.devctl.commands.vcs.push.publication_authorization_decision")
    def test_push_persists_remote_publication_snapshot_before_post_push_bundle_finishes(
        self,
        publication_authorization_mock,
        run_cmd_mock,
        collect_git_status_mock,
        load_policy_mock,
        _remote_exists_mock,
        _remote_branch_exists_mock,
        _preflight_command_mock,
        _current_upstream_ref_mock,
        _post_push_commands_mock,
        write_output_mock,
        _current_head_commit_mock,
        persist_push_progress_snapshot_mock,
        persist_published_remote_snapshot_mock,
    ) -> None:
        collect_git_status_mock.return_value = {"branch": "feature/demo", "changes": []}
        load_policy_mock.return_value = make_policy()
        publication_authorization_mock.return_value = _publication_authorization()

        def _run_cmd(name, cmd, cwd=None, env=None):
            del env
            return {
                "name": name,
                "cmd": list(cmd),
                "cwd": str(cwd or "."),
                "returncode": 1 if name == "push-post-01" else 0,
                "duration_s": 0.1,
                "skipped": False,
            }

        run_cmd_mock.side_effect = _run_cmd

        with (
            patch.object(
                push_preflight_projection,
                "auto_commit_managed_projection_receipt",
                return_value={"ok": True, "committed": False, "paths": ()},
            ),
            patch.object(
                push_preflight_projection,
                "refresh_stale_reviewer_heartbeat_before_publication",
                return_value={
                    "step": "reviewer_heartbeat_refresh",
                    "status": "skipped",
                    "reason": "unit_test",
                },
            ),
        ):
            rc = push.run(make_args(execute=True))

        self.assertEqual(rc, 1)
        self.assertEqual(
            [
                call.kwargs["reason"]
                for call in persist_push_progress_snapshot_mock.call_args_list
            ],
            ["push_preflight_running", "push_pending"],
        )
        first_context = persist_push_progress_snapshot_mock.call_args_list[0].args[0]
        self.assertEqual(first_context.head_commit, "abc123")
        self.assertEqual(first_context.state.branch, "feature/demo")
        second_context = persist_push_progress_snapshot_mock.call_args_list[1].args[0]
        self.assertEqual(
            second_context.approved_target_identity,
            "tree-receipt-20260403T010000Z:tree-123",
        )
        persist_published_remote_snapshot_mock.assert_called_once()
        persisted_payload = persist_published_remote_snapshot_mock.call_args.args[0]
        self.assertEqual(persisted_payload.head_commit, "abc123")
        self.assertEqual(persisted_payload.state.branch, "feature/demo")
        self.assertEqual(
            persist_published_remote_snapshot_mock.call_args.kwargs["reason"],
            "post_push_bundle_pending",
        )
        self.assertTrue(
            persist_published_remote_snapshot_mock.call_args.kwargs["partial_progress"]
        )
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["status"], "published_remote")

    @patch("dev.scripts.devctl.commands.vcs.push.write_output")
    @patch(
        "dev.scripts.devctl.commands.vcs.push.build_post_push_commands",
        return_value=["git status"],
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.current_upstream_ref",
        return_value="origin/feature/demo",
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.build_preflight_shell_command",
        return_value="python3 dev/scripts/devctl.py check-router --since-ref origin/feature/demo --execute",
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.branch_divergence",
        return_value={"behind": 0, "ahead": 1, "error": None},
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.remote_branch_exists", return_value=True
    )
    @patch("dev.scripts.devctl.commands.vcs.push.remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.load_push_policy")
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    @patch("dev.scripts.devctl.commands.vcs.push.run_cmd")
    @patch("dev.scripts.devctl.commands.vcs.push.publication_authorization_decision")
    def test_push_existing_remote_branch_scopes_post_push_bundle_to_branch_ref(
        self,
        publication_authorization_mock,
        run_cmd_mock,
        collect_git_status_mock,
        load_policy_mock,
        _remote_exists_mock,
        _remote_branch_exists_mock,
        _branch_divergence_mock,
        _preflight_command_mock,
        _current_upstream_ref_mock,
        _post_push_commands_mock,
        write_output_mock,
    ) -> None:
        collect_git_status_mock.return_value = {"branch": "feature/demo", "changes": []}
        load_policy_mock.return_value = make_policy()
        publication_authorization_mock.return_value = _publication_authorization()
        run_cmd_mock.side_effect = [
            {
                "name": "git-fetch",
                "cmd": ["git", "fetch", "origin"],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            },
            {
                "name": "push-refresh-render-surfaces",
                "cmd": [
                    "python3",
                    "dev/scripts/devctl.py",
                    "render-surfaces",
                    "--write",
                    "--format",
                    "json",
                ],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            },
            {
                "name": "push-preflight",
                "cmd": [
                    "bash",
                    "-lc",
                    "python3 dev/scripts/devctl.py check-router --since-ref origin/feature/demo --execute",
                ],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            },
            {
                "name": "git-push",
                "cmd": ["git", "push", "origin", "feature/demo"],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            },
            {
                "name": "push-post-01",
                "cmd": ["bash", "-lc", "git status"],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            },
        ]

        with (
            patch.object(
                push_preflight_projection,
                "auto_commit_managed_projection_receipt",
                return_value={"ok": True, "committed": False, "paths": ()},
            ),
            patch.object(
                push_preflight_projection,
                "refresh_stale_reviewer_heartbeat_before_publication",
                return_value={
                    "step": "reviewer_heartbeat_refresh",
                    "status": "skipped",
                    "reason": "unit_test",
                },
            ),
        ):
            rc = push.run(make_args(execute=True))

        self.assertEqual(rc, 0)
        _post_push_commands_mock.assert_called_once_with(
            load_policy_mock.return_value,
            quality_policy_path=None,
            since_ref="origin/feature/demo",
        )
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["status"], "post_push_green")

    def test_execute_push_flow_emits_publication_and_post_push_progress_notices(
        self,
    ) -> None:
        state = push.PushRunState(
            branch="feature/demo",
            remote="origin",
            branch_has_remote=False,
            post_push_since_ref="origin/develop",
        )
        policy = make_policy()
        args = make_args(execute=True)
        progress_messages: list[str] = []

        outcome = push.execute_push_flow_with_dependencies(
            state,
            policy,
            args,
            push.PushFlowDependencies(
                run_cmd_fn=lambda name, cmd, cwd=None, env=None: {
                    "name": name,
                    "cmd": cmd,
                    "cwd": str(cwd or "."),
                    "returncode": 0,
                    "duration_s": 0.1,
                    "skipped": False,
                },
                build_post_push_commands_fn=lambda _policy, quality_policy_path=None, since_ref=None: [
                    "git status",
                    "git log --oneline --decorate -n 10",
                ],
                published_remote_snapshot_fn=lambda reason, operator_guidance, partial_progress: None,
                progress_notice_fn=progress_messages.append,
            ),
        )

        self.assertTrue(outcome.ok)
        self.assertEqual(
            progress_messages[0],
            "Remote publication recorded for the current HEAD; running post-push bundle.",
        )
        self.assertEqual(progress_messages[1], "Post-push step 1/2: git status")
        self.assertEqual(
            progress_messages[2],
            "Post-push step 2/2: git log --oneline --decorate -n 10",
        )

    def test_execute_push_flow_emits_failure_progress_notice(self) -> None:
        state = push.PushRunState(
            branch="feature/demo",
            remote="origin",
            post_push_since_ref="origin/develop",
        )
        policy = make_policy()
        args = make_args(execute=True)
        progress_messages: list[str] = []

        outcome = push.execute_push_flow_with_dependencies(
            state,
            policy,
            args,
            push.PushFlowDependencies(
                run_cmd_fn=lambda name, cmd, cwd=None, env=None: {
                    "name": name,
                    "cmd": cmd,
                    "cwd": str(cwd or "."),
                    "returncode": 1 if name == "push-post-02" else 0,
                    "duration_s": 0.1,
                    "skipped": False,
                },
                build_post_push_commands_fn=lambda _policy, quality_policy_path=None, since_ref=None: [
                    "git status",
                    "git log --oneline --decorate -n 10",
                ],
                published_remote_snapshot_fn=lambda reason, operator_guidance, partial_progress: None,
                progress_notice_fn=progress_messages.append,
            ),
        )

        self.assertFalse(outcome.ok)
        self.assertEqual(
            progress_messages[0],
            "Remote publication recorded for the current HEAD; running post-push bundle.",
        )
        self.assertEqual(
            progress_messages[1],
            "Post-push step 1/2: git status",
        )
        self.assertEqual(
            progress_messages[2],
            "Post-push step 2/2: git log --oneline --decorate -n 10",
        )
        self.assertEqual(
            progress_messages[3],
            "Post-push step 2/2 failed with rc=1.",
        )

    def test_build_preflight_shell_command_prefers_remote_branch_when_it_exists(
        self,
    ) -> None:
        policy = make_policy()

        command = push.build_preflight_shell_command(
            policy,
            remote="origin",
            route_state=push.PushRefRoutingState(
                current_branch="feature/demo",
                upstream_ref="origin/feature/demo",
                branch_has_remote=True,
            ),
        )

        self.assertIn("--since-ref origin/feature/demo", command)

    def test_build_post_push_commands_rewrites_since_ref_for_runtime_scope(
        self,
    ) -> None:
        commands = build_post_push_commands(
            make_policy(),
            since_ref="origin/feature/demo",
        )

        self.assertTrue(
            any(
                command.endswith(
                    "dev/scripts/devctl.py docs-check --user-facing --since-ref origin/feature/demo"
                )
                for command in commands
            )
        )
        self.assertTrue(
            any(
                command.endswith(
                    "dev/scripts/checks/check_code_shape.py --since-ref origin/feature/demo"
                )
                for command in commands
            )
        )
        self.assertFalse(
            any(
                command.endswith(
                    "dev/scripts/checks/check_code_shape.py --since-ref origin/develop"
                )
                for command in commands
            )
        )


class PushLiveExecutionTests(unittest.TestCase):
    def test_execute_populates_real_fetch_preflight_and_push_returncodes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            repo_root = tmp_root / "repo"
            remote_root = tmp_root / "remote.git"
            _run_git(tmp_root, "init", "--bare", str(remote_root))
            _run_git(tmp_root, "init", str(repo_root))
            _run_git(repo_root, "config", "user.email", "test@example.com")
            _run_git(repo_root, "config", "user.name", "Test User")
            _run_git(repo_root, "checkout", "-b", "feature/live-push")
            (repo_root / "tracked.txt").write_text("initial\n", encoding="utf-8")
            _run_git(repo_root, "add", "tracked.txt")
            _run_git(repo_root, "commit", "-m", "initial")
            _run_git(repo_root, "remote", "add", "origin", str(remote_root))
            _run_git(repo_root, "push", "-u", "origin", "feature/live-push")
            (repo_root / "tracked.txt").write_text("updated\n", encoding="utf-8")
            _run_git(repo_root, "commit", "-am", "update tracked file")

            policy = make_policy(
                development_branch="main",
                release_branch="main",
                protected_branches=("main",),
            )

            def _record_projection_phase(_state, _policy, **_kwargs):
                _state.pre_validation_managed_projection_sync = {
                    "phase": "pre_validation_managed_projection_sync",
                    "status": "completed",
                    "ok": True,
                }

            with (
                patch(
                    "dev.scripts.devctl.commands.vcs.push.build_preflight_shell_command",
                    return_value="git status --short",
                ),
                patch(
                    "dev.scripts.devctl.commands.vcs.push.refresh_managed_projections_before_preflight",
                    side_effect=_record_projection_phase,
                ),
            ):
                rc, report = push.run_push_action(
                    make_args(execute=True),
                    repo_root=repo_root,
                    policy=policy,
                    emit_output_report=False,
                    run_cmd_fn=push.run_cmd,
                    build_post_push_commands_fn=lambda _policy, **_kwargs: [],
                    publication_authorization_fn=lambda **_kwargs: _publication_authorization(
                        approved_target_identity="tree-receipt-live:tracked"
                    ),
                )

            self.assertEqual(rc, 0)
            self.assertEqual(report["branch"], "feature/live-push")
            self.assertEqual(
                report["typed_action"]["parameters"]["branch"],
                "feature/live-push",
            )
            self.assertEqual(
                report["approved_target_identity"],
                "tree-receipt-live:tracked",
            )
            for step_name in ("fetch_step", "preflight_step", "push_step"):
                self.assertIsNotNone(report[step_name])
                self.assertEqual(report[step_name]["returncode"], 0)
            self.assertEqual(report["fetch_step"]["name"], "git-fetch")
            self.assertEqual(report["preflight_step"]["name"], "push-preflight")
            self.assertEqual(report["push_step"]["name"], "git-push")
            self.assertEqual(
                _run_git(remote_root, "rev-parse", "refs/heads/feature/live-push"),
                _run_git(repo_root, "rev-parse", "HEAD"),
            )
            self.assertEqual(
                _run_git(
                    repo_root,
                    "rev-list",
                    "--count",
                    "origin/feature/live-push..HEAD",
                ),
                "0",
            )


class PushReceiptTests(unittest.TestCase):
    """Tests for the append-only push receipt history."""

    def setUp(self) -> None:
        import tempfile

        self._tmpdir = tempfile.mkdtemp()
        self._repo_root = Path(self._tmpdir)
        # Create the push report directory structure expected by repo pack
        push_dir = self._repo_root / "dev" / "reports" / "push"
        push_dir.mkdir(parents=True, exist_ok=True)
        # Write a minimal latest.json so the resolve path works
        (push_dir / "latest.json").write_text("{}", encoding="utf-8")

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self._tmpdir, ignore_errors=True)

    @patch(
        "dev.scripts.devctl.commands.vcs.push_artifact.active_path_config",
    )
    def test_append_push_receipt_creates_history_file(self, path_config_mock) -> None:
        from dev.scripts.devctl.commands.vcs.push_artifact import append_push_receipt

        path_config_mock.return_value = SimpleNamespace(
            push_report_rel="dev/reports/push/latest.json",
        )
        report = {
            "branch": "feature/demo",
            "head_commit": "abc123",
            "status": "post_push_green",
        }

        result_path = append_push_receipt(report, repo_root=self._repo_root)

        self.assertTrue(result_path.exists())
        lines = result_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 1)
        entry = json.loads(lines[0])
        self.assertEqual(entry["branch"], "feature/demo")
        self.assertEqual(entry["head_commit"], "abc123")

    @patch(
        "dev.scripts.devctl.commands.vcs.push_artifact.active_path_config",
    )
    def test_append_push_receipt_appends_multiple_entries(
        self, path_config_mock
    ) -> None:
        from dev.scripts.devctl.commands.vcs.push_artifact import append_push_receipt

        path_config_mock.return_value = SimpleNamespace(
            push_report_rel="dev/reports/push/latest.json",
        )
        for i in range(3):
            append_push_receipt(
                {"branch": "feature/demo", "head_commit": f"sha-{i}"},
                repo_root=self._repo_root,
            )

        history_path = (
            self._repo_root / "dev" / "reports" / "push" / "history" / "receipts.jsonl"
        )
        lines = history_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 3)
        self.assertEqual(json.loads(lines[2])["head_commit"], "sha-2")

    @patch(
        "dev.scripts.devctl.commands.vcs.push_artifact.active_path_config",
    )
    def test_lookup_push_receipt_finds_matching_entry(self, path_config_mock) -> None:
        from dev.scripts.devctl.commands.vcs.push_artifact import (
            append_push_receipt,
            lookup_push_receipt,
        )

        path_config_mock.return_value = SimpleNamespace(
            push_report_rel="dev/reports/push/latest.json",
        )
        append_push_receipt(
            {"branch": "feature/demo", "head_commit": "old-sha", "status": "stale"},
            repo_root=self._repo_root,
        )
        append_push_receipt(
            {"branch": "feature/demo", "head_commit": "new-sha", "status": "fresh"},
            repo_root=self._repo_root,
        )

        result = lookup_push_receipt(
            branch="feature/demo",
            head_commit="new-sha",
            repo_root=self._repo_root,
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "fresh")

    @patch(
        "dev.scripts.devctl.commands.vcs.push_artifact.active_path_config",
    )
    def test_lookup_push_receipt_returns_none_for_nonmatching(
        self, path_config_mock
    ) -> None:
        from dev.scripts.devctl.commands.vcs.push_artifact import (
            append_push_receipt,
            lookup_push_receipt,
        )

        path_config_mock.return_value = SimpleNamespace(
            push_report_rel="dev/reports/push/latest.json",
        )
        append_push_receipt(
            {"branch": "feature/other", "head_commit": "abc123"},
            repo_root=self._repo_root,
        )

        result = lookup_push_receipt(
            branch="feature/demo",
            head_commit="abc123",
            repo_root=self._repo_root,
        )

        self.assertIsNone(result)

    @patch(
        "dev.scripts.devctl.commands.vcs.push_artifact.active_path_config",
    )
    def test_lookup_push_receipt_handles_missing_file(self, path_config_mock) -> None:
        from dev.scripts.devctl.commands.vcs.push_artifact import lookup_push_receipt

        path_config_mock.return_value = SimpleNamespace(
            push_report_rel="dev/reports/push/latest.json",
        )

        result = lookup_push_receipt(
            branch="feature/demo",
            head_commit="abc123",
            repo_root=self._repo_root,
        )

        self.assertIsNone(result)

    @patch(
        "dev.scripts.devctl.governance.push_state.latest_push_report_relpath",
        return_value="dev/reports/push/latest.json",
    )
    @patch(
        "dev.scripts.devctl.governance.push_state.load_remote_commit_pipeline_contract",
        return_value=SimpleNamespace(approved_target_identity=""),
    )
    @patch(
        "dev.scripts.devctl.governance.push_state.load_latest_push_report",
        return_value={
            "branch": "feature/demo",
            "remote": "origin",
            "head_commit": "stale-head",
            "push_stages": {
                "validation_ready": True,
                "published_remote": False,
                "post_push_green": False,
            },
        },
    )
    @patch(
        "dev.scripts.devctl.governance.push_state.lookup_push_receipt",
        return_value={
            "branch": "feature/demo",
            "remote": "origin",
            "head_commit": "current-head",
            "push_stages": {
                "validation_ready": True,
                "published_remote": True,
                "post_push_green": True,
            },
        },
    )
    @patch("dev.scripts.devctl.governance.push_state._git_stdout")
    def test_detect_push_enforcement_prefers_receipt_over_stale_latest(
        self,
        git_stdout_mock,
        _lookup_receipt_mock,
        _load_latest_mock,
        _load_pipeline_mock,
        _relpath_mock,
    ) -> None:
        def _fake_git_stdout(_repo_root, *cmd):
            values = {
                ("rev-parse", "--git-path", "hooks/pre-push"): "",
                ("rev-parse", "--abbrev-ref", "HEAD"): "feature/demo",
                ("rev-parse", "HEAD"): "current-head",
                (
                    "rev-parse",
                    "--abbrev-ref",
                    "--symbolic-full-name",
                    "@{u}",
                ): "origin/feature/demo",
                ("rev-list", "--count", "origin/feature/demo..HEAD"): "1",
                ("status", "--porcelain", "--untracked-files=all"): "",
            }
            return values.get(cmd, "")

        git_stdout_mock.side_effect = _fake_git_stdout

        state = detect_push_enforcement_state(make_policy())

        self.assertEqual(state["recommended_action"], "no_push_needed")
        self.assertFalse(state["latest_push_report_published_remote"])
        self.assertFalse(state["latest_push_report_post_push_green"])
        self.assertFalse(state["latest_push_report_matches_current_head"])
        self.assertEqual(state["selected_push_report_source"], "receipt_history")
        self.assertTrue(state["selected_push_report_published_remote"])
        self.assertTrue(state["selected_push_report_post_push_green"])
        self.assertTrue(state["selected_push_report_matches_current_head"])

    @patch(
        "dev.scripts.devctl.governance.push_state.latest_push_report_relpath",
        return_value="dev/reports/push/latest.json",
    )
    @patch(
        "dev.scripts.devctl.governance.push_state.load_remote_commit_pipeline_contract",
        return_value=SimpleNamespace(approved_target_identity="tree-receipt-1"),
    )
    @patch(
        "dev.scripts.devctl.governance.push_state.load_latest_push_report",
        return_value={
            "branch": "feature/demo",
            "remote": "origin",
            "head_commit": "current-head",
            "reason": "push_pending",
            "approved_target_identity": "tree-receipt-1",
            "push_stages": {
                "validation_ready": True,
                "published_remote": False,
                "post_push_green": False,
            },
        },
    )
    @patch(
        "dev.scripts.devctl.governance.push_state.lookup_push_receipt",
        return_value={
            "branch": "feature/demo",
            "remote": "origin",
            "head_commit": "current-head",
            "reason": "validation_failed",
            "approved_target_identity": "tree-receipt-1",
            "push_stages": {
                "validation_ready": False,
                "published_remote": False,
                "post_push_green": False,
            },
        },
    )
    @patch("dev.scripts.devctl.governance.push_state._git_stdout")
    def test_detect_push_enforcement_prefers_current_head_inflight_latest_over_receipt(
        self,
        git_stdout_mock,
        _lookup_receipt_mock,
        _load_latest_mock,
        _load_pipeline_mock,
        _relpath_mock,
    ) -> None:
        def _fake_git_stdout(_repo_root, *cmd):
            values = {
                ("rev-parse", "--git-path", "hooks/pre-push"): "",
                ("rev-parse", "--abbrev-ref", "HEAD"): "feature/demo",
                ("rev-parse", "HEAD"): "current-head",
                (
                    "rev-parse",
                    "--abbrev-ref",
                    "--symbolic-full-name",
                    "@{u}",
                ): "origin/feature/demo",
                ("rev-list", "--count", "origin/feature/demo..HEAD"): "1",
                ("status", "--porcelain", "--untracked-files=all"): "",
            }
            return values.get(cmd, "")

        git_stdout_mock.side_effect = _fake_git_stdout

        state = detect_push_enforcement_state(make_policy())

        self.assertEqual(state["latest_push_report_reason"], "push_pending")
        self.assertEqual(state["latest_push_report_head_commit"], "current-head")
        self.assertTrue(state["latest_push_report_matches_current_head"])
        self.assertEqual(state["selected_push_report_source"], "latest_artifact")
        self.assertEqual(state["selected_push_report_reason"], "push_pending")
        self.assertEqual(state["selected_push_report_head_commit"], "current-head")
        self.assertTrue(state["selected_push_report_matches_current_head"])


class PushPipelineStateSyncTests(unittest.TestCase):
    def test_project_push_report_keeps_branch_already_pushed_as_partial_progress(
        self,
    ) -> None:
        projection = project_push_report(
            action_id="vcs.push",
            report={
                "reason": "branch_already_pushed",
                "artifacts": {"latest_json": "dev/reports/push/latest.json"},
                "push_stages": {
                    "validation_ready": True,
                    "published_remote": True,
                    "post_push_green": False,
                },
            },
            pipeline_artifact_relpath="dev/reports/commit_pipeline.json",
        )

        self.assertEqual(projection.next_state, "push_blocked")
        self.assertEqual(projection.blocked_reason, "branch_already_pushed")
        self.assertFalse(projection.push_result.ok)
        self.assertTrue(projection.push_result.partial_progress)
        self.assertEqual(projection.push_result.reason, "branch_already_pushed")

    def test_project_push_report_auto_transitions_non_destructive_failure(
        self,
    ) -> None:
        projection = project_push_report(
            action_id="vcs.push",
            report={
                "reason": "validation_failed",
                "errors": ["Configured push preflight failed."],
                "push_stages": {
                    "validation_ready": False,
                    "published_remote": False,
                    "post_push_green": False,
                },
            },
            pipeline_artifact_relpath="dev/reports/commit_pipeline.json",
            pipeline_state="push_pending",
            local_commit_landed=True,
        )

        self.assertEqual(
            projection.next_state,
            STATE_DELIVERED_LOCALLY_PENDING_PUBLISH,
        )
        self.assertEqual(projection.blocked_reason, "")
        self.assertEqual(
            projection.push_failure_transition["classification"],
            PUSH_FAILURE_CLASSIFICATION_NON_DESTRUCTIVE,
        )
        self.assertTrue(projection.push_failure_transition["auto_transitioned"])

    def test_project_push_report_keeps_destructive_failure_blocked(self) -> None:
        projection = project_push_report(
            action_id="vcs.push",
            report={
                "reason": "git_push_failed",
                "push_step": {"stderr": "remote rejected non-fast-forward"},
                "push_stages": {
                    "validation_ready": True,
                    "published_remote": False,
                    "post_push_green": False,
                },
            },
            pipeline_artifact_relpath="dev/reports/commit_pipeline.json",
            pipeline_state="push_pending",
            local_commit_landed=True,
        )

        self.assertEqual(projection.next_state, "push_blocked")
        self.assertEqual(projection.blocked_reason, "git_push_failed")
        self.assertEqual(
            projection.push_failure_transition["classification"],
            PUSH_FAILURE_CLASSIFICATION_DESTRUCTIVE,
        )
        self.assertFalse(projection.push_failure_transition["auto_transitioned"])

    def test_sync_commit_pipeline_with_push_report_updates_both_pipeline_artifacts(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            artifact_paths = resolve_artifact_paths(repo_root=repo_root)
            projections_root = Path(artifact_paths.projections_root)
            projections_root.mkdir(parents=True, exist_ok=True)

            pipeline = RemoteCommitPipelineContract(
                pipeline_id="pipeline-123",
                state="push_pending",
                branch="feature/demo",
                remote="origin",
                commit_sha="abc123",
                approved_target_identity="tree-receipt-1",
                snapshot_id="snap-stale",
                zref="zref_stale_abc123",
            )
            persist_remote_commit_pipeline_contract(
                pipeline,
                output_root=projections_root,
            )
            (projections_root / "review_state.json").write_text(
                json.dumps(
                    {
                        "reviewer_runtime": {
                            "reviewer_mode": "active_dual_agent",
                            "effective_reviewer_mode": "active_dual_agent",
                        },
                        "_compat": {
                            "push_decision": {
                                "action": "run_devctl_push",
                                "reason": "push_ready",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            synced = sync_commit_pipeline_with_push_report(
                repo_root=repo_root,
                current_branch="feature/demo",
                current_remote="origin",
                current_head_commit="abc123",
                approved_target_identity="tree-receipt-1",
                report={
                    "reason": "push_completed",
                    "artifacts": {"latest_json": "dev/reports/push/latest.json"},
                    "push_stages": {
                        "validation_ready": True,
                        "published_remote": True,
                        "post_push_green": True,
                    },
                    "push_pipeline_phases": {
                        "pre_validation_managed_projection_sync": {
                            "status": "completed",
                            "receipt_committed": True,
                        },
                        "post_validation_auto_commit_repair": {
                            "status": "completed",
                            "head_moved": False,
                        },
                    },
                },
            )

            self.assertTrue(synced)
            persisted = load_remote_commit_pipeline_contract(
                output_root=projections_root
            )
            legacy = load_remote_commit_pipeline_contract(
                output_root=repo_root / "dev/reports/review_channel/latest"
            )
            self.assertEqual(persisted.state, "push_completed")
            self.assertEqual(legacy.state, "push_completed")
            self.assertEqual(persisted.push_report_path, "dev/reports/push/latest.json")
            self.assertEqual(legacy.push_report_path, "dev/reports/push/latest.json")
            self.assertIsNotNone(persisted.push_result)
            self.assertIsNotNone(legacy.push_result)
            self.assertEqual(persisted.push_result.reason, "push_completed")
            self.assertEqual(legacy.push_result.reason, "push_completed")
            self.assertEqual(
                persisted.push_pipeline_phases[
                    "pre_validation_managed_projection_sync"
                ]["status"],
                "completed",
            )
            self.assertEqual(
                legacy.push_pipeline_phases["post_validation_auto_commit_repair"][
                    "status"
                ],
                "completed",
            )
            self.assertTrue(persisted.snapshot_id.startswith("snap-"))
            self.assertNotEqual(persisted.snapshot_id, "snap-stale")
            self.assertEqual(legacy.snapshot_id, persisted.snapshot_id)
            self.assertTrue(persisted.zref.endswith("_abc123"))
            self.assertEqual(legacy.zref, persisted.zref)

    def test_sync_commit_pipeline_auto_transitions_non_destructive_push_failure(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            artifact_paths = resolve_artifact_paths(repo_root=repo_root)
            projections_root = Path(artifact_paths.projections_root)
            projections_root.mkdir(parents=True, exist_ok=True)

            pipeline = RemoteCommitPipelineContract(
                pipeline_id="pipeline-123",
                state="push_pending",
                branch="feature/demo",
                remote="origin",
                commit_sha="abc123",
                approved_target_identity="tree-receipt-1",
            )
            persist_remote_commit_pipeline_contract(
                pipeline,
                output_root=projections_root,
            )

            synced = sync_commit_pipeline_with_push_report(
                repo_root=repo_root,
                current_branch="feature/demo",
                current_remote="origin",
                current_head_commit="abc123",
                approved_target_identity="tree-receipt-1",
                report={
                    "reason": "validation_failed",
                    "errors": ["Configured push preflight failed."],
                    "artifacts": {"latest_json": "dev/reports/push/latest.json"},
                    "push_stages": {
                        "validation_ready": False,
                        "published_remote": False,
                        "post_push_green": False,
                    },
                },
            )

            self.assertTrue(synced)
            persisted = load_remote_commit_pipeline_contract(
                output_root=projections_root
            )
            legacy = load_remote_commit_pipeline_contract(
                output_root=repo_root / "dev/reports/review_channel/latest"
            )
            self.assertEqual(
                persisted.state,
                STATE_DELIVERED_LOCALLY_PENDING_PUBLISH,
            )
            self.assertEqual(
                legacy.state,
                STATE_DELIVERED_LOCALLY_PENDING_PUBLISH,
            )
            self.assertEqual(persisted.blocked_reason, "")
            self.assertEqual(persisted.delivered_by, "devctl.push")
            self.assertTrue(persisted.delivered_at_utc)
            self.assertEqual(
                persisted.local_delivery_reason,
                "non_destructive_push_failure_local_commit_delivered",
            )
            self.assertEqual(
                persisted.push_failure_transition["classification"],
                PUSH_FAILURE_CLASSIFICATION_NON_DESTRUCTIVE,
            )

    def test_sync_commit_pipeline_keeps_destructive_push_failure_blocked(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            artifact_paths = resolve_artifact_paths(repo_root=repo_root)
            projections_root = Path(artifact_paths.projections_root)
            projections_root.mkdir(parents=True, exist_ok=True)

            pipeline = RemoteCommitPipelineContract(
                pipeline_id="pipeline-123",
                state="push_pending",
                branch="feature/demo",
                remote="origin",
                commit_sha="abc123",
                approved_target_identity="tree-receipt-1",
            )
            persist_remote_commit_pipeline_contract(
                pipeline,
                output_root=projections_root,
            )

            synced = sync_commit_pipeline_with_push_report(
                repo_root=repo_root,
                current_branch="feature/demo",
                current_remote="origin",
                current_head_commit="abc123",
                approved_target_identity="tree-receipt-1",
                report={
                    "reason": "git_push_failed",
                    "push_step": {"stderr": "remote rejected non-fast-forward"},
                    "artifacts": {"latest_json": "dev/reports/push/latest.json"},
                    "push_stages": {
                        "validation_ready": True,
                        "published_remote": False,
                        "post_push_green": False,
                    },
                },
            )

            self.assertTrue(synced)
            persisted = load_remote_commit_pipeline_contract(
                output_root=projections_root
            )
            self.assertEqual(persisted.state, "push_blocked")
            self.assertEqual(persisted.blocked_reason, "git_push_failed")
            self.assertEqual(
                persisted.push_failure_transition["classification"],
                PUSH_FAILURE_CLASSIFICATION_DESTRUCTIVE,
            )
            self.assertFalse(persisted.push_failure_transition["auto_transitioned"])

    def test_sync_commit_pipeline_accepts_managed_projection_receipt_head(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            artifact_paths = resolve_artifact_paths(repo_root=repo_root)
            projections_root = Path(artifact_paths.projections_root)
            projections_root.mkdir(parents=True, exist_ok=True)

            pipeline = RemoteCommitPipelineContract(
                pipeline_id="pipeline-123",
                state="push_pending",
                branch="feature/demo",
                remote="origin",
                commit_sha="content-head",
                approved_target_identity="tree-receipt-1",
            )
            persist_remote_commit_pipeline_contract(
                pipeline,
                output_root=projections_root,
            )

            with patch(
                "dev.scripts.devctl.commands.vcs.push_pipeline_state_sync."
                "receipt_commit_parent_sha",
                return_value="content-head",
            ) as receipt_parent_mock:
                synced = sync_commit_pipeline_with_push_report(
                    repo_root=repo_root,
                    current_branch="feature/demo",
                    current_remote="origin",
                    current_head_commit="receipt-head",
                    approved_target_identity="tree-receipt-1",
                    report={
                        "reason": "push_completed",
                        "artifacts": {"latest_json": "dev/reports/push/latest.json"},
                        "push_stages": {
                            "validation_ready": True,
                            "published_remote": True,
                            "post_push_green": True,
                        },
                    },
                )

            self.assertTrue(synced)
            receipt_parent_mock.assert_called_once()
            persisted = load_remote_commit_pipeline_contract(
                output_root=projections_root
            )
            self.assertEqual(persisted.state, "push_completed")
            self.assertIsNotNone(persisted.push_result)
            self.assertEqual(persisted.push_result.reason, "push_completed")

    def test_sync_commit_pipeline_with_push_report_skips_mismatched_head(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            artifact_paths = resolve_artifact_paths(repo_root=repo_root)
            projections_root = Path(artifact_paths.projections_root)
            projections_root.mkdir(parents=True, exist_ok=True)

            persist_remote_commit_pipeline_contract(
                RemoteCommitPipelineContract(
                    pipeline_id="pipeline-123",
                    state="push_pending",
                    branch="feature/demo",
                    remote="origin",
                    commit_sha="abc123",
                    approved_target_identity="tree-receipt-1",
                ),
                output_root=projections_root,
            )

            synced = sync_commit_pipeline_with_push_report(
                repo_root=repo_root,
                current_branch="feature/demo",
                current_remote="origin",
                current_head_commit="different-head",
                approved_target_identity="tree-receipt-1",
                report={
                    "reason": "push_completed",
                    "artifacts": {"latest_json": "dev/reports/push/latest.json"},
                    "push_stages": {
                        "validation_ready": True,
                        "published_remote": True,
                        "post_push_green": True,
                    },
                },
            )

            self.assertFalse(synced)
            persisted = load_remote_commit_pipeline_contract(
                output_root=projections_root
            )
            self.assertEqual(persisted.state, "push_pending")
            self.assertIsNone(persisted.push_result)
            self.assertEqual(persisted.push_report_path, "")

    def test_sync_commit_pipeline_with_push_report_preserves_push_completed_on_branch_already_pushed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            artifact_paths = resolve_artifact_paths(repo_root=repo_root)
            projections_root = Path(artifact_paths.projections_root)
            projections_root.mkdir(parents=True, exist_ok=True)

            completed_pipeline = RemoteCommitPipelineContract(
                pipeline_id="pipeline-123",
                state="push_completed",
                branch="feature/demo",
                remote="origin",
                commit_sha="abc123",
                approved_target_identity="tree-receipt-1",
            )
            persist_remote_commit_pipeline_contract(
                completed_pipeline,
                output_root=projections_root,
            )

            synced = sync_commit_pipeline_with_push_report(
                repo_root=repo_root,
                current_branch="feature/demo",
                current_remote="origin",
                current_head_commit="abc123",
                approved_target_identity="tree-receipt-1",
                report={
                    "reason": "branch_already_pushed",
                    "artifacts": {"latest_json": "dev/reports/push/latest.json"},
                    "push_stages": {
                        "validation_ready": True,
                        "published_remote": True,
                        "post_push_green": False,
                    },
                },
            )

            self.assertFalse(synced)
            persisted = load_remote_commit_pipeline_contract(
                output_root=projections_root
            )
            self.assertEqual(persisted.state, "push_completed")
            self.assertIsNone(persisted.push_result)
            self.assertEqual(persisted.push_report_path, "")

    def test_sync_commit_pipeline_auto_transitions_regressed_push_blocked_on_branch_already_pushed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            artifact_paths = resolve_artifact_paths(repo_root=repo_root)
            projections_root = Path(artifact_paths.projections_root)
            projections_root.mkdir(parents=True, exist_ok=True)

            persist_remote_commit_pipeline_contract(
                RemoteCommitPipelineContract(
                    pipeline_id="pipeline-123",
                    state="push_blocked",
                    branch="feature/demo",
                    remote="origin",
                    commit_sha="abc123",
                    approved_target_identity="tree-receipt-1",
                    blocked_reason="branch_already_pushed",
                ),
                output_root=projections_root,
            )

            synced = sync_commit_pipeline_with_push_report(
                repo_root=repo_root,
                current_branch="feature/demo",
                current_remote="origin",
                current_head_commit="abc123",
                approved_target_identity="tree-receipt-1",
                report={
                    "reason": "branch_already_pushed",
                    "artifacts": {"latest_json": "dev/reports/push/latest.json"},
                    "push_stages": {
                        "validation_ready": True,
                        "published_remote": True,
                        "post_push_green": False,
                    },
                },
            )

            self.assertTrue(synced)
            persisted = load_remote_commit_pipeline_contract(
                output_root=projections_root
            )
            legacy = load_remote_commit_pipeline_contract(
                output_root=repo_root / "dev/reports/review_channel/latest"
            )
            self.assertEqual(
                persisted.state,
                STATE_DELIVERED_LOCALLY_PENDING_PUBLISH,
            )
            self.assertEqual(
                legacy.state,
                STATE_DELIVERED_LOCALLY_PENDING_PUBLISH,
            )
            self.assertIsNotNone(persisted.push_result)
            self.assertIsNotNone(legacy.push_result)
            self.assertEqual(persisted.push_result.reason, "branch_already_pushed")
            self.assertEqual(legacy.push_result.reason, "branch_already_pushed")
            self.assertTrue(persisted.push_result.partial_progress)
            self.assertTrue(legacy.push_result.partial_progress)
            self.assertEqual(
                persisted.push_failure_transition["classification"],
                PUSH_FAILURE_CLASSIFICATION_NON_DESTRUCTIVE,
            )
            self.assertTrue(persisted.push_failure_transition["auto_transitioned"])


if __name__ == "__main__":
    unittest.main()
