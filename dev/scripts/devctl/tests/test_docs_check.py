"""Tests for docs-check and git status collection behavior."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl import collect
from dev.scripts.devctl.commands import docs_check


class CollectGitStatusTests(unittest.TestCase):
    """Validate git collection for worktree and commit-range modes."""

    @patch("dev.scripts.devctl.collect.shutil.which", return_value="/usr/bin/git")
    @patch("dev.scripts.devctl.collect.subprocess.check_output")
    def test_collect_git_status_uses_worktree_porcelain(self, mock_check_output, _mock_git) -> None:
        mock_check_output.side_effect = [
            "feature/test\n",
            " M guides/USAGE.md\nA  dev/CHANGELOG.md\n",
        ]

        report = collect.collect_git_status()

        self.assertEqual(report["branch"], "feature/test")
        self.assertIsNone(report["since_ref"])
        self.assertEqual(report["head_ref"], "HEAD")
        self.assertTrue(report["changelog_updated"])
        self.assertEqual(
            report["changes"],
            [
                {"status": "M", "path": "guides/USAGE.md"},
                {"status": "A", "path": "dev/CHANGELOG.md"},
            ],
        )
        self.assertEqual(
            mock_check_output.call_args_list[1].args[0],
            ["git", "status", "--porcelain"],
        )

    @patch("dev.scripts.devctl.collect.shutil.which", return_value="/usr/bin/git")
    @patch("dev.scripts.devctl.collect.subprocess.check_output")
    def test_collect_git_status_uses_commit_range_diff(self, mock_check_output, _mock_git) -> None:
        mock_check_output.side_effect = [
            "feature/test\n",
            "M\tguides/USAGE.md\nR100\told.md\tdev/CHANGELOG.md\n",
        ]

        report = collect.collect_git_status("HEAD~1", "HEAD")

        self.assertEqual(report["since_ref"], "HEAD~1")
        self.assertEqual(report["head_ref"], "HEAD")
        self.assertTrue(report["changelog_updated"])
        self.assertEqual(
            report["changes"],
            [
                {"status": "M", "path": "guides/USAGE.md"},
                {"status": "R100", "path": "dev/CHANGELOG.md"},
            ],
        )
        self.assertEqual(
            mock_check_output.call_args_list[1].args[0],
            ["git", "diff", "--name-status", "HEAD~1...HEAD"],
        )


class DocsCheckCommandTests(unittest.TestCase):
    """Validate docs-check command wiring for commit-range mode."""

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch("dev.scripts.devctl.commands.docs_check._scan_deprecated_references", return_value=[])
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_forwards_commit_range(
        self,
        mock_collect_git_status,
        _mock_scan_deprecated,
        _mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {
            "changes": [
                {"status": "M", "path": "dev/CHANGELOG.md"},
                {"status": "M", "path": "guides/USAGE.md"},
            ]
        }
        args = SimpleNamespace(
            user_facing=True,
            strict=False,
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
            since_ref="origin/develop",
            head_ref="HEAD",
            strict_tooling=False,
        )

        code = docs_check.run(args)

        self.assertEqual(code, 0)
        mock_collect_git_status.assert_called_once_with("origin/develop", "HEAD")

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch("dev.scripts.devctl.commands.docs_check._scan_deprecated_references", return_value=[])
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_fails_when_tooling_changes_without_tooling_docs(
        self,
        mock_collect_git_status,
        _mock_scan_deprecated,
        _mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {
            "changes": [
                {"status": "M", "path": "Makefile"},
            ]
        }
        args = SimpleNamespace(
            user_facing=False,
            strict=False,
            strict_tooling=False,
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
            since_ref="HEAD~1",
            head_ref="HEAD",
        )

        code = docs_check.run(args)

        self.assertEqual(code, 1)

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch("dev.scripts.devctl.commands.docs_check._scan_deprecated_references")
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_fails_on_deprecated_reference_violations(
        self,
        mock_collect_git_status,
        mock_scan_deprecated,
        _mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {"changes": []}
        mock_scan_deprecated.return_value = [
            {
                "file": "AGENTS.md",
                "line": 1,
                "pattern": "release-script",
                "replacement": "python3 dev/scripts/devctl.py release --version <version>",
                "line_text": "./dev/scripts/release.sh 1.2.3",
            }
        ]
        args = SimpleNamespace(
            user_facing=False,
            strict=False,
            strict_tooling=False,
            format="json",
            output=None,
            pipe_command=None,
            pipe_args=None,
            since_ref=None,
            head_ref="HEAD",
        )

        code = docs_check.run(args)

        self.assertEqual(code, 1)

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch("dev.scripts.devctl.commands.docs_check._scan_deprecated_references", return_value=[])
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_strict_tooling_requires_engineering_evolution_update(
        self,
        mock_collect_git_status,
        _mock_scan_deprecated,
        _mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {
            "changes": [
                {"status": "M", "path": ".github/workflows/tooling_control_plane.yml"},
                {"status": "M", "path": "AGENTS.md"},
                {"status": "M", "path": "dev/DEVELOPMENT.md"},
                {"status": "M", "path": "dev/scripts/README.md"},
                {"status": "M", "path": "dev/active/MASTER_PLAN.md"},
            ]
        }
        args = SimpleNamespace(
            user_facing=False,
            strict=False,
            strict_tooling=True,
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
            since_ref="HEAD~1",
            head_ref="HEAD",
        )

        code = docs_check.run(args)

        self.assertEqual(code, 1)

    @patch("dev.scripts.devctl.commands.docs_check.write_output")
    @patch("dev.scripts.devctl.commands.docs_check._scan_deprecated_references", return_value=[])
    @patch("dev.scripts.devctl.commands.docs_check.collect_git_status")
    def test_docs_check_strict_tooling_passes_with_engineering_evolution_update(
        self,
        mock_collect_git_status,
        _mock_scan_deprecated,
        _mock_write_output,
    ) -> None:
        mock_collect_git_status.return_value = {
            "changes": [
                {"status": "M", "path": ".github/workflows/tooling_control_plane.yml"},
                {"status": "M", "path": "AGENTS.md"},
                {"status": "M", "path": "dev/DEVELOPMENT.md"},
                {"status": "M", "path": "dev/scripts/README.md"},
                {"status": "M", "path": "dev/active/MASTER_PLAN.md"},
                {"status": "M", "path": "dev/history/ENGINEERING_EVOLUTION.md"},
            ]
        }
        args = SimpleNamespace(
            user_facing=False,
            strict=False,
            strict_tooling=True,
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
            since_ref="HEAD~1",
            head_ref="HEAD",
        )

        code = docs_check.run(args)

        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
