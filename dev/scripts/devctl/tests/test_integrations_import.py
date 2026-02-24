"""Tests for `devctl integrations-import` parser and command behavior."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import integrations_import


def make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "list_profiles": False,
        "source": "code-link-ide",
        "profile": "iphone-core",
        "apply": False,
        "overwrite": False,
        "yes": True,
        "max_files": None,
        "dry_run": False,
        "format": "json",
        "output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def sample_policy() -> dict:
    return {
        "audit_log_path": "dev/reports/integration_import_audit.jsonl",
        "max_files_per_import": 200,
        "allowed_destination_roots": ["dev/integrations/imports"],
        "sources": {
            "code-link-ide": {
                "path": "integrations/code-link-ide",
                "profiles": {
                    "iphone-core": {
                        "description": "Swift package references",
                        "mappings": [
                            {
                                "from": "ios/Sources/VoiceAgentCore",
                                "to": "dev/integrations/imports/code-link-ide/ios/Sources/VoiceAgentCore",
                            }
                        ],
                    }
                },
            }
        },
    }


class IntegrationsImportParserTests(unittest.TestCase):
    def test_cli_accepts_integrations_import_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "integrations-import",
                "--source",
                "code-link-ide",
                "--profile",
                "iphone-core",
                "--apply",
                "--overwrite",
                "--yes",
                "--format",
                "json",
            ]
        )
        self.assertEqual(args.command, "integrations-import")
        self.assertEqual(args.source, "code-link-ide")
        self.assertEqual(args.profile, "iphone-core")
        self.assertTrue(args.apply)
        self.assertTrue(args.overwrite)
        self.assertTrue(args.yes)


class IntegrationsImportCommandTests(unittest.TestCase):
    @patch("dev.scripts.devctl.commands.integrations_import.write_output")
    @patch(
        "dev.scripts.devctl.commands.integrations_import.load_federation_policy",
        return_value=sample_policy(),
    )
    def test_list_profiles_outputs_configured_profiles(
        self,
        _policy_mock,
        write_output_mock,
    ) -> None:
        rc = integrations_import.run(make_args(list_profiles=True, source=None, profile=None))
        self.assertEqual(rc, 0)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["mode"], "list-profiles")
        self.assertEqual(payload["sources"][0]["source"], "code-link-ide")

    def test_preview_mode_builds_import_plan_and_writes_audit_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            source_dir = root / "integrations" / "code-link-ide" / "ios" / "Sources" / "VoiceAgentCore"
            source_dir.mkdir(parents=True, exist_ok=True)
            source_file = source_dir / "AgentConnection.swift"
            source_file.write_text("struct AgentConnection {}", encoding="utf-8")

            with (
                patch("dev.scripts.devctl.commands.integrations_import.REPO_ROOT", root),
                patch(
                    "dev.scripts.devctl.commands.integrations_import.load_federation_policy",
                    return_value=sample_policy(),
                ),
                patch("dev.scripts.devctl.commands.integrations_import.write_output") as write_output_mock,
            ):
                rc = integrations_import.run(make_args(apply=False, format="json"))

            self.assertEqual(rc, 0)
            payload = json.loads(write_output_mock.call_args.args[0])
            self.assertEqual(payload["planned_files"], 1)
            self.assertEqual(payload["applied_files"], 0)
            dest_file = (
                root
                / "dev"
                / "integrations"
                / "imports"
                / "code-link-ide"
                / "ios"
                / "Sources"
                / "VoiceAgentCore"
                / "AgentConnection.swift"
            )
            self.assertFalse(dest_file.exists())
            audit_log = root / "dev" / "reports" / "integration_import_audit.jsonl"
            self.assertTrue(audit_log.exists())
            self.assertEqual(len(audit_log.read_text(encoding="utf-8").splitlines()), 1)

    def test_apply_mode_writes_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            source_dir = root / "integrations" / "code-link-ide" / "ios" / "Sources" / "VoiceAgentCore"
            source_dir.mkdir(parents=True, exist_ok=True)
            source_file = source_dir / "AgentConnection.swift"
            source_file.write_text("struct AgentConnection {}", encoding="utf-8")

            with (
                patch("dev.scripts.devctl.commands.integrations_import.REPO_ROOT", root),
                patch(
                    "dev.scripts.devctl.commands.integrations_import.load_federation_policy",
                    return_value=sample_policy(),
                ),
                patch("dev.scripts.devctl.commands.integrations_import.write_output") as write_output_mock,
            ):
                rc = integrations_import.run(make_args(apply=True, yes=True, format="json"))

            self.assertEqual(rc, 0)
            payload = json.loads(write_output_mock.call_args.args[0])
            self.assertEqual(payload["applied_files"], 1)
            dest_file = (
                root
                / "dev"
                / "integrations"
                / "imports"
                / "code-link-ide"
                / "ios"
                / "Sources"
                / "VoiceAgentCore"
                / "AgentConnection.swift"
            )
            self.assertTrue(dest_file.exists())


if __name__ == "__main__":
    unittest.main()
