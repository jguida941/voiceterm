"""Tests for devctl path-audit command."""

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl import path_audit as path_audit_helpers
from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import path_audit


class PathAuditCommandTests(TestCase):
    def test_cli_accepts_path_audit_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["path-audit", "--format", "json"])
        self.assertEqual(args.command, "path-audit")
        self.assertEqual(args.format, "json")

    @patch("dev.scripts.devctl.commands.path_audit.write_output")
    @patch("dev.scripts.devctl.commands.path_audit.scan_path_audit_references")
    def test_path_audit_passes_when_no_violations(
        self,
        scan_mock,
        _write_output_mock,
    ) -> None:
        scan_mock.return_value = {
            "ok": True,
            "checked_file_count": 25,
            "excluded_prefixes": ["dev/archive/"],
            "legacy_violation_count": 0,
            "workspace_contract_violation_count": 0,
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
    @patch("dev.scripts.devctl.commands.path_audit.scan_path_audit_references")
    def test_path_audit_fails_when_violations_found(
        self,
        scan_mock,
        _write_output_mock,
    ) -> None:
        legacy_path = "dev/scripts/" + "check_active_plan_sync.py"
        replacement_path = "dev/scripts/checks/" + "check_active_plan_sync.py"
        scan_mock.return_value = {
            "ok": False,
            "checked_file_count": 25,
            "excluded_prefixes": ["dev/archive/"],
            "legacy_violation_count": 1,
            "workspace_contract_violation_count": 0,
            "rules": {legacy_path: replacement_path},
            "violations": [
                {
                    "file": "AGENTS.md",
                    "line": 10,
                    "legacy_path": legacy_path,
                    "replacement_path": replacement_path,
                    "line_text": "python3 " + legacy_path,
                    "violation_type": "legacy_check_path",
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

    def test_workspace_contract_scanner_detects_stale_tokens(self) -> None:
        stale_text = "\n".join(
            [
                '      - "src/**"',
                "working-directory: src",
                'directory: "/src"',
                "/src/ @owner",
            ]
        )
        violations = path_audit_helpers._scan_text_for_workspace_contract_references(
            ".github/workflows/rust_ci.yml",
            stale_text,
        )
        self.assertEqual(len(violations), 4)
        self.assertEqual(
            {item["rule_id"] for item in violations},
            {
                "runtime_src_glob",
                "working_directory_src",
                "dependabot_src_directory",
                "codeowners_src_root",
            },
        )

    def test_legacy_scanner_detects_packaged_entrypoint_reference(self) -> None:
        legacy_path = "dev/scripts/" + "workflow_shell_bridge.py"
        violations = path_audit_helpers._scan_text_for_legacy_references(
            "AGENTS.md",
            "python3 " + legacy_path + " resolve-range",
        )
        self.assertEqual(len(violations), 1)
        self.assertEqual(
            violations[0]["replacement_path"],
            "dev/scripts/workflow_bridge/shell.py",
        )
