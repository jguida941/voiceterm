"""Tests for governance pilot bootstrap helpers and CLI wiring."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dev.scripts.devctl import cli, governance_bootstrap_support


class GovernanceBootstrapTests(unittest.TestCase):
    def test_bootstrap_reinitializes_broken_git_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir) / "copied-repo"
            repo_root.mkdir()
            (repo_root / ".git").write_text(
                "gitdir: ../../.git/modules/integrations/ci-cd-hub\n",
                encoding="utf-8",
            )
            (repo_root / "README.md").write_text("pilot\n", encoding="utf-8")

            result = governance_bootstrap_support.bootstrap_governance_pilot_repo(repo_root)

            self.assertEqual(result.git_state, "reinitialized")
            self.assertTrue(result.repaired_git_file)
            self.assertTrue(result.initialized_git_repo)
            self.assertTrue((repo_root / ".git").is_dir())

    def test_bootstrap_keeps_valid_git_repo_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir) / "valid-repo"
            repo_root.mkdir()
            governance_bootstrap_support._run_git(repo_root, ["git", "init"])

            result = governance_bootstrap_support.bootstrap_governance_pilot_repo(repo_root)

            self.assertEqual(result.git_state, "valid")
            self.assertFalse(result.repaired_git_file)
            self.assertFalse(result.initialized_git_repo)


class GovernanceBootstrapParserTests(unittest.TestCase):
    def test_cli_accepts_governance_bootstrap_command(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(
            [
                "governance-bootstrap",
                "--target-repo",
                "/tmp/portable-pilot",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.command, "governance-bootstrap")
        self.assertEqual(args.target_repo, "/tmp/portable-pilot")
        self.assertEqual(args.format, "json")


if __name__ == "__main__":
    unittest.main()
