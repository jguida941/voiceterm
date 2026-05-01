"""Tests for provider-list parity guard."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dev.scripts.checks.check_provider_list_parity_graph import build_report


class ProviderListParityGraphTests(unittest.TestCase):
    def test_current_repo_provider_lists_are_clean(self) -> None:
        report = build_report()

        self.assertTrue(report["ok"], report["violations"])

    def test_agent_choices_with_known_providers_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            parser_dir = root / "dev/scripts/devctl/commands/reporting"
            parser_dir.mkdir(parents=True)
            (parser_dir / "monitor.py").write_text(
                "def add_parser(cmd):\n"
                "    cmd.add_argument('--agent', choices=['operator', 'codex', 'claude'])\n",
                encoding="utf-8",
            )
            report = build_report(repo_root=root)

        self.assertFalse(report["ok"])
        self.assertEqual(report["violations"][0]["check"], "agent_provider_choices_use_shared_registry")

    def test_agent_without_choices_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            parser_dir = root / "dev/scripts/devctl/cli_parser"
            parser_dir.mkdir(parents=True)
            (parser_dir / "agent_mind.py").write_text(
                "def add_parser(cmd):\n"
                "    cmd.add_argument('--agent', metavar='PROVIDER')\n",
                encoding="utf-8",
            )
            report = build_report(repo_root=root)

        self.assertTrue(report["ok"], report["violations"])


if __name__ == "__main__":
    unittest.main()
