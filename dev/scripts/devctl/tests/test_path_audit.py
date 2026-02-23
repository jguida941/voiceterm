"""Tests for devctl path-audit command."""

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import path_audit


class PathAuditCommandTests(TestCase):
    def test_cli_accepts_path_audit_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["path-audit", "--format", "json"])
        self.assertEqual(args.command, "path-audit")
        self.assertEqual(args.format, "json")

    @patch("dev.scripts.devctl.commands.path_audit.write_output")
    @patch("dev.scripts.devctl.commands.path_audit.scan_legacy_path_references")
    def test_path_audit_passes_when_no_violations(
        self,
        scan_mock,
        _write_output_mock,
    ) -> None:
        scan_mock.return_value = {
            "ok": True,
            "checked_file_count": 25,
            "excluded_prefixes": ["dev/archive/"],
            "rules": {},
            "violations": [],
        }
        args = SimpleNamespace(
            format="md",
            output=None,
            pipe_command=None,
            pipe_args=None,
        )

        code = path_audit.run(args)

        self.assertEqual(code, 0)

    @patch("dev.scripts.devctl.commands.path_audit.write_output")
    @patch("dev.scripts.devctl.commands.path_audit.scan_legacy_path_references")
    def test_path_audit_fails_when_violations_found(
        self,
        scan_mock,
        _write_output_mock,
    ) -> None:
        scan_mock.return_value = {
            "ok": False,
            "checked_file_count": 25,
            "excluded_prefixes": ["dev/archive/"],
            "rules": {"dev/scripts/check_active_plan_sync.py": "dev/scripts/checks/check_active_plan_sync.py"},
            "violations": [
                {
                    "file": "AGENTS.md",
                    "line": 10,
                    "legacy_path": "dev/scripts/check_active_plan_sync.py",
                    "replacement_path": "dev/scripts/checks/check_active_plan_sync.py",
                    "line_text": "python3 dev/scripts/check_active_plan_sync.py",
                }
            ],
        }
        args = SimpleNamespace(
            format="json",
            output=None,
            pipe_command=None,
            pipe_args=None,
        )

        code = path_audit.run(args)

        self.assertEqual(code, 1)
