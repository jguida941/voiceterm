"""Tests for the policy-driven devctl push command."""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands.vcs import push
from dev.scripts.devctl.governance.push_policy import (
    PushCheckpointPolicy,
    PushPolicy,
    PushPostPushPolicy,
    PushPreflightPolicy,
    detect_push_enforcement_state,
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
        "checkpoint": PushCheckpointPolicy(),
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
        checkpoint=values["checkpoint"],
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


class PushCommandTests(unittest.TestCase):
    @patch(
        "dev.scripts.devctl.governance.push_state._git_stdout",
        side_effect=[
            "",
            "origin/feature/demo",
            "0",
            " M alpha.py\n M beta.py\n M gamma.py\n?? delta.py\n",
        ],
    )
    def test_detect_push_enforcement_requires_checkpoint_when_budget_exceeded(
        self,
        _git_stdout_mock,
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

    @patch(
        "dev.scripts.devctl.governance.push_state._git_stdout",
        side_effect=[
            "",
            "origin/feature/demo",
            "0",
            " M alpha.py\n?? delta.py\n",
        ],
    )
    def test_detect_push_enforcement_allows_editing_within_budget(
        self,
        _git_stdout_mock,
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
        "dev.scripts.devctl.commands.vcs.push.build_preflight_shell_command",
        return_value="python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute",
    )
    @patch(
        "dev.scripts.devctl.commands.vcs.push.branch_divergence",
        return_value={"behind": 0, "ahead": 2, "error": None},
    )
    @patch("dev.scripts.devctl.commands.vcs.push.remote_branch_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.remote_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.vcs.push.load_push_policy")
    @patch("dev.scripts.devctl.commands.vcs.push.collect_git_status")
    def test_push_default_run_validates_and_stops_before_git_push(
        self,
        collect_git_status_mock,
        load_policy_mock,
        _remote_exists_mock,
        _remote_branch_exists_mock,
        _branch_divergence_mock,
        _preflight_command_mock,
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
                    "python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute",
                ],
                "cwd": ".",
                "returncode": 0,
                "duration_s": 0.1,
                "skipped": False,
            },
        ]

        rc = push.run(make_args())

        self.assertEqual(rc, 0)
        executed = [call.args[1] for call in run_cmd_mock.call_args_list]
        self.assertEqual(
            executed,
            [
                ["git", "fetch", "origin"],
                [
                    "bash",
                    "-lc",
                    "python3 dev/scripts/devctl.py check-router --since-ref origin/develop --execute",
                ],
            ],
        )
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["typed_action"]["action_id"], "vcs.push")

    @patch("dev.scripts.devctl.commands.vcs.push.write_output")
    @patch(
        "dev.scripts.devctl.commands.vcs.push.build_post_push_commands",
        return_value=["git status", "git log --oneline --decorate -n 10"],
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
    def test_push_execute_sets_upstream_and_runs_post_push_bundle(
        self,
        run_cmd_mock,
        collect_git_status_mock,
        load_policy_mock,
        _remote_exists_mock,
        _remote_branch_exists_mock,
        _preflight_command_mock,
        _post_push_commands_mock,
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
        self.assertIn(["git", "push", "--set-upstream", "origin", "feature/demo"], executed)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertEqual(payload["status"], "pushed")


if __name__ == "__main__":
    unittest.main()
