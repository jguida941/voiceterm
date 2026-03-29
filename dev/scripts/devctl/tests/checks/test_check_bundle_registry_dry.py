"""Tests for check_bundle_registry_dry guard script."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from importlib import import_module
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[5]


class CheckBundleRegistryDryTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.script = import_module(
            "dev.scripts.checks.bundle_registry_dry.command"
        )
        cls.analysis = import_module(
            "dev.scripts.checks.bundle_registry_dry.analysis"
        )
        cls.loader = import_module("dev.scripts.checks.bundle_registry_dry.loader")

    def test_build_report_returns_ok(self) -> None:
        report = self.script.build_report()
        self.assertTrue(report["ok"])

    def test_report_has_expected_keys(self) -> None:
        report = self.script.build_report()
        for key in ("command", "timestamp", "ok", "violations"):
            self.assertIn(key, report)
        self.assertEqual(report["command"], "check_bundle_registry_dry")

    def test_report_uses_composition_flag(self) -> None:
        report = self.script.build_report()
        self.assertTrue(report["uses_composition"])

    def test_widely_shared_command_budget_controls_non_composed_registry(
        self,
    ) -> None:
        registry = SimpleNamespace(
            BUNDLE_REGISTRY={
                "bundle.a": ("shared-1", "shared-2", "unique-a"),
                "bundle.b": ("shared-1", "shared-2", "unique-b"),
                "bundle.c": ("shared-1", "shared-2", "unique-c"),
            },
            COMPOSITION_LAYER_NAMES=(),
        )
        with mock.patch.object(self.analysis, "load_registry", return_value=registry):
            strict_report = self.analysis.build_report(
                max_widely_shared_commands=1
            )
            tolerant_report = self.analysis.build_report(
                max_widely_shared_commands=2
            )

        self.assertFalse(strict_report["ok"])
        self.assertEqual(strict_report["widely_shared_count"], 2)
        self.assertTrue(tolerant_report["ok"])
        self.assertEqual(strict_report["max_widely_shared_commands"], 1)
        self.assertEqual(tolerant_report["max_widely_shared_commands"], 2)
        self.assertEqual(tolerant_report["max_shared"], 2)

    def test_declared_composition_layers_must_be_reused_by_bundles(self) -> None:
        registry = SimpleNamespace(
            BUNDLE_REGISTRY={
                "bundle.a": ("prefix", "shared-1", "shared-2", "suffix-a"),
                "bundle.b": ("shared-1", "shared-2", "suffix-b"),
                "bundle.c": ("shared-1", "shared-2", "suffix-c"),
            },
            COMPOSITION_LAYER_NAMES=("_SHARED_LAYER",),
            _SHARED_LAYER=("shared-1", "shared-2"),
        )
        with mock.patch.object(self.analysis, "load_registry", return_value=registry):
            report = self.analysis.build_report(max_widely_shared_commands=0)

        self.assertTrue(report["ok"])
        self.assertEqual(report["composition_layers_used"], ["_SHARED_LAYER"])

    def test_invalid_shim_target_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            shim_path = repo_root / "shim.py"
            shim_path.write_text("# shim-target: missing/registry.py\n", encoding="utf-8")
            with mock.patch.object(self.loader, "REPO_ROOT", repo_root):
                with self.assertRaisesRegex(RuntimeError, "does not resolve to a file"):
                    self.loader.resolve_registry_module_path(shim_path)

    def test_root_entrypoint_smoke(self) -> None:
        """Integration smoke for shipped entrypoints and CLI routing."""
        commands = (
            [
                sys.executable,
                "dev/scripts/checks/check_bundle_registry_dry.py",
                "--format",
                "json",
            ],
            [
                sys.executable,
                "dev/scripts/checks/check_publication_sync.py",
                "--release-branch-aware",
                "--report-only",
                "--format",
                "json",
            ],
            [
                sys.executable,
                "dev/scripts/devctl.py",
                "hygiene",
                "--strict-release-warnings",
                "--format",
                "json",
            ],
        )
        for command in commands:
            result = subprocess.run(
                command,
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertIn("ok", payload)

    def test_render_markdown_contains_header(self) -> None:
        report = self.script.build_report()
        md = self.script.render_markdown(report)
        self.assertIn("# check_bundle_registry_dry", md)


if __name__ == "__main__":
    unittest.main()
