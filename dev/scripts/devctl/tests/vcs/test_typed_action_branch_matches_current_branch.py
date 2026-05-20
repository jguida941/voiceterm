"""Regression coverage for push TypedAction branch identity."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dev.scripts.devctl.commands.vcs import push
from dev.scripts.devctl.tests.vcs.push_regression_helpers import (
    authorization_for_current_repo,
    create_repo_with_ahead_commit,
    make_args,
    make_policy,
    run_git,
)


class PushTypedActionBranchTests(unittest.TestCase):
    def test_typed_action_branch_is_forced_to_live_git_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root, _remote_root = create_repo_with_ahead_commit(
                Path(tmp_dir),
                "feature/live-branch",
            )

            with (
                patch(
                    "dev.scripts.devctl.commands.vcs.push.collect_git_status_for_repo",
                    return_value={"branch": "feature/demo", "changes": []},
                ),
                patch(
                    "dev.scripts.devctl.commands.vcs.push_preflight_flow.build_preflight_shell_command",
                    return_value="git status --short",
                ),
                patch(
                    "dev.scripts.devctl.commands.vcs.push_preflight_flow.refresh_managed_projections_before_preflight",
                ),
            ):
                rc, report = push.run_push_action(
                    make_args(execute=False),
                    repo_root=repo_root,
                    policy=make_policy(),
                    emit_output_report=False,
                    run_cmd_fn=push.run_cmd,
                    build_post_push_commands_fn=lambda _policy, **_kwargs: [],
                    publication_authorization_fn=lambda **_kwargs: authorization_for_current_repo(
                        repo_root
                    ),
                )

            live_branch = run_git(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
            self.assertEqual(rc, 1)
            self.assertEqual(report["branch"], live_branch)
            self.assertEqual(
                report["typed_action"]["parameters"]["branch"],
                live_branch,
            )
            self.assertEqual(report["findings"][0]["type"], "BranchIdentityViolation")
            self.assertEqual(
                report["findings"][0]["evidence"]["configured_branch"],
                "feature/demo",
            )


if __name__ == "__main__":
    unittest.main()
