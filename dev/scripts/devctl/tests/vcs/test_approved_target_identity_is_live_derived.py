"""Regression coverage for live-derived push approved target identity."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.commands.vcs import push
from dev.scripts.devctl.review_channel.service_identity import (
    worktree_identity_for_repo,
)
from dev.scripts.devctl.tests.vcs.push_regression_helpers import (
    authorization_for_current_repo,
    create_repo_with_ahead_commit,
    make_args,
    make_policy,
)


class PushApprovedTargetIdentityTests(unittest.TestCase):
    def test_approved_target_identity_comes_from_live_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root, _remote_root = create_repo_with_ahead_commit(
                Path(tmp_dir),
                "feature/live-identity",
            )
            live_identity = "tree-receipt-29990101T000000Z:live-tree"

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
                    make_args(
                        execute=False,
                        approved_target_identity=(
                            "tree-receipt-20260403T010000Z:tree-123"
                        ),
                    ),
                    repo_root=repo_root,
                    policy=make_policy(),
                    emit_output_report=False,
                    run_cmd_fn=push.run_cmd,
                    build_post_push_commands_fn=lambda _policy, **_kwargs: [],
                    publication_authorization_fn=lambda **_kwargs: authorization_for_current_repo(
                        repo_root,
                        identity=live_identity,
                    ),
                )

            self.assertEqual(rc, 1)
            self.assertEqual(report["approved_target_identity"], live_identity)
            self.assertEqual(
                report["typed_action"]["parameters"]["approved_target_identity"],
                live_identity,
            )
            self.assertEqual(
                report["typed_action"]["parameters"]["current_worktree_identity"],
                worktree_identity_for_repo(repo_root),
            )
            self.assertEqual(
                report["typed_action"]["parameters"]["head_commit"],
                push.current_head_commit_sha(repo_root=repo_root),
            )
            self.assertEqual(
                report["typed_action"]["parameters"]["approved_target_identity_source"],
                "live_publication_authorization",
            )
            self.assertEqual(
                report["findings"][0]["type"],
                "ApprovedTargetIdentityViolation",
            )

    def test_stale_approved_target_identity_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root, _remote_root = create_repo_with_ahead_commit(
                Path(tmp_dir),
                "feature/stale-identity",
            )
            head = push.current_head_commit_sha(repo_root=repo_root)

            def stale_authorization(**_kwargs):
                return SimpleNamespace(
                    authorized=True,
                    reason="push_authorization_current",
                    summary="Publication is authorized for the current HEAD.",
                    push_authorization=SimpleNamespace(
                        approved_target_identity=(
                            "tree-receipt-20260403T010000Z:tree-123"
                        ),
                        authorization_id="push-auth-20260403T010000Z",
                        approval_mode="commit_pipeline_approval",
                        authorized_head_sha=head,
                        approved_at_utc="2026-04-03T01:00:00Z",
                        expires_at_utc="2026-04-03T01:30:00Z",
                        worktree_identity=worktree_identity_for_repo(repo_root),
                    ),
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
                    make_args(execute=False),
                    repo_root=repo_root,
                    policy=make_policy(),
                    emit_output_report=False,
                    run_cmd_fn=push.run_cmd,
                    build_post_push_commands_fn=lambda _policy, **_kwargs: [],
                    publication_authorization_fn=stale_authorization,
                )

            self.assertEqual(rc, 1)
            self.assertEqual(report["status"], "blocked")
            self.assertEqual(
                report["findings"][0]["type"],
                "ApprovedTargetIdentityViolation",
            )
            self.assertIn("stale", report["findings"][0]["message"])


if __name__ == "__main__":
    unittest.main()
