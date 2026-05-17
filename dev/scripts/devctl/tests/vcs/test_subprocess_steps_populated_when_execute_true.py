"""Regression coverage for execute=True push subprocess evidence."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.commands.vcs import push
from dev.scripts.devctl.governance.push_policy import PushBypassPolicy
from dev.scripts.devctl.tests.vcs.push_regression_helpers import (
    authorization_for_current_repo,
    create_repo_with_ahead_commit,
    make_args,
    make_policy,
)


class PushExecuteStepEvidenceTests(unittest.TestCase):
    def test_execute_true_populates_fetch_preflight_push_and_post_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root, _remote_root = create_repo_with_ahead_commit(
                Path(tmp_dir),
                "feature/subprocess-steps",
            )
            policy = make_policy(
                bypass=PushBypassPolicy(allow_skip_post_push=True),
            )
            with (
                patch(
                    "dev.scripts.devctl.commands.vcs.push.build_preflight_shell_command",
                    return_value="git status --short",
                ),
                patch(
                    "dev.scripts.devctl.commands.vcs.push.refresh_managed_projections_before_preflight",
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

            self.assertEqual(rc, 0)
            self.assertEqual(report["status"], "published_remote")
            for field_name in ("fetch_step", "preflight_step", "push_step"):
                self.assertIsNotNone(report[field_name], field_name)
                self.assertEqual(report[field_name]["returncode"], 0)
            self.assertTrue(report["post_push_steps"])
            self.assertEqual(report["post_push_steps"][0]["name"], "push-post-skipped")


if __name__ == "__main__":
    unittest.main()
