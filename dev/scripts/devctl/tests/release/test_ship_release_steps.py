"""Tests for repo-policy-driven release tag steps."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.commands.ship_release_steps import run_tag_step
from dev.scripts.devctl.governance.push_policy import (
    PushBypassPolicy,
    PushCheckpointPolicy,
    PushPolicy,
    PushPostPushPolicy,
    PushPreflightPolicy,
    PushPublicationPolicy,
)


def make_policy(**overrides) -> PushPolicy:
    defaults = {
        "policy_path": "dev/config/devctl_repo_policy.json",
        "repo_pack_id": "voiceterm",
        "warnings": (),
        "default_remote": "upstream",
        "development_branch": "develop",
        "release_branch": "release",
        "protected_branches": ("develop", "release"),
        "allowed_branch_prefixes": ("feature/", "fix/"),
        "preflight": PushPreflightPolicy(),
        "post_push": PushPostPushPolicy(),
        "bypass": PushBypassPolicy(),
        "checkpoint": PushCheckpointPolicy(),
        "publication": PushPublicationPolicy(),
    }
    defaults.update(overrides)
    return PushPolicy(**defaults)


class ShipReleaseStepsTests(unittest.TestCase):
    @patch("dev.scripts.devctl.commands.ship_release_steps.tag_exists", return_value=True)
    @patch("dev.scripts.devctl.commands.ship_release_steps.run_cmd")
    @patch("dev.scripts.devctl.commands.ship_release_steps.load_push_policy")
    @patch("dev.scripts.devctl.commands.ship_release_steps.read_version", return_value="1.2.3")
    @patch("dev.scripts.devctl.commands.ship_release_steps.changelog_has_version", return_value=True)
    @patch("dev.scripts.devctl.commands.ship_release_steps.subprocess.run")
    @patch("dev.scripts.devctl.commands.ship_release_steps.run_checked", return_value=(0, "release"))
    def test_run_tag_step_uses_release_branch_and_remote_from_policy(
        self,
        _run_checked_mock,
        subprocess_run_mock,
        _changelog_mock,
        _read_version_mock,
        load_push_policy_mock,
        run_cmd_mock,
        _tag_exists_mock,
    ) -> None:
        subprocess_run_mock.return_value.returncode = 0
        load_push_policy_mock.return_value = make_policy()
        run_cmd_mock.return_value = {
            "name": "git-pull",
            "cmd": ["git", "pull", "--ff-only", "upstream", "release"],
            "cwd": ".",
            "returncode": 0,
            "duration_s": 0.1,
            "skipped": False,
        }

        args = SimpleNamespace(dry_run=False, yes=True)
        result = run_tag_step(args, {"version": "1.2.3", "tag": "v1.2.3"})

        self.assertTrue(result["ok"])
        run_cmd_mock.assert_called_once_with(
            "git-pull",
            ["git", "pull", "--ff-only", "upstream", "release"],
            cwd=unittest.mock.ANY,
            dry_run=False,
        )


if __name__ == "__main__":
    unittest.main()
