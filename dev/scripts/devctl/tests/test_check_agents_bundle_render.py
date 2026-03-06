"""Tests for AGENTS bundle render guard script."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]


def _load_module(name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module at {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CheckAgentsBundleRenderTests(unittest.TestCase):
    """Protect AGENTS rendered bundle section guard behavior."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_module(
            "check_agents_bundle_render",
            "dev/scripts/checks/check_agents_bundle_render.py",
        )

    def test_build_report_passes_when_agents_section_matches_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_path = Path(tmpdir) / "AGENTS.md"
            agents_path.write_text(
                "\n".join(
                    [
                        "# AGENTS",
                        "",
                        "Header text.",
                        "",
                        self.script.render_agents_bundle_section_markdown(),
                        "",
                        self.script.NEXT_HEADING,
                        "",
                        "Tail text.",
                    ]
                ),
                encoding="utf-8",
            )
            original_agents_path = self.script.AGENTS_PATH
            self.addCleanup(setattr, self.script, "AGENTS_PATH", original_agents_path)
            self.script.AGENTS_PATH = agents_path

            report = self.script.build_report()

            self.assertTrue(report["ok"])
            self.assertFalse(report["changed"])
            self.assertFalse(report["wrote"])

    def test_build_report_detects_drift_without_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_path = Path(tmpdir) / "AGENTS.md"
            agents_path.write_text(
                "\n".join(
                    [
                        "# AGENTS",
                        "",
                        "## Command bundles (rendered reference)",
                        "",
                        "stale section",
                        "",
                        self.script.NEXT_HEADING,
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            original_agents_path = self.script.AGENTS_PATH
            self.addCleanup(setattr, self.script, "AGENTS_PATH", original_agents_path)
            self.script.AGENTS_PATH = agents_path

            report = self.script.build_report(write=False)

            self.assertFalse(report["ok"])
            self.assertTrue(report["changed"])
            self.assertFalse(report["wrote"])
            self.assertGreater(len(report.get("diff_preview", [])), 0)

    def test_build_report_write_repairs_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_path = Path(tmpdir) / "AGENTS.md"
            agents_path.write_text(
                "\n".join(
                    [
                        "# AGENTS",
                        "",
                        "## Command bundles (rendered reference)",
                        "",
                        "stale section",
                        "",
                        self.script.NEXT_HEADING,
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            original_agents_path = self.script.AGENTS_PATH
            self.addCleanup(setattr, self.script, "AGENTS_PATH", original_agents_path)
            self.script.AGENTS_PATH = agents_path

            report = self.script.build_report(write=True)
            self.assertTrue(report["ok"])
            self.assertTrue(report["changed"])
            self.assertTrue(report["wrote"])

            second_report = self.script.build_report(write=False)
            self.assertTrue(second_report["ok"])
            self.assertFalse(second_report["changed"])

    def test_build_report_fails_when_section_markers_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_path = Path(tmpdir) / "AGENTS.md"
            agents_path.write_text("# AGENTS\n\nno section markers\n", encoding="utf-8")
            original_agents_path = self.script.AGENTS_PATH
            self.addCleanup(setattr, self.script, "AGENTS_PATH", original_agents_path)
            self.script.AGENTS_PATH = agents_path

            report = self.script.build_report()

            self.assertFalse(report["ok"])
            self.assertIn("Unable to locate AGENTS bundle section boundaries", report["error"])


if __name__ == "__main__":
    unittest.main()
