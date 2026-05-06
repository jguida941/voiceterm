"""Tests for the AGENTS boot-card compatibility guard."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[5]


def _load_module(name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module at {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CheckAgentsBundleRenderTests(unittest.TestCase):
    """Protect the compatibility shim over render-surfaces."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_module(
            "check_agents_bundle_render",
            "dev/scripts/checks/check_agents_bundle_render.py",
        )

    def test_build_report_delegates_to_agents_boot_card_surface(self) -> None:
        with patch.object(self.script, "build_surface_report") as build_report:
            build_report.return_value = {
                "command": "render-surfaces",
                "ok": True,
                "surfaces": [{"surface_id": "agents_boot_card"}],
            }

            report = self.script.build_report(write=True)

        self.assertTrue(report["ok"])
        self.assertEqual(report["command"], "check_agents_bundle_render")
        self.assertIn("InstructionBootCard", report["compatibility_note"])
        build_report.assert_called_once_with(
            surface_ids=("agents_boot_card",),
            write=True,
            allow_missing_local_only=False,
            allowed_renderers=frozenset({"instruction_boot_card"}),
        )

    def test_render_markdown_keeps_compatibility_heading(self) -> None:
        markdown = self.script.render_markdown(
            {
                "command": "check_agents_bundle_render",
                "ok": True,
                "repo_pack_id": "voiceterm",
                "repo_pack_version": "0.1.0-dev",
                "policy_path": "dev/config/devctl_repo_policy.json",
                "surface_count": 0,
                "warnings": [],
                "surfaces": [],
            }
        )

        self.assertIn("# check_agents_bundle_render", markdown)


if __name__ == "__main__":
    unittest.main()
