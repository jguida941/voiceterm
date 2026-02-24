"""Tests for `devctl integrations-sync` parser and command behavior."""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from dev.scripts.devctl.cli import build_parser
from dev.scripts.devctl.commands import integrations_sync


def make_args(**overrides) -> SimpleNamespace:
    defaults = {
        "source": None,
        "status_only": True,
        "remote": False,
        "dry_run": False,
        "format": "json",
        "output": None,
        "pipe_command": None,
        "pipe_args": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class IntegrationsSyncParserTests(unittest.TestCase):
    def test_cli_accepts_integrations_sync_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "integrations-sync",
                "--source",
                "code-link-ide",
                "--source",
                "ci-cd-hub",
                "--remote",
                "--format",
                "json",
            ]
        )
        self.assertEqual(args.command, "integrations-sync")
        self.assertEqual(args.source, ["code-link-ide", "ci-cd-hub"])
        self.assertTrue(args.remote)
        self.assertEqual(args.format, "json")


class IntegrationsSyncCommandTests(unittest.TestCase):
    @patch("dev.scripts.devctl.commands.integrations_sync._append_audit_log")
    @patch("dev.scripts.devctl.commands.integrations_sync._source_status")
    @patch("dev.scripts.devctl.commands.integrations_sync.write_output")
    @patch(
        "dev.scripts.devctl.commands.integrations_sync.load_federation_policy",
        return_value={
            "audit_log_path": "dev/reports/integration_import_audit.jsonl",
            "sources": {
                "code-link-ide": {
                    "path": "integrations/code-link-ide",
                    "url": "https://github.com/jguida941/code-link-ide.git",
                }
            },
        },
    )
    def test_status_only_reports_selected_source(
        self,
        _policy_mock,
        write_output_mock,
        source_status_mock,
        _audit_log_mock,
    ) -> None:
        source_status_mock.return_value = {
            "source": "code-link-ide",
            "path": "integrations/code-link-ide",
            "url": "https://github.com/jguida941/code-link-ide.git",
            "exists": True,
            "sha": "abc123",
            "branch": "main",
            "dirty": False,
            "submodule_status": " abc123 integrations/code-link-ide",
            "errors": [],
        }
        with patch("dev.scripts.devctl.commands.integrations_sync.run_cmd") as run_cmd_mock:
            rc = integrations_sync.run(make_args(status_only=True))
        self.assertEqual(rc, 0)
        run_cmd_mock.assert_not_called()
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["mode"], "status-only")
        self.assertEqual(payload["selected_sources"], ["code-link-ide"])

    @patch("dev.scripts.devctl.commands.integrations_sync._append_audit_log")
    @patch("dev.scripts.devctl.commands.integrations_sync.write_output")
    @patch(
        "dev.scripts.devctl.commands.integrations_sync.load_federation_policy",
        return_value={
            "audit_log_path": "dev/reports/integration_import_audit.jsonl",
            "sources": {
                "code-link-ide": {"path": "integrations/code-link-ide"},
            },
        },
    )
    def test_unknown_source_fails(
        self,
        _policy_mock,
        write_output_mock,
        _audit_log_mock,
    ) -> None:
        rc = integrations_sync.run(
            make_args(source=["unknown-source"], status_only=True, format="json")
        )
        self.assertEqual(rc, 1)
        payload = json.loads(write_output_mock.call_args.args[0])
        self.assertFalse(payload["ok"])
        self.assertTrue(any("Unknown integration source" in err for err in payload["errors"]))


if __name__ == "__main__":
    unittest.main()
