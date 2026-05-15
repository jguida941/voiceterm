"""Tests for the runtime bridge projection-separation report-only guard."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path
from unittest import TestCase

from dev.scripts.devctl.config import REPO_ROOT

COMMAND_PATH = REPO_ROOT / "dev/scripts/checks/runtime_bridge_projection_separation/command.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location(
        "check_runtime_bridge_projection_separation_command",
        COMMAND_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load runtime_bridge_projection_separation/command.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CheckRuntimeBridgeProjectionSeparationTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = _load_script_module()

    def _repo(self) -> Path:
        tmp_dir = tempfile.TemporaryDirectory(dir=REPO_ROOT)
        self.addCleanup(tmp_dir.cleanup)
        return Path(tmp_dir.name)

    def _write(self, root: Path, rel_path: str, text: str) -> None:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_report_only_guard_does_not_fail_on_current_violations(self) -> None:
        root = self._repo()
        self._write(
            root,
            "dev/scripts/devctl/runtime/bad_import.py",
            "from ..review_channel.bridge_projection import render_bridge_projection\n",
        )

        report = self.script._build_report(root=root)

        self.assertTrue(report["ok"])
        self.assertTrue(report["report_only"])
        self.assertTrue(report["would_fail"])
        rules = {str(item.get("rule", "")) for item in report["violations"]}
        self.assertIn("runtime_bridge_projection_import", rules)

    def test_flags_bridge_derived_helper_calls(self) -> None:
        root = self._repo()
        self._write(
            root,
            "dev/scripts/devctl/runtime/bad_call.py",
            """
def bad(payload):
    first = extract_bridge_snapshot(payload)
    second = bridge_config_from_mapping(payload)
    return build_runtime_bridge_state(first, second)
""",
        )

        report = self.script._build_report(root=root)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violation_count"], 3)
        rules = {str(item.get("rule", "")) for item in report["violations"]}
        self.assertIn("runtime_bridge_projection_call", rules)

    def test_scans_review_channel_and_commands_roots(self) -> None:
        root = self._repo()
        self._write(
            root,
            "dev/scripts/devctl/review_channel/non_bridge_reader.py",
            "from .bridge_projection import render_bridge_projection\n",
        )
        self._write(
            root,
            "dev/scripts/devctl/commands/review_channel/non_bridge_reader.py",
            """
from .bridge_support import bridge_support


def bad(payload):
    return build_runtime_bridge_state(payload)
""",
        )

        report = self.script._build_report(root=root)

        checked_paths = set(report["checked_paths"])
        self.assertIn(
            "dev/scripts/devctl/review_channel/non_bridge_reader.py",
            checked_paths,
        )
        self.assertIn(
            "dev/scripts/devctl/commands/review_channel/non_bridge_reader.py",
            checked_paths,
        )
        violation_paths = {str(item.get("path", "")) for item in report["violations"]}
        self.assertIn(
            "dev/scripts/devctl/review_channel/non_bridge_reader.py",
            violation_paths,
        )
        self.assertIn(
            "dev/scripts/devctl/commands/review_channel/non_bridge_reader.py",
            violation_paths,
        )

    def test_allows_non_bridge_runtime_helpers(self) -> None:
        root = self._repo()
        self._write(
            root,
            "dev/scripts/devctl/runtime/good.py",
            """
def good(payload):
    return build_runtime_state(payload)
""",
        )

        report = self.script._build_report(root=root)

        self.assertTrue(report["ok"])
        self.assertFalse(report["would_fail"])
        self.assertEqual(report["violation_count"], 0)
