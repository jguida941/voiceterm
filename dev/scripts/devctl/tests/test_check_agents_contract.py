"""Unit tests for check_agents_contract governance script."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from dev.scripts.devctl.config import REPO_ROOT

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


def _valid_agents_text(script) -> str:
    lines: list[str] = ["# AGENTS", ""]
    for heading in script.REQUIRED_H2:
        lines.append(f"## {heading}")
        lines.append("placeholder")
        lines.append("")
    for bundle in script.REQUIRED_BUNDLES:
        lines.append(f"`{bundle}`")
    lines.append("")
    lines.extend(script.REQUIRED_MARKERS)
    lines.append("")
    lines.extend(script.REQUIRED_ROUTER_SNIPPETS)
    lines.append("")
    return "\n".join(lines)


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

    def test_build_report_ok_for_complete_contract(self) -> None:
        agents_path = self._with_temp_agents(_valid_agents_text(self.script))
        with patch.object(self.script, "AGENTS_PATH", agents_path):
            report = self.script._build_report()
        self.assertTrue(report["ok"])
        self.assertEqual(report["missing_h2"], [])
        self.assertEqual(report["missing_bundles"], [])
        self.assertEqual(report["missing_markers"], [])
        self.assertEqual(report["missing_router_rows"], [])

    def test_build_report_flags_missing_router_row(self) -> None:
        text = _valid_agents_text(self.script).replace(
            self.script.REQUIRED_ROUTER_SNIPPETS[0], ""
        )
        agents_path = self._with_temp_agents(text)
        with patch.object(self.script, "AGENTS_PATH", agents_path):
            report = self.script._build_report()
        self.assertFalse(report["ok"])
        self.assertEqual(
            report["missing_router_rows"], [self.script.REQUIRED_ROUTER_SNIPPETS[0]]
        )

    def test_build_report_missing_file_returns_error(self) -> None:
        missing_path = REPO_ROOT / "tmp-check-agents-contract-missing.md"
        if missing_path.exists():
            missing_path.unlink()
        with patch.object(self.script, "AGENTS_PATH", missing_path):
            report = self.script._build_report()
        self.assertFalse(report["ok"])
        self.assertIn("Missing file", report["error"])
