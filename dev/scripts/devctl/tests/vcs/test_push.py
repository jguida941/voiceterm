"""Tests for the policy-driven devctl push command."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands.vcs import push
from dev.scripts.devctl.commands.vcs import push_preflight_commit
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
from dev.scripts.devctl.review_channel.event_store import resolve_artifact_paths
from dev.scripts.devctl.review_channel.remote_commit_pipeline_artifact import (
    load_remote_commit_pipeline_contract,
    persist_remote_commit_pipeline_contract,
)
from dev.scripts.devctl.runtime.remote_commit_pipeline_models import (
    RemoteCommitPipelineContract,
)


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


def _publication_authorization(
    *,
    authorized: bool = True,
    reason: str = "push_authorization_current",
    summary: str = "Publication is authorized for the current HEAD.",
    approved_target_identity: str = "tree-receipt-20260403T010000Z:tree-123",
    authorization_id: str = "push-auth-20260403T010000Z",
    approval_mode: str = "commit_pipeline_approval",
) -> SimpleNamespace:
    return SimpleNamespace(
        authorized=authorized,
        reason=reason,
        summary=summary,
        push_authorization=(
            SimpleNamespace(
                approved_target_identity=approved_target_identity,
                authorization_id=authorization_id,
                approval_mode=approval_mode,
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

    @patch("dev.scripts.devctl.commands.vcs.push_executor_routing.emit_output")
    @patch("dev.scripts.devctl.commands.vcs.push_executor_routing.load_latest_push_report")
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
        load_latest_report_mock.return_value = {
            "ok": True,
            "branch": "feature/demo",
            "head_commit": "abc123",
            "push_stages": {
                "published_remote": True,
                "post_push_green": True,
                "validation_ready": True,
            },
        }
        emit_output_mock.return_value = 0

        rc = push.run(make_args(execute=True, format="json"))

        self.assertEqual(rc, 0)
        fake_executor.execute.assert_called_once()
        emit_output_mock.assert_called_once()

    @patch("dev.scripts.devctl.commands.vcs.push_pipeline_recovery.apply_refresh_authorization")
    @patch(
        "dev.scripts.devctl.commands.vcs.push_pipeline_recovery.current_head_commit_sha",
        return_value="abc123",
    )
    @patch("dev.scripts.devctl.commands.vcs.push_executor_routing.emit_output")
    @patch("dev.scripts.devctl.commands.vcs.push_executor_routing.load_latest_push_report")
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
        load_latest_report_mock.return_value = {
            "ok": True,
            "branch": "feature/demo",
            "head_commit": "abc123",
            "push_stages": {
                "published_remote": True,
                "post_push_green": True,
                "validation_ready": True,
            },
        }
        emit_output_mock.return_value = 0
        apply_refresh_authorization_mock.return_value = {"ok": True}

        rc = push.run(make_args(execute=True, format="json"))

        self.assertEqual(rc, 0)
        apply_refresh_authorization_mock.assert_called_once()
        fake_executor.execute.assert_called_once()

    @patch("dev.scripts.devctl.commands.vcs.push_executor_routing.emit_output", return_value=7)
    @patch("dev.scripts.devctl.commands.vcs.push_executor_routing.load_latest_push_report")
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
        load_latest_report_mock.return_value = {
            "ok": True,
            "branch": "feature/demo",
            "head_commit": "abc123",
            "push_stages": {
                "published_remote": True,
                "post_push_green": True,
                "validation_ready": True,
            },
        }

        rc = push.run(make_args(execute=True, format="json"))

        self.assertEqual(rc, 7)

    @patch("dev.scripts.devctl.commands.vcs.push_executor_routing.emit_output")
    @patch("dev.scripts.devctl.commands.vcs.push_executor_routing.load_latest_push_report")
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
        load_latest_report_mock.return_value = {
            "ok": True,
            "branch": "feature/demo",
            "head_commit": "abc123",
            "push_stages": {
                "published_remote": True,
                "post_push_green": True,
                "validation_ready": True,
            },
        }
        _emit_output_mock.return_value = 0

        rc = push.run(make_args(execute=True, format="json"))

        self.assertEqual(rc, 0)
        action = fake_executor.execute.call_args.args[0]
        self.assertEqual(action.parameters["remote"], "upstream")
        self.assertEqual(
            action.parameters["approved_target_identity"],
            "tree-receipt-20260403T010000Z:tree-123",
        )

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
        return_value=SimpleNamespace(
            approved_target_identity=""
        ),
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
    @patch("dev.scripts.devctl.commands.vcs.push.remote_branch_exists", return_value=True)
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
        self.assertEqual(payload["artifacts"]["latest_json"], "dev/reports/push/latest.json")
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
    @patch("dev.scripts.devctl.commands.vcs.push.remote_branch_exists", return_value=True)
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
        self.assertEqual(payload["status"], "published_remote")
        self.assertEqual(payload["reason"], "branch_already_pushed")
        self.assertIsNone(payload["preflight_step"])
        self.assertIsNone(payload["push_step"])
        self.assertEqual(
            payload["push_stages"],
            {
                "validation_ready": True,
                "published_remote": True,
                "post_push_green": False,
            },
        )

    @patch("dev.scripts.devctl.commands.vcs.push.write_output")
    @patch("dev.scripts.devctl.commands.vcs.push.run_cmd")
    @patch(
        "dev.scripts.devctl.commands.vcs.push.branch_divergence",
        return_value={"behind": 0, "ahead": 0, "error": None},
    )
    @patch("dev.scripts.devctl.commands.vcs.push.remote_branch_exists", return_value=True)
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

        rc = push.run(make_args(execute=True))

        self.assertEqual(rc, 0)
        self.assertEqual(
            [call.args[1] for call in run_cmd_mock.call_args_list],
            [["git", "fetch", "origin"]],
        )
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["status"], "published_remote")
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
    @patch("dev.scripts.devctl.commands.vcs.push.remote_branch_exists", return_value=False)
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
            ["git", "-c", "devctl.governed-push=true", "push", "--set-upstream", "origin", "feature/demo"],
            executed,
        )
        _post_push_commands_mock.assert_called_once_with(
            load_policy_mock.return_value,
            quality_policy_path=None,
            since_ref="origin/develop",
        )
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["status"], "post_push_green")
        self.assertEqual(payload["artifacts"]["latest_json"], "dev/reports/push/latest.json")
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
    @patch("dev.scripts.devctl.commands.vcs.push.remote_branch_exists", return_value=True)
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

    def test_sync_bridge_projection_before_preflight_reprojects_active_bridge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            bridge_path = repo_root / "bridge.md"
            review_channel_path = repo_root / "dev" / "active" / "review_channel.md"
            review_state_path = (
                repo_root / "dev" / "reports" / "review_channel" / "latest" / "review_state.json"
            )
            bridge_path.write_text("# Review Bridge\n", encoding="utf-8")
            review_channel_path.parent.mkdir(parents=True, exist_ok=True)
            review_channel_path.write_text("# active review channel\n", encoding="utf-8")
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
            ["commit", "-m", "chore(push): auto-commit preflight-generated changes"],
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

    @patch("dev.scripts.devctl.commands.vcs.push.write_output")
    @patch(
        "dev.scripts.devctl.commands.vcs.push.current_upstream_ref",
        return_value="",
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.build_preflight_shell_command",
        return_value="python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute",
    )
    @patch("dev.scripts.devctl.commands.vcs.push.remote_branch_exists", return_value=False)
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
        ]

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
    @patch("dev.scripts.devctl.commands.vcs.push.remote_branch_exists", return_value=False)
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
                "returncode": 1,
                "duration_s": 0.1,
                "skipped": False,
            },
        ]

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
    @patch("dev.scripts.devctl.commands.vcs.push.current_head_commit_sha", return_value="abc123")
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
    @patch("dev.scripts.devctl.commands.vcs.push.remote_branch_exists", return_value=False)
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
                "returncode": 1,
                "duration_s": 0.1,
                "skipped": False,
            },
        ]

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
    @patch("dev.scripts.devctl.commands.vcs.push.remote_branch_exists", return_value=True)
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

        rc = push.run(make_args(execute=True))

        self.assertEqual(rc, 0)
        _post_push_commands_mock.assert_called_once_with(
            load_policy_mock.return_value,
            quality_policy_path=None,
            since_ref="origin/feature/demo",
        )
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["status"], "post_push_green")

    def test_execute_push_flow_emits_publication_and_post_push_progress_notices(self) -> None:
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

    def test_build_preflight_shell_command_prefers_remote_branch_when_it_exists(self) -> None:
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

    def test_build_post_push_commands_rewrites_since_ref_for_runtime_scope(self) -> None:
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
    def test_append_push_receipt_appends_multiple_entries(self, path_config_mock) -> None:
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
    def test_lookup_push_receipt_returns_none_for_nonmatching(self, path_config_mock) -> None:
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
            persisted = load_remote_commit_pipeline_contract(output_root=projections_root)
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
            persisted = load_remote_commit_pipeline_contract(output_root=projections_root)
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


if __name__ == "__main__":
    unittest.main()
