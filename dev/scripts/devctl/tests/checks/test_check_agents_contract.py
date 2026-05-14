"""Unit tests for check_agents_contract governance script."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.config import REPO_ROOT
from dev.scripts.devctl.governance.instruction_boot_card import (
    build_instruction_boot_card,
)

SCRIPT_PATH = REPO_ROOT / "dev/scripts/checks/check_agents_contract.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location(
        "check_agents_contract_script", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load check_agents_contract.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CheckAgentsContractTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()

    def _with_temp_agents(self, text: str):
        tmp_dir = tempfile.TemporaryDirectory(dir=REPO_ROOT)
        self.addCleanup(tmp_dir.cleanup)
        path = Path(tmp_dir.name) / "AGENTS.md"
        path.write_text(text, encoding="utf-8")
        return path

    def _valid_agents_text(self) -> str:
        return build_instruction_boot_card(
            surface_id="agents_boot_card",
            output_path="AGENTS.md",
            source_path="dev/state/plan_index.jsonl",
            repo_pack_id="voiceterm",
            repo_pack_version="0.1.0-dev",
        )

    def test_build_report_ok_for_boot_projection(self) -> None:
        agents_path = self._with_temp_agents(self._valid_agents_text())
        with patch.object(self.script, "AGENTS_PATH", agents_path):
            report = self.script._build_report()
        self.assertTrue(report["ok"])
        self.assertEqual(report["missing_h2"], [])
        self.assertEqual(report["missing_markers"], [])
        self.assertEqual(report["missing_commands"], [])
        self.assertEqual(report["forbidden_claims"], [])
        self.assertEqual(report["missing_role_choices"], [])
        self.assertEqual(report["forbidden_role_placeholders"], [])

    def test_build_report_flags_missing_command(self) -> None:
        missing_command = "system-picture"
        text = self._valid_agents_text().replace(missing_command, "")
        agents_path = self._with_temp_agents(text)
        with patch.object(self.script, "AGENTS_PATH", agents_path):
            report = self.script._build_report()
        self.assertFalse(report["ok"])
        self.assertEqual(report["missing_commands"], [missing_command])

    def test_build_report_flags_forbidden_authority_claim(self) -> None:
        text = self._valid_agents_text() + "\nAGENTS.md is canonical authority\n"
        agents_path = self._with_temp_agents(text)
        with patch.object(self.script, "AGENTS_PATH", agents_path):
            report = self.script._build_report()
        self.assertFalse(report["ok"])
        self.assertEqual(
            report["forbidden_claims"],
            ["AGENTS.md is canonical authority"],
        )

    def test_build_report_flags_role_placeholder(self) -> None:
        text = self._valid_agents_text().replace("--role reviewer", "--role <role>", 1)
        agents_path = self._with_temp_agents(text)
        with patch.object(self.script, "AGENTS_PATH", agents_path):
            report = self.script._build_report()
        self.assertFalse(report["ok"])
        self.assertEqual(report["forbidden_role_placeholders"], ["--role <role>"])

    def test_build_report_flags_missing_role_choice(self) -> None:
        text = self._valid_agents_text().replace("`observer`", "`viewer`")
        agents_path = self._with_temp_agents(text)
        with patch.object(self.script, "AGENTS_PATH", agents_path):
            report = self.script._build_report()
        self.assertFalse(report["ok"])
        self.assertEqual(report["missing_role_choices"], ["observer"])

    def test_build_report_missing_file_returns_error(self) -> None:
        missing_path = REPO_ROOT / "tmp-check-agents-contract-missing.md"
        if missing_path.exists():
            missing_path.unlink()
        with patch.object(self.script, "AGENTS_PATH", missing_path):
            report = self.script._build_report()
        self.assertFalse(report["ok"])
        self.assertIn("Missing file", report["error"])
