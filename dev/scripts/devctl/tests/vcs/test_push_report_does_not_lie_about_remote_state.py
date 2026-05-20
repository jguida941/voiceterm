"""Regression coverage for governed push remote-publication truth."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.commands.vcs import push
from dev.scripts.devctl.governance.push_policy import PushBypassPolicy
from dev.scripts.devctl.runtime.git_mutation_proof_receipt import (
    GIT_MUTATION_PROOF_RECEIPT_STORE_REL,
)
from dev.scripts.devctl.tests.vcs.push_regression_helpers import (
    authorization_for_current_repo,
    create_repo_with_ahead_commit,
    make_args,
    make_policy,
    run_git,
)


class PushRemoteTruthTests(unittest.TestCase):
    def test_published_remote_status_requires_remote_ref_advance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root, remote_root = create_repo_with_ahead_commit(
                Path(tmp_dir),
                "feature/live-remote-truth",
            )
            before = run_git(
                remote_root,
                "rev-parse",
                "refs/heads/feature/live-remote-truth",
            )
            policy = make_policy(
                bypass=PushBypassPolicy(allow_skip_post_push=True),
            )
            with (
                patch(
                    "dev.scripts.devctl.commands.vcs.push_preflight_flow.build_preflight_shell_command",
                    return_value="git status --short",
                ),
                patch(
                    "dev.scripts.devctl.commands.vcs.push_preflight_flow.refresh_managed_projections_before_preflight",
                ),
            ):
                rc, report = push.run_push_action(
                    make_args(execute=True, skip_post_push=True),
                    repo_root=repo_root,
                    policy=policy,
                    emit_output_report=False,
                    run_cmd_fn=push.run_cmd,
                    build_post_push_commands_fn=lambda _policy, **_kwargs: [],
                    publication_authorization_fn=lambda **_kwargs: authorization_for_current_repo(
                        repo_root
                    ),
                )

            after = run_git(
                remote_root,
                "rev-parse",
                "refs/heads/feature/live-remote-truth",
            )
            self.assertEqual(rc, 0)
            self.assertEqual(report["status"], "published_remote")
            self.assertTrue(report["governed_push_verified"])
            self.assertTrue(report["git_mutation_proof_verified"])
            self.assertEqual(
                report["artifacts"]["git_mutation_proof_receipts"],
                GIT_MUTATION_PROOF_RECEIPT_STORE_REL,
            )
            self.assertIn(
                GIT_MUTATION_PROOF_RECEIPT_STORE_REL,
                report["action_result"]["artifact_paths"],
            )
            self.assertNotEqual(before, after)
            self.assertEqual(after, run_git(repo_root, "rev-parse", "HEAD"))

    def test_post_push_green_does_not_inherit_pending_snapshot_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root, remote_root = create_repo_with_ahead_commit(
                Path(tmp_dir),
                "feature/post-push-green",
            )
            before = run_git(
                remote_root,
                "rev-parse",
                "refs/heads/feature/post-push-green",
            )
            with (
                patch(
                    "dev.scripts.devctl.commands.vcs.push_preflight_flow.build_preflight_shell_command",
                    return_value="git status --short",
                ),
                patch(
                    "dev.scripts.devctl.commands.vcs.push_preflight_flow.refresh_managed_projections_before_preflight",
                ),
            ):
                rc, report = push.run_push_action(
                    make_args(execute=True),
                    repo_root=repo_root,
                    policy=make_policy(),
                    emit_output_report=False,
                    run_cmd_fn=push.run_cmd,
                    build_post_push_commands_fn=lambda _policy, **_kwargs: [
                        "git status --short"
                    ],
                    publication_authorization_fn=lambda **_kwargs: authorization_for_current_repo(
                        repo_root
                    ),
                )

            after = run_git(
                remote_root,
                "rev-parse",
                "refs/heads/feature/post-push-green",
            )
            self.assertEqual(rc, 0)
            self.assertNotEqual(before, after)
            self.assertEqual(report["status"], "post_push_green")
            self.assertTrue(report["published_remote"])
            self.assertTrue(report["post_push_green"])
            self.assertTrue(report["governed_push_verified"])
            self.assertTrue(report["git_mutation_proof_verified"])
            self.assertEqual(
                report["artifacts"]["git_mutation_proof_receipts"],
                GIT_MUTATION_PROOF_RECEIPT_STORE_REL,
            )
            self.assertEqual(report["errors"], [])
            self.assertEqual(report["findings"], [])

    def test_successful_push_step_without_remote_update_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root, remote_root = create_repo_with_ahead_commit(
                Path(tmp_dir),
                "feature/remote-no-advance",
            )
            before = run_git(
                remote_root,
                "rev-parse",
                "refs/heads/feature/remote-no-advance",
            )

            def fake_run_cmd(name, cmd, cwd=None, env=None):
                del env
                return {
                    "name": name,
                    "cmd": list(cmd),
                    "cwd": str(cwd or "."),
                    "returncode": 0,
                    "duration_s": 0.0,
                    "skipped": False,
                }

            with (
                patch(
                    "dev.scripts.devctl.commands.vcs.push_preflight_flow.build_preflight_shell_command",
                    return_value="git status --short",
                ),
                patch(
                    "dev.scripts.devctl.commands.vcs.push_preflight_flow.refresh_managed_projections_before_preflight",
                ),
            ):
                rc, report = push.run_push_action(
                    make_args(execute=True),
                    repo_root=repo_root,
                    policy=make_policy(),
                    emit_output_report=False,
                    run_cmd_fn=fake_run_cmd,
                    build_post_push_commands_fn=lambda _policy, **_kwargs: [],
                    publication_authorization_fn=lambda **_kwargs: authorization_for_current_repo(
                        repo_root
                    ),
                )

            after = run_git(
                remote_root,
                "rev-parse",
                "refs/heads/feature/remote-no-advance",
            )
            self.assertEqual(before, after)
            self.assertEqual(rc, 1)
            self.assertEqual(report["status"], "blocked")
            self.assertEqual(report["reason"], "remote_ref_not_updated")
            self.assertFalse(report["governed_push_verified"])
            self.assertFalse(report["git_mutation_proof_verified"])
            self.assertEqual(
                report["artifacts"]["git_mutation_proof_receipts"],
                GIT_MUTATION_PROOF_RECEIPT_STORE_REL,
            )
            self.assertEqual(report["findings"][0]["type"], "SilentPushFailure")


if __name__ == "__main__":
    unittest.main()
