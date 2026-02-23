"""Tests for devctl path-rewrite command."""

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import path_rewrite


class PathRewriteCommandTests(TestCase):
    def test_cli_accepts_path_rewrite_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["path-rewrite", "--dry-run", "--format", "json"])
        self.assertEqual(args.command, "path-rewrite")
        self.assertTrue(args.dry_run)
        self.assertEqual(args.format, "json")

    @patch("dev.scripts.devctl.commands.path_rewrite.write_output")
    @patch("dev.scripts.devctl.commands.path_rewrite.rewrite_legacy_path_references")
    def test_path_rewrite_passes_when_rewrite_is_clean(
        self,
        rewrite_mock,
        _write_output_mock,
    ) -> None:
        rewrite_mock.return_value = {
            "ok": True,
            "dry_run": True,
            "checked_file_count": 42,
            "changed_file_count": 2,
            "replacement_count": 4,
            "changes": [
                {"file": "AGENTS.md", "replacements": 2},
                {"file": "dev/DEVELOPMENT.md", "replacements": 2},
            ],
            "post_scan": {"ok": True, "violations": []},
        }
        args = SimpleNamespace(
            dry_run=True,
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
        )

        code = path_rewrite.run(args)

        self.assertEqual(code, 0)
        rewrite_mock.assert_called_once_with(dry_run=True)

    @patch("dev.scripts.devctl.commands.path_rewrite.write_output")
    @patch("dev.scripts.devctl.commands.path_rewrite.rewrite_legacy_path_references")
    def test_path_rewrite_fails_when_post_scan_still_has_violations(
        self,
        rewrite_mock,
        _write_output_mock,
    ) -> None:
        rewrite_mock.return_value = {
            "ok": False,
            "dry_run": False,
            "checked_file_count": 42,
            "changed_file_count": 1,
            "replacement_count": 1,
            "changes": [{"file": "AGENTS.md", "replacements": 1}],
            "post_scan": {"ok": False, "violations": [{}]},
        }
        args = SimpleNamespace(
            dry_run=False,
            format="json",
            output=None,
            pipe_command=None,
            pipe_args=None,
        )

        code = path_rewrite.run(args)

        self.assertEqual(code, 1)
        rewrite_mock.assert_called_once_with(dry_run=False)
